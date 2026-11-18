"""Builds deliverables/Topic25_Corda_REST_API_24BTRBT029.pptx (16:9, navy + teal) with narration in the notes."""
import json
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P = lambda *a: os.path.join(ROOT, *a)
OUT = P("deliverables", "Topic25_Corda_REST_API_24BTRBT029.pptx")

NAVY = RGBColor(0x0B, 0x1A, 0x33); NAVY2 = RGBColor(0x13, 0x28, 0x4A); NAVY3 = RGBColor(0x1C, 0x36, 0x60)
TEAL = RGBColor(0x14, 0xC4, 0xB8); TEAL_D = RGBColor(0x0E, 0x96, 0x96); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xC9, 0xD6, 0xE8); MUTED = RGBColor(0x8A, 0x9B, 0xB5); ORANGE = RGBColor(0xF3, 0x9C, 0x4A)
RED = RGBColor(0xF0, 0x6E, 0x6E); GREEN = RGBColor(0x5B, 0xD6, 0x8E)
FONT = "Segoe UI"

LS = json.load(open(P("evidence", "latency_results.json")))["summary"]
LG = json.load(open(P("evidence", "latency_get.json")))

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
SN = [0]


def bg(slide, color=NAVY):
    f = slide.background.fill; f.solid(); f.fore_color.rgb = color


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1.25)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, txt, size=18, color=WHITE, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         italic=False, font=FONT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.03)
    lines = txt if isinstance(txt, list) else [txt]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold; r.font.italic = italic; r.font.name = font
    return tb


def shape_text(s, txt, size=14, color=WHITE, bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE):
    tf = s.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.1); tf.margin_top = tf.margin_bottom = Inches(0.05)
    lines = txt if isinstance(txt, list) else [txt]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        if isinstance(ln, tuple):
            r = p.add_run(); r.text = ln[0]; r.font.size = Pt(ln[1]); r.font.bold = ln[2]; r.font.color.rgb = ln[3] if len(ln) > 3 else color
        else:
            r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
        r.font.name = FONT


def bullets(slide, x, y, w, h, items, size=19, gap=10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap); p.line_spacing = 1.05
        r0 = p.add_run(); r0.text = "■  "; r0.font.size = Pt(size - 6); r0.font.color.rgb = TEAL; r0.font.name = FONT
        if isinstance(it, tuple):
            r = p.add_run(); r.text = it[0]; r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = WHITE; r.font.name = FONT
            r = p.add_run(); r.text = it[1]; r.font.size = Pt(size); r.font.color.rgb = SOFT; r.font.name = FONT
        else:
            r = p.add_run(); r.text = it; r.font.size = Pt(size); r.font.color.rgb = SOFT; r.font.name = FONT
    return tb


def picture(slide, path, x, y, w, h, card=True, pad=0.08):
    iw, ih = Image.open(path).size
    if card:
        rect(slide, x, y, w, h, WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
        x, y, w, h = x + pad, y + pad, w - 2 * pad, h - 2 * pad
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    slide.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def table(slide, x, y, w, rows, col_w, size=13, header_fill=TEAL_D, row_h=0.42):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    t = shp.table
    for i, cw in enumerate(col_w):
        t.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        t.rows[r].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = t.cell(r, c); cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (NAVY2 if r % 2 else NAVY3)
            cell.margin_left = cell.margin_right = Inches(0.08); cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]
            col = WHITE
            if isinstance(val, tuple):
                val, col = val
            rr = p.add_run(); rr.text = str(val); rr.font.size = Pt(size); rr.font.name = FONT
            rr.font.bold = r == 0; rr.font.color.rgb = WHITE if r == 0 else col
    return t


