#!/usr/bin/env python3
"""
external_erp_client.py - simulates an outside ERP system that talks to the Corda network
only through the REST API (it knows nothing about Corda RPC, flows or the vault).

  Seller ERP  -> http://localhost:10050  (SellerCorp node)
  Buyer  ERP  -> http://localhost:10060  (BuyerCorp node)

Happy path : issue 3 invoices (seller), approve+pay one, approve one, reject one (buyer)
Error cases: wrong API key (401), invalid amount (400), paying an un-approved invoice (422),
             unknown linearId (404)
Finally it lists the invoices from BOTH nodes as a table to show they agree.

Author: Suraj Patel (24BTRBT029)
Usage : python external_erp_client.py [--out evidence/erp_client_run.txt]
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import uuid

import requests

SELLER = {"name": "SellerCorp", "url": os.getenv("SELLER_API", "http://localhost:10050"),
          "key": os.getenv("SELLER_KEY", "seller-secret-key-123")}
BUYER = {"name": "BuyerCorp", "url": os.getenv("BUYER_API", "http://localhost:10060"),
         "key": os.getenv("BUYER_KEY", "buyer-secret-key-456")}
BUYER_X500 = "O=BuyerCorp,L=Bengaluru,C=IN"

LINES = []
RESPONSES = {}


def out(text=""):
    print(text)
    LINES.append(text)


def call(node, method, path, body=None, key=None, label=None):
    """Calls the API, prints a one-line summary and returns (status, json)."""
    headers = {"X-API-KEY": node["key"] if key is None else key, "Content-Type": "application/json"}
    t0 = time.perf_counter()
    r = requests.request(method, node["url"] + path, headers=headers,
                         data=None if body is None else json.dumps(body), timeout=90)
    ms = (time.perf_counter() - t0) * 1000
    try:
        payload = r.json()
    except ValueError:
        payload = {"raw": r.text}
    out(f"  {method:<4} {node['name']:<10} {path:<60} -> HTTP {r.status_code}  ({ms:.0f} ms)")
    if label:
        RESPONSES[label] = {"request": {"method": method, "url": node["url"] + path, "body": body},
                            "status": r.status_code, "response": payload}
    return r.status_code, payload


def check(cond, msg):
    out(f"    [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        check.failures += 1


check.failures = 0


def table(rows, headers):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out(sep)
    out("| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |")
    out(sep)
    for r in rows:
        out("| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |")
    out(sep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="evidence/erp_client_run.txt")
    ap.add_argument("--json-dir", default="evidence/api_responses")
    args = ap.parse_args()

    run = dt.datetime.now().strftime("%H%M%S")
    out("=" * 96)
    out(" EXTERNAL ERP CLIENT  ->  Corda Invoice REST API")
    out(f" Run at {dt.datetime.now().isoformat(timespec='seconds')}   |   author: Suraj Patel (24BTRBT029)")
    out("=" * 96)

    out("\n[1] Connectivity check")
    for node in (SELLER, BUYER):
        s, p = call(node, "GET", "/api/health", label=f"health_{node['name']}")
        check(s == 200 and p["data"]["status"] == "UP", f"{node['name']} API is UP, node = {p['data'].get('node')}")
        s, p = call(node, "GET", "/api/me", label=f"me_{node['name']}")
        check(s == 200, f"/api/me -> {p['data']['name']}")
    s, p = call(SELLER, "GET", "/api/peers", label="peers")
    check(BUYER_X500.replace(",", ", ") in p["data"]["peers"], f"Seller sees peers {p['data']['peers']}")
    s, p = call(SELLER, "GET", "/api/notaries", label="notaries")
    check(len(p["data"]["notaries"]) == 1, f"Notaries {p['data']['notaries']}")

    out("\n[2] Seller ERP issues 3 invoices (POST /api/invoices -> IssueInvoiceFlow)")
    specs = [("A", 125000.00, "50 units of industrial steel rods"),
             ("B", 48250.50, "Annual maintenance contract - Q1"),
             ("C", 9999.99, "Office furniture (wrong quantity)")]
    ids = {}
    for tag, amount, desc in specs:
        body = {"invoiceNo": f"INV-{run}-{tag}", "buyer": BUYER_X500, "amount": amount, "currency": "INR",
                "description": desc, "dueDate": "2026-12-31"}
        s, p = call(SELLER, "POST", "/api/invoices", body, label=f"issue_{tag}")
        check(s == 201 and p["success"], f"{body['invoiceNo']} issued, tx {p['data']['txHash'][:16]}..., "
                                         f"linearId {p['data']['linearId']}")
        ids[tag] = p["data"]["linearId"]

    out("\n[3] Buyer ERP sees the same invoices on its own node")
    s, p = call(BUYER, "GET", "/api/invoices?status=ISSUED", label="buyer_list_issued")
    seen = {i["linearId"] for i in p["data"]}
    check(all(v in seen for v in ids.values()), "all 3 new invoices are in BuyerCorp's vault with status ISSUED")

    out("\n[4] Buyer ERP processes the invoices (PUT approve / pay / reject)")
    s, p = call(BUYER, "PUT", f"/api/invoices/{ids['A']}/approve", {"remarks": "Goods received in good condition"},
                label="approve_A")
    check(s == 200 and p["data"]["invoice"]["status"] == "APPROVED", "Invoice A -> APPROVED")
    s, p = call(BUYER, "PUT", f"/api/invoices/{ids['A']}/pay", {"remarks": "NEFT UTR HDFC0001234567"}, label="pay_A")
    check(s == 200 and p["data"]["invoice"]["status"] == "PAID", "Invoice A -> PAID")
    s, p = call(BUYER, "PUT", f"/api/invoices/{ids['B']}/approve", {"remarks": "Approved by finance"},
                label="approve_B")
    check(s == 200 and p["data"]["invoice"]["status"] == "APPROVED", "Invoice B -> APPROVED (payment pending)")

    out("\n[5] Error handling")
    s, p = call(SELLER, "GET", "/api/invoices", key="wrong-key", label="error_401")
    check(s == 401, f"wrong API key -> 401 {p['error']['code']}: {p['error']['message']}")
    bad = {"invoiceNo": f"INV-{run}-X", "buyer": BUYER_X500, "amount": -500, "currency": "INR",
           "description": "negative amount", "dueDate": "2026-12-31"}
    s, p = call(SELLER, "POST", "/api/invoices", bad, label="error_400")
    check(s == 400, f"invalid amount -> 400 {p['error']['code']}: {p['error']['details']}")
    s, p = call(BUYER, "PUT", f"/api/invoices/{ids['C']}/pay", {"remarks": "trying to pay too early"}, label="error_422")
    check(s == 422, f"paying an un-approved invoice -> 422 {p['error']['code']}: {p['error']['message']}")
    s, p = call(BUYER, "GET", f"/api/invoices/{uuid.uuid4()}", label="error_404")
    check(s == 404, f"unknown linearId -> 404 {p['error']['code']}")

    s, p = call(BUYER, "PUT", f"/api/invoices/{ids['C']}/reject", {"remarks": "Wrong quantity delivered"},
                label="reject_C")
    check(s == 200 and p["data"]["invoice"]["status"] == "REJECTED", "Invoice C -> REJECTED")

    out("\n[6] Audit trail of invoice A (GET /history)")
    s, p = call(SELLER, "GET", f"/api/invoices/{ids['A']}/history", label="history_A")
    table([(h["version"], h["status"], h["stateStatus"], h["txHash"][:16] + "...", h["remarks"] or "-")
           for h in p["data"]], ["v", "status", "vault", "txHash", "remarks"])
    check([h["status"] for h in p["data"]] == ["ISSUED", "APPROVED", "PAID"], "history = ISSUED -> APPROVED -> PAID")

    out("\n[7] Invoices of this run as seen by each node")
    views = {}
    for node in (SELLER, BUYER):
        s, p = call(node, "GET", "/api/invoices", label=f"list_{node['name']}")
        views[node["name"]] = {i["linearId"]: i for i in p["data"] if i["invoiceNo"].startswith(f"INV-{run}")}
    for name, view in views.items():
        out(f"\n  {name} vault:")
        table([(i["invoiceNo"], f"{i['amount']:,.2f} {i['currency']}", i["status"], i["linearId"][:8] + "...",
                (i["remarks"] or "-")[:28]) for i in sorted(view.values(), key=lambda x: x["invoiceNo"])],
              ["invoiceNo", "amount", "status", "linearId", "remarks"])
    check({k: v["status"] for k, v in views["SellerCorp"].items()} ==
          {k: v["status"] for k, v in views["BuyerCorp"].items()}, "Seller and Buyer vaults are in agreement")

    out("\n" + "=" * 96)
    out(f" RESULT: {'ALL CHECKS PASSED' if check.failures == 0 else str(check.failures) + ' CHECK(S) FAILED'}")
    out("=" * 96)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    os.makedirs(args.json_dir, exist_ok=True)
    for label, data in RESPONSES.items():
        with open(os.path.join(args.json_dir, f"{label}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    with open(os.path.join(args.json_dir, "_ids.json"), "w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2)
    return 0 if check.failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
