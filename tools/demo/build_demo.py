"""Assembles the silent implementation demo: title cards + rendered terminal recordings + browser recordings."""
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import render as R

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "deliverables", "Topic25_Implementation_Demo_24BTRBT029.mp4")
gh = glob.glob(r"D:\corda-rest-api-run\demo\browser\github\*.webm")[0]
sw = glob.glob(r"D:\corda-rest-api-run\demo\browser\swagger\*.webm")[0]

segs = [
    R.title_card("t00", "Topic 25  |  Corda Development  |  Implementation demo",
                 "Corda REST API Integration", [
                     "Invoice CorDapp on Corda 4.12 + Spring Boot 3 REST API (one per node)",
                     "Code walkthrough, 42 tests, live 3-node network, Swagger UI, ERP client, curl",
                     "Suraj Patel (24BTRBT029)  -  screen recording, no voice-over"], 7),
    R.title_card("t01", "Step 1 of 9", "Project structure", [
        "Started from the official R3 cordapp-template-java (Corda 4.12, JDK 17)",
        "contracts/  workflows/  clients/webserver/  + ERP client, Postman, scripts"]),
    R.render_cast("01_overview", "Step 1 - Project structure (git repository)", min_group=0.35, tail_hold=6),
    R.title_card("t02", "Step 2 of 9", "Code walkthrough", [
        "InvoiceState, InvoiceContract, IssueInvoiceFlow, InvoiceTransitionFlow",
        "InvoiceController, InvoiceService, ApiKeyFilter, GlobalExceptionHandler, tests",
        "Real browser recording of the public GitHub repository"]),
    R.webm_to_segment(gh, "s02_github", trim_start=0.5),
    R.title_card("t03", "Step 3 of 9", "Automated tests", [
        "15 contract tests (ledger DSL), 6 flow tests (MockNetwork), 21 API tests (MockMvc)",
        "Long waits are shortened; the real elapsed time is shown bottom-right"]),
    R.render_cast("02_tests", "Step 3 - gradlew test (contracts, flows, REST API)", min_group=0.12, tail_hold=7),
    R.title_card("t04", "Step 4 of 9", "Deploy the Corda network", [
        "deployNodes: Notary, SellerCorp (Mumbai), BuyerCorp (Bengaluru) with RPC users",
        "writeLaunchArgs: classpath file used to start the REST APIs"]),
    R.render_cast("03_deploy", "Step 4 - gradlew deployNodes", min_group=0.08, tail_hold=4),
    R.title_card("t05", "Step 5 of 9", "Start nodes and REST APIs", [
        "Each node started headless with java -jar corda.jar, waiting for \"started up\"",
        "Seller API on :10050 and Buyer API on :10060 (Spring profiles), /api/health = UP"]),
    R.render_cast("04_start", "Step 5 - start_network.ps1", tail_hold=4),
    R.render_cast("05_nodelog", "Step 5 - Corda node start-up banners", min_group=0.4, tail_hold=6),
    R.title_card("t06", "Step 6 of 9", "Live demo in Swagger UI", [
        "401 without key, 400 validation, 201 issue (both signatures + notary)",
        "Buyer API: 422 pay-before-approve, approve, pay, 404 unknown id",
        "Seller API: full history ISSUED -> APPROVED -> PAID"]),
    R.webm_to_segment(sw, "s06_swagger", trim_start=0.5),
    R.title_card("t07", "Step 7 of 9", "External ERP client (Python)", [
        "An outside system that only knows HTTP + JSON",
        "Issues 3 invoices, approves / pays / rejects, triggers 401 / 400 / 422 / 404",
        "Checks that the Seller and Buyer vaults agree"]),
    R.render_cast("06_erp", "Step 7 - python external_erp_client.py", min_group=0.3, tail_hold=8),
    R.title_card("t08", "Step 8 of 9", "curl walk-through", [
        "Every endpoint from the command line: me, peers, notaries, issue, approve, pay, history",
        "Error envelopes: 401, 400, 422, 404"]),
    R.render_cast("07_curl", "Step 8 - bash scripts/api_demo.sh", min_group=0.45, tail_hold=7),
    R.title_card("t09", "Step 9 of 9", "Clean shutdown", ["APIs first, then BuyerCorp, SellerCorp and the Notary"]),
    R.render_cast("08_stop", "Step 9 - stop_network.ps1", tail_hold=4),
    R.title_card("t10", "Summary", "Implementation complete", [
        "42 / 42 tests passing  |  11 REST endpoints  |  3-node Corda 4.12 network",
        "POST /api/invoices avg 583 ms (full flow + notary), GET avg 78 ms",
        "github.com/Momo-1628/corda-rest-api-integration"], 7),
]
lst = os.path.join(R.DEMO, "concat.txt")
with open(lst, "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")
silent = os.path.join(R.DEMO, "joined.mp4")
subprocess.run([R.FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
# add a silent stereo track (some upload portals reject video-only files)
subprocess.run([R.FFMPEG, "-y", "-v", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "32k", "-shortest",
                "-movflags", "+faststart", OUT], check=True)
print("written", OUT)
