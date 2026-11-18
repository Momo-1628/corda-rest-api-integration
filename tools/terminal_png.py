"""Renders evidence text files as dark terminal-style PNGs (Pillow). Output: evidence/images/*.png"""
import os
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
EV = os.path.join(ROOT, "evidence")
OUT = os.path.join(EV, "images")
os.makedirs(OUT, exist_ok=True)

FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)
FONT_B = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 17)
TITLE_F = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
BG = (24, 28, 36); BAR = (40, 45, 56); FG = (214, 220, 228)
GREEN = (80, 220, 130); RED = (255, 105, 105); YELLOW = (240, 200, 90); CYAN = (90, 200, 230)
GREY = (130, 140, 155); MAGENTA = (200, 150, 255); ORANGE = (255, 170, 80)


def colour(line):
    if re.search(r"\bFAIL(ED)?\b", line) and "0 CHECK" not in line:
        return RED, False
    if "PASS" in line or "PASSED" in line or "BUILD SUCCESSFUL" in line or "started up" in line or "ALL CHECKS PASSED" in line:
        return GREEN, "BUILD" in line or "ALL CHECKS" in line or "started up" in line
    if re.search(r"HTTP (4|5)\d\d", line) or '"success": false' in line or '"success":false' in line:
        return ORANGE, False
    if re.search(r"HTTP 20\d", line):
        return CYAN, False
    if line.startswith(("$ ", "> ", "=====")) or line.startswith("[") and "]" in line[:4]:
        return YELLOW, True
    if line.strip().startswith(("+-", "|")):
        return MAGENTA if line.strip().startswith("+") else FG, False
    if line.startswith(("=", "-")) or "Task :" in line:
        return GREY, False
    return FG, False


def render(lines, out_name, title, max_cols=124):
    wrapped = []
    for l in lines:
        l = l.replace("\t", "    ")
        wrapped += textwrap.wrap(l, max_cols, subsequent_indent="    ", drop_whitespace=False) or [""]
    cols = max(60, min(max_cols, max(len(l) for l in wrapped)))
    cw = FONT.getbbox("M")[2]; lh = 23
    W = int(cols * cw + 60); H = 44 + 24 + len(wrapped) * lh + 24
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, 44), radius=0, fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((18 + i * 24, 15, 32 + i * 24, 29), fill=c)
    tw = d.textbbox((0, 0), title, font=TITLE_F)[2]
    d.text(((W - tw) / 2, 11), title, font=TITLE_F, fill=(200, 205, 215))
    y = 44 + 20
    for l in wrapped:
        col, bold = colour(l)
        d.text((30, y), l, font=FONT_B if bold else FONT, fill=col)
        y += lh
    im.save(os.path.join(OUT, out_name))
    print(out_name, im.size)


def read(name):
    return open(os.path.join(EV, name), encoding="utf-8", errors="replace").read().rstrip("\n").split("\n")


# 1 tests
t = read("test_results.txt")
tests = [l for l in t if "Tests >" in l]
summary_start = next(i for i, l in enumerate(t) if "JUnit summary" in l) - 1
body = [t[0], ""] + [l for l in t if l.startswith("> Task") and l.endswith(":test")] + [""] + tests + [""] + \
       [l for l in t if l.startswith("BUILD")] + t[summary_start:summary_start + 11]
render(body, "test_results.png", "Terminal - gradlew test  (Suraj Patel, 24BTRBT029)")

# 2 node start-up
n = read("node_startup.txt")
render(n, "node_startup.png", "Terminal - Corda 4.12 nodes started headless (Notary, SellerCorp, BuyerCorp)")

# 3 ERP client (split in two images)
e = read("erp_client_run.txt")
cut = next(i for i, l in enumerate(e) if l.startswith("[5]"))
render(["$ python external_erp_client.py", ""] + e[:cut], "erp_client_run_1.png", "Terminal - external ERP client (part 1: happy path)")
render(e[cut:], "erp_client_run_2.png", "Terminal - external ERP client (part 2: errors, history, both vaults)")

# 4 curl responses: issue + error cases
c = read("curl_responses.txt")
start = next(i for i, l in enumerate(c) if "POST $SELLER/api/invoices" in l or "POST http" in l or "-X POST" in l)
end = next(i for i, l in enumerate(c) if i > start + 3 and l.startswith("$ "))
render(c[start:end], "curl_issue.png", "Terminal - curl POST /api/invoices (Seller API :10050)")
err = next(i for i, l in enumerate(c) if "error cases" in l)
render(c[err:], "curl_errors.png", "Terminal - curl error cases (401 / 400 / 422 / 404)")
hist = next(i for i, l in enumerate(c) if "/history" in l and l.startswith("$ "))
render(c[hist:err], "curl_history.png", "Terminal - curl GET /api/invoices/{linearId}/history")

# 5 request log + latency
lg = read("api_request_log_seller.txt")
render(["$ tail build/run/api-seller.out.log   (RequestLoggingFilter)", ""] + [l[:150] for l in lg],
       "api_request_log.png", "Seller API - request log")