def new_slide(title, notes, kicker=None):
    s = prs.slides.add_slide(BLANK); bg(s); SN[0] += 1
    rect(s, 0, 0, 0.18, 7.5, TEAL)
    if kicker:
        text(s, 0.6, 0.3, 9, 0.35, kicker.upper(), size=12, color=TEAL, bold=True)
    text(s, 0.6, 0.55, 12.2, 0.8, title, size=32, bold=True)
    rect(s, 0.62, 1.38, 1.1, 0.06, TEAL)
    text(s, 0.6, 7.03, 8, 0.3, "Suraj Patel  |  24BTRBT029  |  Corda Development - Topic 25", size=10, color=MUTED)
    text(s, 11.9, 7.03, 0.9, 0.3, f"{SN[0]:02d} / 17", size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


# --------------------------------------------------------------------------------------------- 1 title
s = prs.slides.add_slide(BLANK); bg(s); SN[0] += 1
rect(s, 0, 0, 13.333, 7.5, NAVY)
rect(s, 8.9, 0, 4.433, 7.5, NAVY2)
rect(s, 8.9, 0, 0.08, 7.5, TEAL)
text(s, 0.8, 0.9, 7.8, 0.4, "CORDA DEVELOPMENT  |  TOPIC 25  |  MODULE M5", size=14, color=TEAL, bold=True)
text(s, 0.8, 1.45, 7.9, 2.4, ["Implementation of an", "External REST API Integration", "with a Corda CorDapp"], size=36, bold=True)
rect(s, 0.82, 3.95, 1.3, 0.07, TEAL)
text(s, 0.8, 4.2, 7.8, 0.5, "Invoice management between companies, exposed to ERP and web apps through REST", size=17, color=SOFT)
text(s, 0.8, 5.2, 7.8, 0.5, "Suraj Patel – 24BTRBT029", size=24, bold=True)
text(s, 0.8, 5.75, 7.8, 0.9, ["B.Tech CSE (Blockchain Technology), Semester V", "Jain (Deemed-to-be University)"], size=15, color=SOFT)
for i, (t1, t2, col) in enumerate([("External ERP", "HTTP + JSON", ORANGE), ("REST API", "Spring Boot 3", TEAL),
                                    ("Corda 4.12", "Seller + Buyer + Notary", RGBColor(0x9D, 0xB4, 0xFF))]):
    y = 1.35 + i * 1.85
    b = rect(s, 9.6, y, 3.1, 1.25, NAVY3, line=col, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    shape_text(b, [(t1, 20, True, WHITE), (t2, 13, False, SOFT)])
    if i < 2:
        a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(10.95), Inches(y + 1.3), Inches(0.4), Inches(0.5))
        a.fill.solid(); a.fill.fore_color.rgb = TEAL; a.line.fill.background()
s.notes_slide.notes_text_frame.text = (
    "Hello, I am Suraj Patel, USN 24BTRBT029, from B.Tech Computer Science and Engineering with specialisation in "
    "Blockchain Technology, Semester five, at Jain University. My mini project for the Corda Development course is "
    "topic twenty five: Implementation of an External REST API Integration with a Corda CorDapp. In this project I "
    "built an invoice application on Corda 4.12, and then I put a Spring Boot REST API in front of it, so that "
    "outside systems like an ERP or a web app can use the ledger with simple JSON calls. In the next few minutes I "
    "will walk you through the problem, my design, the implementation and the results.")

# --------------------------------------------------------------------------------------------- 2 problem
s = new_slide("Problem Statement", (
    "Let me start with the problem. When two companies trade, the seller and the buyer each keep their own copy of "
    "the same invoice in their own ERP system. These copies drift apart. One side says the invoice is approved, the "
    "other side says it is still pending, and finance teams waste days reconciling them. Corda can fix this, because "
    "both companies can share one signed and notarised invoice. But a Corda node is only reachable through Corda RPC, "
    "which needs Java libraries and Corda classes on the client. Normal business software cannot call it directly. "
    "So my problem was to build a secure REST bridge between the two worlds."), kicker="Why this project")
bullets(s, 0.6, 1.75, 6.3, 4.6, [
    ("Two copies, two truths: ", "seller and buyer track the same invoice in separate ERPs"),
    ("Manual reconciliation: ", "disputes on amount, approval and payment status"),
    ("Corda gives one shared record, ", "signed by both and notarised"),
    ("But Corda RPC is not web-friendly: ", "Java/Kotlin client, CorDapp classes, AMQP"),
    ("Goal: ", "a secure, documented REST API so any system can use the ledger"),
], size=18)
for i, (name, status, col) in enumerate([("Seller ERP", "INV-101: SENT", ORANGE), ("Buyer ERP", "INV-101: UNDER REVIEW", RED)]):
    b = rect(s, 7.5 + i * 2.75, 1.9, 2.45, 1.5, NAVY3, line=col, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    shape_text(b, [(name, 18, True, WHITE), (status, 13, False, col)])
text(s, 9.7, 2.35, 0.6, 0.6, "≠", size=36, color=RED, bold=True, align=PP_ALIGN.CENTER)
b = rect(s, 7.5, 4.0, 5.2, 1.0, NAVY3, line=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
shape_text(b, [("Corda ledger: one shared, signed invoice", 16, True, WHITE)])
b = rect(s, 7.5, 5.35, 5.2, 1.2, NAVY2, line=MUTED, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
shape_text(b, [("Missing piece", 13, True, TEAL), ("An HTTP / JSON door that ERPs and web apps can use", 15, False, WHITE)])

# --------------------------------------------------------------------------------------------- 3 objectives
s = new_slide("Objectives", (
    "I set five objectives for this project. First, model the invoice on the ledger as a linear state with four "
    "statuses: issued, approved, paid and rejected. Second, enforce the business rules in a contract and implement "
    "the four flows with proper signatures and notarisation. Third, and this is the core of the topic, build a "
    "production style REST API with authentication, validation and clear error codes. Fourth, prove that it really "
    "works from outside, using a Python ERP client, Postman and curl. And fifth, test everything automatically and "
    "measure the API latency."), kicker="What I set out to do")
objs = [("1", "Model", "InvoiceState (LinearState) with ISSUED → APPROVED → PAID / REJECTED"),
        ("2", "Enforce", "InvoiceContract + 4 flows with CollectSignatures, Notary, Finality"),
        ("3", "Expose", "Spring Boot 3 REST API: 11 endpoints, API key, validation, Swagger"),
        ("4", "Integrate", "Python ERP client, Postman collection and curl scripts"),
        ("5", "Verify", "42 automated tests + latency of 20 POST calls")]
for i, (n, h, d) in enumerate(objs):
    y = 1.8 + i * 1.0
    c = rect(s, 0.6, y, 0.75, 0.75, TEAL, shape=MSO_SHAPE.OVAL); shape_text(c, [(n, 22, True, NAVY)])
    b = rect(s, 1.55, y, 11.1, 0.78, NAVY2, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
    shape_text(b, [(h + ":  ", 19, True, WHITE)], align=PP_ALIGN.LEFT)
    p = b.text_frame.paragraphs[0]; r = p.add_run(); r.text = d; r.font.size = Pt(17); r.font.color.rgb = SOFT; r.font.name = FONT

# --------------------------------------------------------------------------------------------- 4 why rest
s = new_slide("Why REST over Corda?", (
    "Why put REST in front of Corda at all? Corda RPC is powerful, but it is designed for Java and Kotlin clients. "
    "The client needs the Corda RPC library and the CorDapp classes, it talks AMQP over Artemis, and it receives "
    "Corda types like SignedTransaction. A browser cannot use it, and an SAP or dot net system cannot easily use it "
    "either. REST is the opposite: any language can send HTTP, JSON is universal, Swagger documents the contract, and "
    "standard tools like API keys, CORS and load balancers just work. So I kept RPC inside the trusted server and "
    "exposed only REST to the outside."), kicker="Design decision")
table(s, 0.6, 1.8, 12.1, [
    ["Aspect", "Corda RPC (direct)", "REST API (this project)"],
    ["Client language", "Java / Kotlin only", ("Any: Python, JS, .NET, SAP, curl", GREEN)],
    ["Protocol", "AMQP over Artemis, custom serialisation", ("HTTP + JSON", GREEN)],
    ["Client dependencies", "corda-rpc + CorDapp jars on classpath", ("None", GREEN)],
    ["Browser / web apps", "Not possible", ("Yes, with CORS", GREEN)],
    ["Contract & docs", "Java interfaces", ("OpenAPI 3 + Swagger UI", GREEN)],
    ["Errors", "Corda exceptions", ("HTTP 400 / 401 / 404 / 422 + JSON envelope", GREEN)],
], [2.9, 4.4, 4.8], size=15, row_h=0.55)
text(s, 0.6, 5.95, 12.1, 0.8, "RPC stays inside the trusted server; outside systems only see a documented, authenticated JSON API.",
     size=17, color=TEAL, bold=True)

# --------------------------------------------------------------------------------------------- 5 concepts
s = new_slide("Corda Concepts Used", (
    "These are the Corda concepts I used. The invoice is a LinearState, so every version keeps the same linear ID, "
    "and the API can use that ID in its URLs. Corda follows the UTXO model: each approve, pay or reject consumes the "
    "old state and creates a new one, which gives me a free audit trail. The contract runs on every node. Flows "
    "collect signatures, and a non validating notary prevents double spends. Finally, the vault stores the states, "
    "and RPC is the only door between my REST layer and the node."), kicker="Building blocks")
tiles = [("LinearState", "same linearId across versions → /api/invoices/{linearId}"),
         ("UTXO consume / create", "each transition spends the old state → /history"),
         ("Contract & commands", "Issue, Approve, Pay, Reject verified on every node"),
         ("Flows & signatures", "@InitiatingFlow, @StartableByRPC, CollectSignaturesFlow"),
         ("Notary & finality", "non-validating notary, FinalityFlow records in both vaults"),
         ("Vault & RPC", "vaultQueryBy + startFlowDynamic via CordaRPCOps")]
for i, (h, d) in enumerate(tiles):
    x = 0.6 + (i % 3) * 4.08; y = 1.85 + (i // 3) * 2.45
    b = rect(s, x, y, 3.85, 2.2, NAVY2, line=NAVY3, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    rect(s, x, y, 3.85, 0.09, TEAL)
    text(s, x + 0.25, y + 0.3, 3.4, 0.5, h, size=20, bold=True)
    text(s, x + 0.25, y + 0.95, 3.4, 1.2, d, size=15, color=SOFT)

# --------------------------------------------------------------------------------------------- 6 architecture
s = new_slide("System Architecture", (
    "Here is the architecture. On the left are the external systems: my Python ERP client, Postman or curl, and any "
    "web dashboard. They only speak HTTP and JSON. In the middle is my REST layer. I run one Spring Boot instance per "
    "node: the Seller API on port 10050 and the Buyer API on port 10060. Each request passes through a logging filter "
    "and an API key filter, then the controller, then the service, which calls the node through CordaRPCOps. On the "
    "right are the Corda nodes, SellerCorp and BuyerCorp, which talk to each other and to the notary over peer to "
    "peer messaging."), kicker="Three layers")
picture(s, P("docs", "diagrams", "architecture.png"), 0.6, 1.7, 12.1, 5.2)

# --------------------------------------------------------------------------------------------- 7 state & contract
s = new_slide("State & Contract Design", (
    "This slide shows the ledger design. The InvoiceState holds the linear ID, the invoice number, the seller and "
    "buyer parties, the amount and currency, a description, the due date, the status and remarks. Both parties are "
    "participants. The contract has four commands. Issue needs no input, an amount above zero, different seller and "
    "buyer, and both signatures. Approve, Pay and Reject need only the buyer's signature, and they must follow the "
    "lifecycle shown on the right. For every transition, the invoice number, amount and parties cannot change."),
    kicker="Ledger layer")
b = rect(s, 0.6, 1.75, 4.6, 4.95, NAVY2, line=NAVY3, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
text(s, 0.85, 1.9, 4.2, 0.4, "InvoiceState  (LinearState)", size=17, bold=True, color=TEAL)
fields = ["linearId : UniqueIdentifier", "invoiceNo : String", "seller, buyer : Party", "amount : BigDecimal",
          "currency, description : String", "dueDate : LocalDate", "status : ISSUED | APPROVED | PAID | REJECTED",
          "remarks : String", "participants = seller + buyer"]
text(s, 0.85, 2.4, 4.25, 3.9, fields, size=13.5, color=SOFT, font="Consolas")
text(s, 0.85, 5.6, 4.2, 1.0, ["Invariant: invoiceNo, amount,", "currency, parties never change"], size=14, color=ORANGE, bold=True)
picture(s, P("docs", "diagrams", "lifecycle.png"), 5.45, 1.75, 7.25, 3.65)
table(s, 5.45, 5.55, 7.25, [["Command", "Transition", "Signers"],
                            ["Issue", "– → ISSUED", "seller + buyer"],
                            ["Approve / Pay / Reject", "per lifecycle", "buyer"]], [2.6, 2.45, 2.2], size=12.5, row_h=0.37)

# --------------------------------------------------------------------------------------------- 8 flow design
s = new_slide("Flow Design", (
    "Now the flows. This sequence diagram shows what happens when the ERP posts a new invoice. The API checks the key "
    "and validates the body, then calls startFlowDynamic on the seller node. The IssueInvoiceFlow builds the "
    "transaction, verifies the contract and signs it. Through CollectSignaturesFlow, the buyer node checks the "
    "proposal and adds its signature. FinalityFlow then gets the notary signature and records the transaction in both "
    "vaults. Finally the API returns 201 with the transaction hash and linear ID. Approve, pay and reject share one "
    "base flow that the buyer starts."), kicker="Workflow layer")
bullets(s, 0.6, 1.8, 3.9, 4.9, [
    ("IssueInvoiceFlow: ", "seller builds, signs, collects buyer signature"),
    ("Responder ", "checks: I am the buyer, sender is the seller"),
    ("FinalityFlow: ", "notarise + record in both vaults"),
    ("Approve / Pay / Reject: ", "one shared base flow, started by the buyer"),
    ("Clear errors: ", "\"must be APPROVED to move to PAID\""),
], size=16, gap=9)
picture(s, P("docs", "diagrams", "sequence_issue.png"), 4.7, 1.7, 8.0, 5.2)

# --------------------------------------------------------------------------------------------- 9 api design
s = new_slide("REST API Design", (
    "This is the REST API design. There are eleven endpoints. Four are about the node: me, peers, notaries and a "
    "public health check. The invoice endpoints follow normal REST style. POST on slash api slash invoices issues an "
    "invoice and returns 201. GET lists invoices, optionally filtered by status, or fetches one by linear ID. PUT "
    "approve, pay and reject start the matching flows on the buyer node, and history returns every consumed and "
    "unconsumed version. Every response uses the same envelope with success, data, error and timestamp."),
    kicker="Interface")
picture(s, P("docs", "diagrams", "endpoint_map.png"), 0.6, 1.7, 12.1, 5.2)

# --------------------------------------------------------------------------------------------- 10 security
s = new_slide("Security & Error Handling", (
    "Since this API is the front door to a ledger, I added production style protection. Every call except health "
    "needs an X-API-KEY header, otherwise the API answers 401. Request bodies are checked with bean validation, so a "
    "negative amount or a wrong currency code gives 400 with a clear list of problems. A global exception handler "
    "maps an unknown linear ID to 404, and a flow or contract rejection to 422, which tells the client the request "
    "was understood but refused by business rules. I also enabled CORS and added request logging with a request ID."),
    kicker="Production-style details")
bullets(s, 0.6, 1.8, 5.6, 4.9, [
    ("API key: ", "X-API-KEY header per node, constant-time check"),
    ("Validation: ", "@NotBlank, @DecimalMin, ISO currency, due date"),
    ("Global handler: ", "Corda exceptions → clean JSON errors"),
    ("Envelope: ", "{ success, data, error, timestamp }"),
    ("CORS + logging: ", "browser clients, X-Request-Id, timing"),
], size=17, gap=11)
table(s, 6.5, 1.8, 6.2, [["Status", "When"],
                         [("200 / 201", GREEN), "success / invoice issued"],
                         [("400", ORANGE), "validation, bad UUID, unknown buyer"],
                         [("401", ORANGE), "missing or wrong API key"],
                         [("404", ORANGE), "unknown linearId"],
                         [("422", RED), "flow or contract rejected"],
                         [("503 / 504", RED), "node unreachable / flow timeout"]], [1.6, 4.6], size=15, row_h=0.6)

# --------------------------------------------------------------------------------------------- 11 tech stack
s = new_slide("Tech Stack", (
    "Here is my tech stack. The ledger runs on Corda 4.12 Community Edition with Java 17. I started from the official "
    "R3 Java template and built it with Gradle 7.6. The REST layer uses Spring Boot 3.2 with Spring Web, Bean "
    "Validation and springdoc OpenAPI for Swagger. For testing I used the Corda ledger DSL, MockNetwork, and Spring "
    "MockMvc with Mockito. On the client side, the ERP simulation is written in Python with the requests library, "
    "and I also provide a Postman collection and curl scripts."), kicker="Tools")
stack = [("Corda 4.12", "Community Edition, H2 vault"), ("JDK 17", "Temurin 17.0.20"), ("Gradle 7.6", "R3 cordapp-template-java"),
         ("Spring Boot 3.2.5", "Web, Validation, Tomcat"), ("springdoc 2.5", "OpenAPI 3 + Swagger UI"), ("Corda RPC", "CordaRPCOps client"),
         ("Testing", "Ledger DSL, MockNetwork, MockMvc"), ("Python 3", "requests: ERP client, benchmark"), ("Postman + curl", "collection, sh / ps1 scripts")]
for i, (h, d) in enumerate(stack):
    x = 0.6 + (i % 3) * 4.08; y = 1.8 + (i // 3) * 1.65
    b = rect(s, x, y, 3.85, 1.45, NAVY2, line=NAVY3, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    rect(s, x + 0.18, y + 0.35, 0.09, 0.75, TEAL)
    text(s, x + 0.45, y + 0.25, 3.3, 0.5, h, size=20, bold=True)
    text(s, x + 0.45, y + 0.78, 3.3, 0.5, d, size=14, color=SOFT)

# --------------------------------------------------------------------------------------------- 12 tests
s = new_slide("Results – Tests", (
    "Now the results, starting with the tests. I wrote forty two automated tests and all of them pass. Fifteen "
    "contract tests use the MockServices ledger DSL and cover valid and invalid cases for every command, like a zero "
    "amount, a missing buyer signature, or a changed amount. Six flow tests run on an in-memory MockNetwork with a "
    "notary and both companies, including issue, approve, pay and issue, reject. And twenty one API tests use MockMvc "
    "with a mocked CordaRPCOps to check routing, the API key, validation and error mapping."), kicker="Automated testing")
b = rect(s, 0.6, 1.8, 4.6, 1.9, NAVY2, line=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
shape_text(b, [("42 / 42", 54, True, TEAL), ("tests passing  -  BUILD SUCCESSFUL", 15, False, SOFT)])
table(s, 0.6, 4.0, 4.6, [["Suite", "Tests"], ["Contract (ledger DSL)", "15"], ["Flow (MockNetwork)", "6"],
                         ["REST API (MockMvc)", "21"]], [3.4, 1.2], size=15, row_h=0.6)
picture(s, P("evidence", "images", "test_summary_slide.png"), 5.5, 1.7, 7.2, 5.2, card=False)

# --------------------------------------------------------------------------------------------- 13 live demo
s = new_slide("Results – Live Demo", (
    "Next, the live demo. I deployed three nodes, notary, SellerCorp and BuyerCorp, started them headless, and "
    "started both APIs. On the left is the Swagger UI that springdoc generates for the seller API. On the right is my "
    "external ERP client. It issued three invoices, approved and paid one, approved another and rejected the third. "
    "It also triggered every error case: a wrong key gave 401, a negative amount gave 400, paying an unapproved "
    "invoice gave 422, and an unknown ID gave 404. At the end, both vaults showed exactly the same invoices."),
    kicker="Running network")
picture(s, P("evidence", "screenshots", "swagger_ui_top.png"), 0.6, 1.75, 5.0, 4.45)
picture(s, P("evidence", "images", "erp_highlights_slide.png"), 5.8, 1.75, 6.9, 4.45, card=False)
text(s, 0.6, 6.35, 12.1, 0.5, "3 invoices issued  •  approve + pay  •  reject  •  401 / 400 / 422 / 404 shown  •  both vaults identical",
     size=15, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

# --------------------------------------------------------------------------------------------- 14 performance
s = new_slide("Performance Analysis", (
    f"For performance, I timed twenty sequential POST calls to slash api slash invoices, after two warm up calls. "
    f"Each call runs the whole flow, including the buyer signature and notarisation. The average was about "
    f"{LS['average_ms']:.0f} milliseconds, the fastest was {LS['min_ms']:.0f} and the slowest was {LS['max_ms']:.0f} "
    f"milliseconds. A simple read, GET invoices, took only about {LG['average_ms']:.0f} milliseconds. This shows the "
    f"REST layer adds very little; almost all the write time is Corda consensus, signatures and notarisation. All "
    f"five JVMs ran on one laptop, so real servers should do better."), kicker="Latency of 20 calls")
picture(s, P("docs", "diagrams", "latency_chart.png"), 0.6, 1.7, 7.9, 4.0)
table(s, 8.75, 1.7, 3.95, [["Metric", "POST", "GET"],
                           ["Average", f"{LS['average_ms']:.0f} ms", f"{LG['average_ms']:.0f} ms"],
                           ["Minimum", f"{LS['min_ms']:.0f} ms", f"{LG['min_ms']:.0f} ms"],
                           ["Maximum", f"{LS['max_ms']:.0f} ms", f"{LG['max_ms']:.0f} ms"],
                           ["Median", f"{LS['median_ms']:.0f} ms", "-"],
                           ["Throughput", f"{LS['throughput_tx_per_s']:.1f} tx/s", "-"]], [1.55, 1.25, 1.15], size=14, row_h=0.55)
bullets(s, 0.6, 5.75, 12.1, 1.2, [("Writes ≈ 7x reads: ", "time is spent in signatures, P2P and notarisation, not in the REST layer"),
                                  ("Warm-up excluded: ", "the first call after start-up took ~8.4 s (class loading, JIT, P2P sessions)")], size=16, gap=6)

# --------------------------------------------------------------------------------------------- 15 adv & limits
s = new_slide("Advantages & Limitations", (
    "Let me be honest about the strengths and weaknesses. The big advantage is reach: any system that can send HTTP "
    "can now use the ledger, with no Corda libraries. The API is documented, validated and secured at the edge, and "
    "the ledger guarantees stay intact, with a free audit trail. On the limitation side, one shared API key per node "
    "is quite coarse. Write calls wait about half a second for finality. The list endpoints do not have pagination "
    "yet, and the measurements were made on a single laptop, not on production servers."), kicker="Evaluation")
for col, (head, colr, items) in enumerate([
        ("Advantages", GREEN, ["Any language / tool can use the ledger", "Self-documenting: Swagger + one envelope",
                               "Bad requests stopped before the node", "Signatures, notary, contract unchanged",
                               "Free audit trail via /history"]),
        ("Limitations", ORANGE, ["Shared API key, no per-user roles", "Writes block ~0.6 s until finality",
                                 "No pagination on list endpoints", "No RPC auto-reconnect / circuit breaker",
                                 "Measured on one laptop, HTTP not HTTPS"])]):
    x = 0.6 + col * 6.2
    b = rect(s, x, 1.8, 5.9, 4.95, NAVY2, line=colr, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
    text(s, x + 0.3, 1.95, 5.3, 0.55, head, size=22, bold=True, color=colr)
    bullets(s, x + 0.3, 2.75, 5.4, 4.0, items, size=19, gap=17)

# --------------------------------------------------------------------------------------------- 16 conclusion
s = new_slide("Conclusion & Future Scope", (
    "To conclude, I built a complete REST integration for a Corda CorDapp. The invoice lifecycle is protected by a "
    "contract and four flows, and a Spring Boot gateway turns eleven JSON endpoints into flows and vault queries. "
    "All forty two tests pass, and a Python ERP ran the full lifecycle and every error case on a live network. In the "
    "future, I would replace the API key with OAuth2 and JWT, push ledger events to clients with webhooks or Kafka "
    "instead of polling, add idempotency keys and pagination, and package everything with Docker Compose."),
    kicker="Wrapping up")
bullets(s, 0.6, 1.8, 6.0, 4.9, [
    ("Built: ", "invoice CorDapp + Spring Boot 3 REST gateway"),
    ("Secure & clear: ", "API key, validation, 400/401/404/422"),
    ("Proven: ", "42 tests + live ERP client on 3 nodes"),
    ("Fast enough: ", f"~{LS['average_ms']:.0f} ms write, ~{LG['average_ms']:.0f} ms read"),
    ("Lesson: ", "a thin REST layer makes Corda usable by ordinary software"),
], size=17, gap=12)
fut = [("OAuth2 / JWT", "per-user identity and roles"), ("Webhooks", "notify ERPs on vault updates"),
       ("Kafka events", "stream vaultTrack changes"), ("Idempotency + paging", "safe retries, large lists"),
       ("Docker Compose", "one-command deployment")]
text(s, 7.0, 1.75, 5.7, 0.45, "Future scope", size=18, bold=True, color=TEAL)
for i, (h, d) in enumerate(fut):
    y = 2.3 + i * 0.9
    b = rect(s, 7.0, y, 5.7, 0.78, NAVY2, line=NAVY3, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.15)
    shape_text(b, [(h + "  ", 17, True, WHITE)], align=PP_ALIGN.LEFT)
    r = b.text_frame.paragraphs[0].add_run(); r.text = "– " + d; r.font.size = Pt(14); r.font.color.rgb = SOFT; r.font.name = FONT

# --------------------------------------------------------------------------------------------- 17 thanks
s = new_slide("Thank You", (
    "That brings me to the end of my presentation. All the code, the tests, the evidence and the Postman collection "
    "are available in my public GitHub repository, corda rest api integration, under the account Momo-1628. The main "
    "references I used are the Corda 4.12 documentation, the R3 CorDapp template, the Spring Boot reference "
    "documentation and the springdoc project. Thank you very much for watching and listening. I am Suraj Patel, USN "
    "24BTRBT029, and I am happy to answer any questions."), kicker="Questions welcome")
text(s, 0.6, 1.8, 6.0, 0.8, "Suraj Patel – 24BTRBT029", size=26, bold=True)
text(s, 0.6, 2.55, 6.0, 0.9, ["B.Tech CSE (Blockchain Technology), Sem V", "Jain (Deemed-to-be University)"], size=16, color=SOFT)
b = rect(s, 0.6, 3.75, 6.0, 1.1, NAVY2, line=TEAL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
shape_text(b, [("Source code", 13, True, TEAL), ("github.com/Momo-1628/corda-rest-api-integration", 16, True, WHITE)])
text(s, 7.0, 1.75, 5.7, 0.45, "References", size=18, bold=True, color=TEAL)
bullets(s, 7.0, 2.3, 5.7, 4.5, [
    "Corda 4.12 docs – docs.r3.com",
    "R3 cordapp-template-java – github.com/corda",
    "Spring Boot 3 reference – docs.spring.io",
    "springdoc-openapi – springdoc.org",
    "Jakarta Bean Validation 3.0 – jakarta.ee",
], size=16, gap=12)

# narration lives in tools/narration.py (one place for the notes and the video)
import sys as _sys
_sys.path.insert(0, os.path.dirname(__file__))
from narration import NOTES
assert len(NOTES) == len(prs.slides)
for _sl, _n in zip(prs.slides, NOTES):
    _sl.notes_slide.notes_text_frame.text = _n

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
for i, sl in enumerate(prs.slides, 1):
    n = sl.notes_slide.notes_text_frame.text
    print(i, len(n.split()), "words")
