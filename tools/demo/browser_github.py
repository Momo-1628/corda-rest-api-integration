"""Records a real browser session (Playwright + Chrome) walking through the source code on GitHub."""
import os
import shutil
import time

from playwright.sync_api import sync_playwright

REPO = "https://github.com/Momo-1628/corda-rest-api-integration"
OUT = r"D:\corda-rest-api-run\demo\browser\github"
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
B = "main"

TOUR = [
    ("README", REPO, "Repository overview: what the project contains and how to run it", 0, 9),
    ("InvoiceState", f"{REPO}/blob/{B}/contracts/src/main/java/com/cordarest/states/InvoiceState.java#L21-L62",
     "Ledger layer - InvoiceState.java: the LinearState shared by seller and buyer", 1, 12),
    ("InvoiceContract", f"{REPO}/blob/{B}/contracts/src/main/java/com/cordarest/contracts/InvoiceContract.java#L41-L77",
     "Ledger layer - InvoiceContract.java: Issue / Approve / Pay / Reject rules", 1, 15),
    ("IssueInvoiceFlow", f"{REPO}/blob/{B}/workflows/src/main/java/com/cordarest/flows/IssueInvoiceFlow.java#L62-L92",
     "Workflow layer - IssueInvoiceFlow.java: sign, CollectSignaturesFlow, FinalityFlow", 1, 15),
    ("InvoiceTransitionFlow", f"{REPO}/blob/{B}/workflows/src/main/java/com/cordarest/flows/InvoiceTransitionFlow.java#L51-L80",
     "Workflow layer - InvoiceTransitionFlow.java: buyer-side Approve / Pay / Reject", 1, 12),
    ("InvoiceController", f"{REPO}/blob/{B}/clients/webserver/src/main/java/com/cordarest/webserver/controller/InvoiceController.java#L29-L82",
     "REST layer - InvoiceController.java: the /api/invoices endpoints", 1, 13),
    ("InvoiceService", f"{REPO}/blob/{B}/clients/webserver/src/main/java/com/cordarest/webserver/service/InvoiceService.java#L99-L150",
     "REST layer - InvoiceService.java: CordaRPCOps.startFlowDynamic + error translation", 1, 14),
    ("ApiKeyFilter", f"{REPO}/blob/{B}/clients/webserver/src/main/java/com/cordarest/webserver/security/ApiKeyFilter.java#L40-L66",
     "Security - ApiKeyFilter.java: X-API-KEY check, 401 envelope", 1, 10),
    ("GlobalExceptionHandler", f"{REPO}/blob/{B}/clients/webserver/src/main/java/com/cordarest/webserver/exception/GlobalExceptionHandler.java#L29-L95",
     "Error handling - GlobalExceptionHandler.java: 400 / 404 / 422 / 503 / 504", 1, 12),
    ("SellerProps", f"{REPO}/blob/{B}/clients/webserver/src/main/resources/application-seller.properties",
     "Configuration - one webserver per node, chosen by Spring profile", 0, 7),
    ("ApiTests", f"{REPO}/blob/{B}/clients/webserver/src/test/java/com/cordarest/webserver/InvoiceApiTests.java#L240-L262",
     "Tests - InvoiceApiTests.java: MockMvc with a mocked CordaRPCOps", 1, 10),
]

BANNER_JS = """(txt) => {
  let b = document.getElementById('demo-banner');
  if (!b) { b = document.createElement('div'); b.id = 'demo-banner'; document.body.appendChild(b); }
  b.textContent = txt;
  Object.assign(b.style, {position:'fixed', left:'0', right:'0', bottom:'0', zIndex: 2147483647,
    background:'rgba(11,26,51,0.94)', color:'#fff', font:'600 19px Segoe UI, sans-serif',
    padding:'12px 24px', borderTop:'4px solid #14C4B8', letterSpacing:'0.2px'});
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 810}, record_video_dir=OUT,
                              record_video_size={"width": 1440, "height": 810}, color_scheme="light")
    page = ctx.new_page()
    for name, url, caption, scroll_to_hl, secs in TOUR:
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        time.sleep(1.0)
        page.evaluate(BANNER_JS, f"Code walkthrough  |  {caption}")
        if scroll_to_hl:
            # GitHub highlights the #L range; bring its first line near the top
            try:
                first = url.split("#L")[1].split("-")[0]
                page.locator(f"#LC{first}, [data-line-number='{first}']").first.scroll_into_view_if_needed(timeout=5000)
                page.mouse.move(800, 400); page.mouse.wheel(0, 260)
            except Exception as e:
                print("scroll fallback", name, e)
        t_end = time.time() + secs
        page.mouse.move(800, 450)
        while time.time() < t_end:
            time.sleep(1.2)
            page.mouse.wheel(0, 70 if scroll_to_hl else 120)
        print("done", name)
    vid = page.video.path()
    ctx.close(); browser.close()
print("video:", vid)
