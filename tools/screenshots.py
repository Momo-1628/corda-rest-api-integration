"""Browser screenshots with Playwright (installed Chrome): Swagger UI, an executed request, raw JSON."""
import json
import os
import statistics
import time

import requests
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(__file__), "..")
SHOTS = os.path.join(ROOT, "evidence", "screenshots")
os.makedirs(SHOTS, exist_ok=True)
SELLER, SKEY = "http://localhost:10050", "seller-secret-key-123"

# --- read-latency comparison: 20 x GET /api/invoices (vault query only, no flow)
s = requests.Session(); s.headers["X-API-KEY"] = SKEY
s.get(SELLER + "/api/invoices")
vals = []
for _ in range(20):
    t0 = time.perf_counter(); r = s.get(SELLER + "/api/invoices"); vals.append((time.perf_counter() - t0) * 1000)
    r.raise_for_status()
get_summary = {"calls": 20, "average_ms": round(statistics.mean(vals), 1), "min_ms": round(min(vals), 1),
               "max_ms": round(max(vals), 1), "invoices_returned": len(r.json()["data"])}
json.dump(get_summary, open(os.path.join(ROOT, "evidence", "latency_get.json"), "w"), indent=2)
print("GET latency", get_summary)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)

    # 1) Swagger UI overview
    page = browser.new_page(viewport={"width": 1440, "height": 1300}, device_scale_factor=1)
    page.goto(SELLER + "/swagger-ui.html", wait_until="networkidle")
    page.wait_for_selector(".opblock", timeout=30000)
    page.screenshot(path=os.path.join(SHOTS, "swagger_ui.png"), full_page=True)

    # 2) Swagger UI: authorize + execute GET /api/invoices
    page.click("button.authorize")
    page.fill(".modal-ux input[type=text]", SKEY)
    page.click(".modal-ux button.authorize")
    page.click(".modal-ux button.btn-done")
    op = page.locator(".opblock-get:has(.opblock-summary-path[data-path='/api/invoices'])").first
    op.locator(".opblock-summary").click()
    op.locator("button.try-out__btn").click()
    op.locator("button.execute").click()
    page.wait_for_selector(".responses-table .response .microlight", timeout=30000)
    time.sleep(1)
    op.screenshot(path=os.path.join(SHOTS, "swagger_execute_get_invoices.png"))

    # 3) raw JSON of GET /api/invoices in the browser (API key sent as header)
    ctx = browser.new_context(viewport={"width": 1280, "height": 1100}, extra_http_headers={"X-API-KEY": SKEY})
    jpage = ctx.new_page()
    jpage.goto(SELLER + "/api/invoices?status=PAID", wait_until="load")
    # Chrome shows a "pretty-print" checkbox for JSON documents; tick it when present
    try:
        jpage.locator("input[type=checkbox]").first.check(timeout=2000)
    except Exception:
        pass
    jpage.screenshot(path=os.path.join(SHOTS, "browser_get_invoices_json.png"), full_page=False)

    # 4) health endpoint
    jpage.goto(SELLER + "/api/health", wait_until="load")
    jpage.screenshot(path=os.path.join(SHOTS, "browser_health_json.png"))
    browser.close()
print("screenshots in", os.path.abspath(SHOTS))
