#!/usr/bin/env python3
"""
latency_benchmark.py - times N sequential POST /api/invoices calls against the Seller API.
Each call runs the full IssueInvoiceFlow: build -> verify -> sign -> CollectSignatures (BuyerCorp)
-> notarise -> record in both vaults -> JSON response.

Author: Suraj Patel (24BTRBT029)
Usage : python scripts/latency_benchmark.py [-n 20] [--out evidence/latency_results.json]
"""
import argparse
import datetime as dt
import json
import statistics
import time

import requests

ap = argparse.ArgumentParser()
ap.add_argument("-n", type=int, default=20)
ap.add_argument("--url", default="http://localhost:10050")
ap.add_argument("--key", default="seller-secret-key-123")
ap.add_argument("--warmup", type=int, default=2)
ap.add_argument("--out", default="evidence/latency_results.json")
args = ap.parse_args()

session = requests.Session()
session.headers.update({"X-API-KEY": args.key, "Content-Type": "application/json"})
run = dt.datetime.now().strftime("%H%M%S")


def post(i, tag):
    body = {"invoiceNo": f"PERF-{run}-{tag}{i:02d}", "buyer": "O=BuyerCorp,L=Bengaluru,C=IN",
            "amount": 1000 + i, "currency": "INR", "description": "latency benchmark", "dueDate": "2026-12-31"}
    t0 = time.perf_counter()
    r = session.post(args.url + "/api/invoices", data=json.dumps(body), timeout=120)
    ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return ms, r.json()["data"]["txHash"]


for w in range(args.warmup):  # JIT / connection warm-up, not counted
    post(w, "W")

samples = []
for i in range(1, args.n + 1):
    ms, tx = post(i, "")
    samples.append({"call": i, "ms": round(ms, 1), "txHash": tx})
    print(f"call {i:2d}: {ms:8.1f} ms  tx={tx[:16]}...")

values = [s["ms"] for s in samples]
summary = {
    "calls": len(values),
    "warmup_calls_excluded": args.warmup,
    "average_ms": round(statistics.mean(values), 1),
    "median_ms": round(statistics.median(values), 1),
    "min_ms": round(min(values), 1),
    "max_ms": round(max(values), 1),
    "stdev_ms": round(statistics.stdev(values), 1) if len(values) > 1 else 0,
    "p90_ms": round(sorted(values)[int(0.9 * len(values)) - 1], 1),
    "throughput_tx_per_s": round(1000 / statistics.mean(values), 2),
    "measured_at": dt.datetime.now().isoformat(timespec="seconds"),
}
print(json.dumps(summary, indent=2))
with open(args.out, "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "samples": samples}, f, indent=2)
