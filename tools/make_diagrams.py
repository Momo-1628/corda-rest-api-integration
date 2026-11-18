"""Generates the 4 project diagrams as PNGs (Pillow). Output: docs/diagrams/*.png"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)
FD = "C:/Windows/Fonts/"

NAVY = (15, 32, 64); TEAL = (0, 150, 150); TEAL_L = (220, 242, 242); NAVY_L = (226, 232, 243)
GREY = (90, 98, 112); LINE = (60, 70, 90); WHITE = (255, 255, 255); BG = (250, 251, 253)
ORANGE = (230, 126, 34); ORANGE_L = (252, 236, 220); GREEN = (39, 150, 90); GREEN_L = (221, 243, 230)
RED = (200, 60, 60); RED_L = (250, 225, 225); PURPLE = (110, 80, 170); PURPLE_L = (236, 230, 248)


def font(size, bold=False, mono=False):
    name = ("consolab.ttf" if bold else "consola.ttf") if mono else ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(FD + name, size)


def tsize(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def ctext(d, cx, y, text, f, fill):
    w, _ = tsize(d, text, f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def box(d, x, y, w, h, title, lines=(), fill=NAVY_L, edge=NAVY, tf=None, lf=None, radius=16, title_fill=None):
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=edge, width=3)
    tf = tf or font(26, True); lf = lf or font(20)
    total = tsize(d, "Ag", tf)[1] + 14 + len(lines) * (tsize(d, "Ag", lf)[1] + 8)
    ty = y + (h - total) / 2 - 4
    ctext(d, x + w / 2, ty, title, tf, title_fill or edge)
    ty += tsize(d, "Ag", tf)[1] + 16
    for ln in lines:
        ctext(d, x + w / 2, ty, ln, lf, GREY)
        ty += tsize(d, "Ag", lf)[1] + 8


def arrow(d, p1, p2, color=LINE, width=3, label=None, lf=None, both=False, label_off=(0, -30), dash=False):
    x1, y1 = p1; x2, y2 = p2
    if dash:
        n = int(math.hypot(x2 - x1, y2 - y1) // 14)
        for i in range(0, n, 2):
            a = i / n; b = min((i + 1) / n, 1)
            d.line((x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), fill=color, width=width)
    else:
        d.line((x1, y1, x2, y2), fill=color, width=width)

    def head(xa, ya, xb, yb):
        ang = math.atan2(yb - ya, xb - xa); L = 16
        pts = [(xb, yb), (xb - L * math.cos(ang - 0.4), yb - L * math.sin(ang - 0.4)),
               (xb - L * math.cos(ang + 0.4), yb - L * math.sin(ang + 0.4))]
        d.polygon(pts, fill=color)
    head(x1, y1, x2, y2)
    if both:
        head(x2, y2, x1, y1)
    if label:
        lf = lf or font(19, True)
        w, h = tsize(d, label, lf)
        mx, my = (x1 + x2) / 2 + label_off[0], (y1 + y2) / 2 + label_off[1]
        d.rounded_rectangle((mx - w / 2 - 8, my - 4, mx + w / 2 + 8, my + h + 10), radius=6, fill=WHITE, outline=color, width=1)
        d.text((mx - w / 2, my), label, font=lf, fill=color)


def header(d, W, title, sub):
    d.rectangle((0, 0, W, 96), fill=NAVY)
    d.rectangle((0, 96, W, 102), fill=TEAL)
    d.text((40, 18), title, font=font(38, True), fill=WHITE)
    w, _ = tsize(d, sub, font(20))
    d.text((W - w - 40, 36), sub, font=font(20), fill=(180, 200, 220))


# ----------------------------------------------------------------------------- 1 architecture
def architecture():
    W, H = 2000, 1120
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    header(d, W, "System Architecture - REST API integration with a Corda CorDapp", "Suraj Patel | 24BTRBT029")

    # zone labels
    for x, w, t in ((30, 400, "EXTERNAL SYSTEMS"), (500, 560, "REST API LAYER (Spring Boot 3)"), (1140, 830, "CORDA NETWORK (Corda 4.12)")):
        d.rounded_rectangle((x, 130, x + w, H - 40), radius=20, outline=(200, 208, 220), width=2, fill=(255, 255, 255))
        ctext(d, x + w / 2, 145, t, font(22, True), GREY)

    # external clients
    ext = [("External ERP", ["external_erp_client.py", "(Python requests)"]),
           ("Postman / curl", ["collection + scripts"]),
           ("Web dashboard", ["browser, CORS", "Swagger UI"])]
    for i, (t, ls) in enumerate(ext):
        box(d, 70, 215 + i * 280, 320, 190, t, ls, fill=ORANGE_L, edge=ORANGE)

    # two API servers
    for i, (name, port, rpc) in enumerate((("Seller API", ":10050", "RPC :10006"), ("Buyer API", ":10060", "RPC :10009"))):
        y = 200 + i * 450
        d.rounded_rectangle((540, y, 1020, y + 400), radius=18, fill=TEAL_L, outline=TEAL, width=3)
        ctext(d, 780, y + 14, f"{name}  {port}", font(28, True), TEAL)
        layers = ["RequestLoggingFilter  +  ApiKeyFilter (X-API-KEY)", "Controllers  (validation, OpenAPI)",
                  "InvoiceService  +  GlobalExceptionHandler", f"CordaRPCOps proxy  ({rpc})"]
        for j, l in enumerate(layers):
            ly = y + 70 + j * 80
            d.rounded_rectangle((570, ly, 990, ly + 62), radius=10, fill=WHITE, outline=TEAL, width=2)
            ctext(d, 780, ly + 17, l, font(19, True if j == 3 else False), NAVY)
            if j < 3:
                arrow(d, (780, ly + 62), (780, ly + 80), color=TEAL, width=2)

    # nodes
    def node(x, y, name, x500, extra):
        d.rounded_rectangle((x, y, x + 400, y + 330), radius=18, fill=NAVY_L, outline=NAVY, width=3)
        ctext(d, x + 200, y + 14, name, font(28, True), NAVY)
        ctext(d, x + 200, y + 54, x500, font(17), GREY)
        for j, (t, c) in enumerate(extra):
            ly = y + 95 + j * 74
            d.rounded_rectangle((x + 30, ly, x + 370, ly + 58), radius=10, fill=WHITE, outline=c, width=2)
            ctext(d, x + 200, ly + 15, t, font(19), NAVY)

    node(1180, 215, "SellerCorp node", "O=SellerCorp, L=Mumbai, C=IN",
         [("CorDapp: contracts + flows", NAVY), ("Flow state machine", NAVY), ("Vault (H2): InvoiceState", GREEN)])
    node(1180, 665, "BuyerCorp node", "O=BuyerCorp, L=Bengaluru, C=IN",
         [("CorDapp: contracts + flows", NAVY), ("Flow state machine", NAVY), ("Vault (H2): InvoiceState", GREEN)])
    box(d, 1660, 450, 280, 220, "Notary", ["O=Notary, L=London", "non-validating", "uniqueness / double-spend"],
        fill=PURPLE_L, edge=PURPLE)

    # arrows: clients -> APIs
    arrow(d, (390, 310), (540, 330), color=ORANGE, label="HTTP + JSON", label_off=(0, -44))
    arrow(d, (390, 590), (540, 420), color=ORANGE)
    arrow(d, (390, 600), (540, 800), color=ORANGE)
    arrow(d, (390, 870), (540, 880), color=ORANGE, label="HTTP + JSON", label_off=(0, 14))
    # API -> node RPC
    arrow(d, (1020, 520), (1180, 450), color=TEAL, both=True, label="Corda RPC", label_off=(-10, -40))
    arrow(d, (1020, 970), (1180, 900), color=TEAL, both=True, label="Corda RPC", label_off=(-10, 10))
    # P2P
    arrow(d, (1380, 545), (1380, 665), color=NAVY, both=True, label="P2P (AMQP/TLS)", label_off=(0, -16))
    arrow(d, (1580, 400), (1660, 520), color=PURPLE, both=True)
    arrow(d, (1580, 840), (1660, 610), color=PURPLE, both=True)
    ctext(d, 1800, 690, "notarisation", font(19, True), PURPLE)

    d.text((40, H - 34), "Clients never touch RPC: they only see a documented JSON API. Each API instance is bound to one node by Spring profile.",
           font=font(19), fill=GREY)
    im.save(os.path.join(OUT, "architecture.png"))


# ----------------------------------------------------------------------------- 2 sequence
def sequence():
    W, H = 2000, 1300
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    header(d, W, "Sequence - POST /api/invoices  ->  IssueInvoiceFlow", "Suraj Patel | 24BTRBT029")
    parts = [("ERP Client", ORANGE, ORANGE_L), ("Seller REST API", TEAL, TEAL_L), ("SellerCorp node", NAVY, NAVY_L),
             ("BuyerCorp node", NAVY, NAVY_L), ("Notary", PURPLE, PURPLE_L)]
    xs = [180, 560, 960, 1380, 1780]
    for (n, c, f), x in zip(parts, xs):
        d.rounded_rectangle((x - 150, 130, x + 150, 200), radius=12, fill=f, outline=c, width=3)
        ctext(d, x, 148, n, font(25, True), c)
        arrow(d, (x, 200), (x, H - 60), color=(170, 178, 190), width=2, dash=True)
        d.polygon([(x, H - 60), (x - 1, H - 61), (x + 1, H - 61)], fill=BG)  # hide arrowhead
    msgs = [
        (0, 1, "1  POST /api/invoices  {invoiceNo, buyer, amount, ...}", ORANGE, False),
        (1, 1, "2  API key check + Bean Validation (400 / 401 on failure)", TEAL, True),
        (1, 2, "3  rpc.startFlowDynamic(IssueInvoiceFlow, ...)", TEAL, False),
        (2, 2, "4  build tx  ->  verify InvoiceContract  ->  sign (seller key)", NAVY, True),
        (2, 3, "5  CollectSignaturesFlow: send proposed tx", NAVY, False),
        (3, 3, "6  Responder checkTransaction()  ->  sign (buyer key)", NAVY, True),
        (3, 2, "7  return buyer signature", NAVY, False),
        (2, 4, "8  FinalityFlow: request notarisation", PURPLE, False),
        (4, 2, "9  notary signature (no double spend)", PURPLE, False),
        (2, 3, "10  broadcast final tx; both record in VAULT", GREEN, False),
        (2, 1, "11  SignedTransaction (txHash, output state)", TEAL, False),
        (1, 0, "12  201 Created  {success, data:{txHash, linearId, invoice}, error:null}", ORANGE, False),
    ]
    y = 260
    for a, b, text, col, selfmsg in msgs:
        f = font(21, True)
        if selfmsg:
            x = xs[a]
            d.rounded_rectangle((x - 10, y - 8, x + 10, y + 64), radius=4, fill=col)
            w, h = tsize(d, text, f)
            tx = x + 30 if a < 4 else x - w - 30
            d.rounded_rectangle((tx - 10, y + 6, tx + w + 10, y + h + 22), radius=8, fill=WHITE, outline=col, width=2)
            d.text((tx, y + 10), text, font=f, fill=col)
        else:
            x1, x2 = xs[a], xs[b]
            arrow(d, (x1 + (12 if x2 > x1 else -12), y + 40), (x2 + (-12 if x2 > x1 else 12), y + 40), color=col, width=3,
                  dash=(b < a and col != ORANGE and text.startswith(("7", "9", "11"))))
            w, h = tsize(d, text, f)
            cx = (x1 + x2) / 2
            tx = max(20, min(cx - w / 2, W - w - 20))
            d.rectangle((tx - 6, y + 4, tx + w + 6, y + h + 12), fill=BG)
            d.text((tx, y + 4), text, font=f, fill=col)
        y += 82
    im.save(os.path.join(OUT, "sequence_issue.png"))


# ----------------------------------------------------------------------------- 3 lifecycle
def lifecycle():
    W, H = 2000, 1000
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    header(d, W, "InvoiceState lifecycle (enforced by InvoiceContract)", "Suraj Patel | 24BTRBT029")
    def state(cx, cy, name, fill, edge, sub):
        d.ellipse((cx - 150, cy - 90, cx + 150, cy + 90), fill=fill, outline=edge, width=4)
        ctext(d, cx, cy - 34, name, font(36, True), edge)
        ctext(d, cx, cy + 16, sub, font(19), GREY)
    d.ellipse((140, 445, 190, 495), fill=NAVY)
    ctext(d, 165, 410, "start", font(19), GREY)
    state(560, 470, "ISSUED", NAVY_L, NAVY, "both parties hold it")
    state(1100, 300, "APPROVED", TEAL_L, TEAL, "buyer accepted")
    state(1640, 300, "PAID", GREEN_L, GREEN, "final state")
    state(1100, 720, "REJECTED", RED_L, RED, "final state")
    def lbl(x, y, lines, col):
        f1, f2 = font(22, True), font(18)
        w = max(tsize(d, lines[0], f1)[0], *(tsize(d, l, f2)[0] for l in lines[1:])) + 30
        h = 36 + 28 * (len(lines) - 1)
        d.rounded_rectangle((x - w / 2, y, x + w / 2, y + h), radius=10, fill=WHITE, outline=col, width=2)
        ctext(d, x, y + 6, lines[0], f1, col)
        for i, l in enumerate(lines[1:]):
            ctext(d, x, y + 38 + i * 28, l, f2, GREY)
    arrow(d, (190, 470), (410, 470), color=NAVY, width=4)
    lbl(300, 520, ["Issue", "POST /api/invoices", "signers: seller + buyer", "amount > 0, seller != buyer"], NAVY)
    arrow(d, (700, 410), (955, 340), color=TEAL, width=4)
    lbl(790, 210, ["Approve", "PUT /{id}/approve", "signer: buyer"], TEAL)
    arrow(d, (1250, 300), (1490, 300), color=GREEN, width=4)
    lbl(1370, 150, ["Pay", "PUT /{id}/pay", "signer: buyer"], GREEN)
    arrow(d, (700, 530), (955, 680), color=RED, width=4)
    lbl(780, 650, ["Reject", "PUT /{id}/reject", "signer: buyer"], RED)
    # invalid example
    ctext(d, 1180, 520, "ISSUED -> PAID directly  =  contract violation  ->  HTTP 422", font(21, True), RED)
    d.rounded_rectangle((300, 860, 1700, 960), radius=12, fill=WHITE, outline=(200, 208, 220), width=2)
    ctext(d, 1000, 872, "Invariants on every transition: linearId, invoiceNo, amount, currency, seller and buyer must not change.",
          font(22, True), NAVY)
    ctext(d, 1000, 912, "Each transition consumes the old state and creates a new one; the old versions stay in the vault as history.",
          font(20), GREY)
    im.save(os.path.join(OUT, "lifecycle.png"))


# ----------------------------------------------------------------------------- 4 endpoint map
def endpoints():
    W, H = 2000, 1150
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    header(d, W, "REST endpoint map", "Suraj Patel | 24BTRBT029")
    rows = [
        ("GET", "/api/health", "Liveness + RPC check (public)", "rpc.currentNodeTime()", "any"),
        ("GET", "/api/me", "Node legal identity", "rpc.nodeInfo()", "any"),
        ("GET", "/api/peers", "Other business nodes", "rpc.networkMapSnapshot()", "any"),
        ("GET", "/api/notaries", "Notary identities", "rpc.notaryIdentities()", "any"),
        ("POST", "/api/invoices", "Issue invoice -> 201 {txHash, linearId}", "IssueInvoiceFlow", "Seller"),
        ("GET", "/api/invoices?status=", "List unconsumed invoices", "vaultQueryBy (UNCONSUMED)", "any"),
        ("GET", "/api/invoices/{linearId}", "One invoice (404 if unknown)", "LinearStateQueryCriteria", "any"),
        ("PUT", "/api/invoices/{linearId}/approve", "ISSUED -> APPROVED", "ApproveInvoiceFlow", "Buyer"),
        ("PUT", "/api/invoices/{linearId}/pay", "APPROVED -> PAID", "PayInvoiceFlow", "Buyer"),
        ("PUT", "/api/invoices/{linearId}/reject", "ISSUED -> REJECTED", "RejectInvoiceFlow", "Buyer"),
        ("GET", "/api/invoices/{linearId}/history", "All consumed + unconsumed versions", "vaultQueryBy (ALL)", "any"),
    ]
    cols = [(40, 120, "Method"), (170, 560, "Path"), (740, 520, "Purpose"), (1270, 430, "Corda call"), (1710, 250, "Node")]
    y = 140
    d.rounded_rectangle((30, y, W - 30, y + 60), radius=10, fill=NAVY)
    for x, w, t in cols:
        d.text((x + 14, y + 14), t, font=font(24, True), fill=WHITE)
    y += 72
    mcol = {"GET": (GREEN, GREEN_L), "POST": (ORANGE, ORANGE_L), "PUT": (TEAL, TEAL_L)}
    for i, (m, p, purpose, call, node) in enumerate(rows):
        d.rounded_rectangle((30, y, W - 30, y + 66), radius=10, fill=WHITE if i % 2 else (244, 247, 251), outline=(220, 226, 235))
        c, f = mcol[m]
        d.rounded_rectangle((50, y + 14, 150, y + 52), radius=8, fill=f, outline=c, width=2)
        ctext(d, 100, y + 22, m, font(22, True, mono=True), c)
        d.text((184, y + 24), p, font=font(22, True, mono=True), fill=NAVY)
        d.text((754, y + 18), purpose, font=font(22), fill=(40, 46, 60))
        d.text((1284, y + 24), call, font=font(21, mono=True), fill=PURPLE if "Flow" in call else GREY)
        d.text((1724, y + 18), node, font=font(22, True), fill=ORANGE if node == "Seller" else TEAL if node == "Buyer" else GREY)
        y += 74
    y += 10
    d.text((40, y), "All responses: { success, data, error{status, code, message, details}, timestamp }    |    "
                    "Header: X-API-KEY (all except /api/health)", font=font(21, True), fill=NAVY)
    d.text((40, y + 40), "Status codes: 200/201 OK  |  400 validation  |  401 API key  |  404 unknown linearId  |  "
                         "422 flow/contract rejected  |  503 node down  |  504 flow timeout", font=font(21), fill=GREY)
    im.save(os.path.join(OUT, "endpoint_map.png"))


if __name__ == "__main__":
    architecture(); sequence(); lifecycle(); endpoints()
    print("diagrams written to", os.path.abspath(OUT))
