"""Builds deliverables/Project_Report_24BTRBT029.docx with python-docx."""
import json
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "deliverables", "Project_Report_24BTRBT029.docx")
P = lambda *a: os.path.join(ROOT, *a)
NAVY = RGBColor(0x0F, 0x20, 0x40); TEAL = RGBColor(0x00, 0x96, 0x96); GREY = RGBColor(0x55, 0x5E, 0x6E)

lat = json.load(open(P("evidence", "latency_results.json")))
LS = lat["summary"]; LG = json.load(open(P("evidence", "latency_get.json")))

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(2.3); sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.0)

st = doc.styles
st["Normal"].font.name = "Calibri"; st["Normal"].font.size = Pt(11)
st["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st["Normal"].paragraph_format.space_after = Pt(6); st["Normal"].paragraph_format.line_spacing = 1.15
for lvl, size, col in ((1, 16, NAVY), (2, 12.5, TEAL)):
    h = st[f"Heading {lvl}"]; h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True
    h.font.color.rgb = col; h.element.rPr.rFonts.set(qn("w:asciiTheme"), "minorHAnsi") if False else None
    rf = h.element.get_or_add_rPr().get_or_add_rFonts()
    for a in ("w:ascii", "w:hAnsi", "w:cs"): rf.set(qn(a), "Calibri")
    h.paragraph_format.space_before = Pt(14 if lvl == 1 else 10); h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hex_fill); tcPr.append(s)


def para(text, bold=False, italic=False, size=None, color=None, align=None, after=None, style=None):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    if align is not None: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p


def rich(parts, style=None):
    """parts: list of (text, bold) tuples."""
    p = doc.add_paragraph(style=style)
    for t, b in parts:
        r = p.add_run(t); r.bold = b
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def body(text):
    p = para(text); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; return p


def bullets(items):
    for it in items:
        if isinstance(it, tuple):
            p = doc.add_paragraph(style="List Bullet"); r = p.add_run(it[0]); r.bold = True; p.add_run(it[1])
        else:
            doc.add_paragraph(it, style="List Bullet")


def numbered(items, fmt="{}.", justify=True):
    for n, it in enumerate(items, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.7)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(fmt.format(n) + "	")
        p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
        if isinstance(it, tuple):
            r = p.add_run(it[0]); r.bold = True; p.add_run(it[1])
        else:
            p.add_run(it)


FIG = [0]


def figure(path, caption, width_cm=16.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width_cm))
    FIG[0] += 1
    c = para(f"Figure {FIG[0]}: {caption}", italic=True, size=9.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)


def figure_pair(a, b, width_cm=7.9):
    t = doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (path, cap) in enumerate((a, b)):
        cell = t.rows[0].cells[i]; cell.width = Cm(8.2)
        pp = cell.paragraphs[0]; pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pp.add_run().add_picture(path, width=Cm(width_cm))
        FIG[0] += 1
        c = t.rows[1].cells[i]; c.width = Cm(8.2); cp = c.paragraphs[0]; cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(f"Figure {FIG[0]}: {cap}"); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GREY
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


TAB = [0]


def table(headers, rows, widths, caption=None, font=9.5):
    if caption:
        TAB[0] += 1
        c = para(f"Table {TAB[0]}: {caption}", bold=True, size=9.5, color=NAVY, after=3)
        c.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1 + len(rows), cols=len(headers)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]; cell.text = ""; r = cell.paragraphs[0].add_run(h)
        r.bold = True; r.font.size = Pt(font); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); shade(cell, "0F2040")
    for ri, row in enumerate(rows):
        for i, v in enumerate(row):
            cell = t.rows[ri + 1].cells[i]; cell.text = ""
            r = cell.paragraphs[0].add_run(str(v)); r.font.size = Pt(font)
            if ri % 2: shade(cell, "EEF3F8")
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
            row.cells[i].paragraphs[0].paragraph_format.space_after = Pt(1)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def code(text, caption):
    c = para(caption, bold=True, size=9.5, color=NAVY, after=2); c.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]; shade(cell, "F3F5F8"); cell.width = Cm(16.4)
    cell.text = ""
    lines = text.strip("\n").split("\n")
    p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    for i, ln in enumerate(lines):
        r = p.add_run(ln); r.font.name = "Consolas"; r.font.size = Pt(8.3)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        if i < len(lines) - 1: r.add_break()
    tbl = t._tbl; borders = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{e}"); b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "4"); b.set(qn("w:color"), "C8D0DC"); borders.append(b)
    tbl.tblPr.append(borders)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_number_footer(section):
    fp = section.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Suraj Patel (24BTRBT029)  |  Corda Development - Topic 25  |  Page "); r.font.size = Pt(8.5); r.font.color.rgb = GREY
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        run = fp.add_run(); run.font.size = Pt(8.5); run.font.color.rgb = GREY
        if kind:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); run._r.append(f)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; run._r.append(it)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# =========================================================================== COVER
sec.different_first_page_header_footer = True
for _ in range(2): para("")
para("JAIN (DEEMED-TO-BE UNIVERSITY)", bold=True, size=18, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
para("Faculty of Engineering and Technology", size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
para("Department of Computer Science and Engineering", size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=30)
para("MINI PROJECT REPORT", bold=True, size=13, color=TEAL, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
para("Implementation of an External REST API Integration with a Corda CorDapp", bold=True, size=22, color=NAVY,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
para("Topic No. 25  |  Module M5  |  Focus: API integration", size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=30)
para("Course: Corda Development", bold=True, size=13, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
para("B.Tech - Computer Science and Engineering (Blockchain Technology)", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
para("Semester V", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=40)
para("Submitted by:", size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
para("Suraj Patel (24BTRBT029)", bold=True, size=16, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
para("CSE (Blockchain Technology), Semester V", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=40)
para("Individual project  |  Academic year 2026-27", size=11, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
para("Source code: https://github.com/Momo-1628/corda-rest-api-integration", size=10, color=TEAL,
     align=WD_ALIGN_PARAGRAPH.CENTER)
page_number_footer(sec)
page_break()

# contents
para("Contents", bold=True, size=16, color=NAVY, after=10)
contents = ["Title", "Problem Statement", "Objectives", "Introduction", "Corda/Blockchain Concepts Used",
            "System Architecture", "Methodology", "Implementation", "Results", "Screenshots", "Analysis",
            "Advantages and Limitations", "Conclusion", "References"]
for i, c in enumerate(contents, 1):
    para(f"{i}.  {c}", size=12, after=4)
para("")
para("Declaration", bold=True, size=13, color=NAVY, after=4)
body("I, Suraj Patel (USN 24BTRBT029), declare that this mini project, \"Implementation of an External REST API "
     "Integration with a Corda CorDapp\", is my own individual work, carried out for the Corda Development course "
     "in Semester V. I started from the official R3 CorDapp template (Java), replaced its sample code, and designed, "
     "implemented, tested and measured everything described here myself. All external sources are listed in the "
     "References section.")
para("")
para("Suraj Patel  -  24BTRBT029", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
page_break()

# =========================================================================== 1 TITLE
doc.add_heading("1. Title", 1)
para("Implementation of an External REST API Integration with a Corda CorDapp", bold=True, size=14, color=NAVY, after=8)
table(["Item", "Detail"], [
    ["Topic", "No. 25, Module M5 - External REST API integration (focus: API integration)"],
    ["Course", "Corda Development - B.Tech CSE (Blockchain Technology), Semester V"],
    ["Student", "Suraj Patel - USN 24BTRBT029 (individual project)"],
    ["Use case", "Invoice management between two companies, exposed to ERP systems and web apps through REST"],
    ["Platform", "Corda 4.12 Community Edition, JDK 17, Spring Boot 3.2.5, springdoc-openapi 2.5, Gradle 7.6"],
    ["Repository", "https://github.com/Momo-1628/corda-rest-api-integration"],
], [4.0, 12.4])
body("In this project I built a permissioned-ledger application (a CorDapp) that records invoices between a seller and "
     "a buyer, and then a REST gateway in front of it. Any system that can send an HTTP request can use the ledger "
     "through this gateway: an ERP, a web dashboard, Postman or a shell script. They never have to understand Corda's "
     "RPC protocol, flows or vault queries.")

# =========================================================================== 2 PROBLEM
doc.add_heading("2. Problem Statement", 1)
body("Companies that trade with each other keep separate copies of the same invoice in separate ERP systems. The "
     "seller's system says an invoice is \"sent\", the buyer's system says it is \"under review\", and finance teams "
     "spend days reconciling the two. Disputes about amounts, approvals and payment status are common because there "
     "is no shared record that both sides trust.")
body("Corda solves the trust part: both companies can hold the same, signed, notarised invoice state, and a contract "
     "decides which changes are legal. But a CorDapp on its own is hard for ordinary business software to reach. A "
     "Corda node is driven through Corda RPC, a Java/Kotlin client library that speaks AMQP over Artemis. It needs the "
     "CorDapp classes on the client classpath and returns Corda-specific types such as SignedTransaction and "
     "StateAndRef. An ERP written in another language, a JavaScript front end, or a partner's integration platform "
     "cannot simply call it.")
rich([("Problem: ", True), ("design and implement a secure, well-documented, production-style REST API that exposes a "
     "Corda CorDapp's business operations as JSON endpoints. It must translate HTTP requests into Corda flows and "
     "vault queries, map ledger failures to meaningful HTTP status codes, and be proven to work from an external, "
     "non-Corda client.", False)])

# =========================================================================== 3 OBJECTIVES
doc.add_heading("3. Objectives", 1)
numbered([
    ("Model the business object on the ledger: ", "an InvoiceState (LinearState) with a four-status lifecycle "
     "(ISSUED, APPROVED, PAID, REJECTED) shared by seller and buyer."),
    ("Enforce the rules in a contract: ", "InvoiceContract with Issue, Approve, Pay and Reject commands, correct "
     "signers and unchangeable fields (invoiceNo, amount, parties)."),
    ("Implement the flows: ", "IssueInvoiceFlow (seller + buyer signatures through CollectSignaturesFlow) and the "
     "buyer-driven Approve/Pay/Reject flows, each with a responder and FinalityFlow."),
    ("Build the REST layer: ", "a Spring Boot 3 webserver per node that connects over CordaRPCOps and offers 11 JSON "
     "endpoints with an API key, validation, a global exception handler, a consistent response envelope, CORS, "
     "OpenAPI/Swagger UI and request logging."),
    ("Prove the integration from outside: ", "a Python ERP client, a Postman collection and curl scripts that run "
     "the full lifecycle and the error cases (401, 400, 422, 404) against live nodes."),
    ("Test at three levels: ", "contract tests (ledger DSL), flow tests (MockNetwork) and API tests (MockMvc with a "
     "mocked CordaRPCOps)."),
    ("Measure: ", "the end-to-end latency of 20 POST /api/invoices calls (average, min and max)."),
])

# =========================================================================== 4 INTRODUCTION
doc.add_heading("4. Introduction", 1)
body("Corda is an open-source distributed ledger platform from R3, designed for regulated business networks. Unlike "
     "public blockchains, Corda does not broadcast every transaction to every participant. Data is shared only "
     "between the parties to a deal, identities are known (X.500 names backed by certificates), and uniqueness is "
     "guaranteed by a notary service instead of mining. These properties make Corda a good fit for inter-company "
     "processes such as trade finance, invoicing and settlement.")
body("A CorDapp (Corda Distributed Application) has three main parts: states (the shared facts), contracts (the rules "
     "that every transaction must satisfy) and flows (the step-by-step protocol that builds, signs, notarises and "
     "distributes transactions). Clients start flows and read the vault through the node's RPC interface.")
body("Real enterprises, however, run SAP, Oracle, Tally, custom Java or .NET systems and modern web front ends, and "
     "they integrate through HTTP APIs. This project focuses on that integration boundary. I took the R3 Java "
     "template, replaced the sample IOU with an invoice CorDapp, and added a REST gateway (clients/webserver) designed "
     "the way a real integration layer would be: authenticated, validated, documented and observable. I then "
     "deployed a three-node network (Notary, SellerCorp in Mumbai, BuyerCorp in Bengaluru), ran one gateway per "
     "business node, and drove everything from a simulated external ERP written in Python.")

# =========================================================================== 5 CONCEPTS
doc.add_heading("5. Corda/Blockchain Concepts Used", 1)
table(["Concept", "How I used it in this project"], [
    ["LinearState & UniqueIdentifier", "InvoiceState is a LinearState. Every version of one invoice shares the same "
     "linearId, so the REST API can address an invoice as /api/invoices/{linearId} while the ledger keeps evolving it."],
    ["UTXO model (consume / create)", "Approve, Pay and Reject consume the current state and create a new one. Old "
     "versions become CONSUMED, which gives the /history endpoint a full audit trail for free."],
    ["Contract & commands", "InvoiceContract.verify() runs on every node for every transaction. Issue/Approve/Pay/"
     "Reject are TypeOnlyCommandData commands that carry the required signer keys."],
    ["Participants & signers", "Participants = seller + buyer (both store the state). Issue needs both signatures; "
     "the transitions need the buyer's signature only."],
    ["Flows, @InitiatingFlow, @StartableByRPC", "Each business action is a flow that the REST API starts with "
     "CordaRPCOps.startFlowDynamic(). Responder flows (@InitiatedBy) run on the counterparty."],
    ["CollectSignaturesFlow / SignTransactionFlow", "The seller collects the buyer's signature. The buyer's responder "
     "checks the proposal (it is the buyer, the counterparty is the seller) before signing."],
    ["Notary & FinalityFlow", "A non-validating notary prevents double-spends. FinalityFlow notarises the transaction "
     "and records it in both vaults (ReceiveFinalityFlow on the other side)."],
    ["Vault & vault queries", "The API reads with vaultQueryBy() using VaultQueryCriteria (UNCONSUMED) and "
     "LinearStateQueryCriteria (UNCONSUMED or ALL for history)."],
    ["Corda RPC (CordaRPCOps)", "The only channel between the REST layer and the node: nodeInfo, "
     "networkMapSnapshot, notaryIdentities, vaultQueryBy, startFlowDynamic, currentNodeTime."],
    ["Network bootstrapper (deployNodes)", "Cordform task that generates node folders, certificates, network "
     "parameters and RPC users for the three nodes."],
], [4.6, 11.8], caption="Corda concepts and where they appear in the project")

# =========================================================================== 6 ARCHITECTURE
doc.add_heading("6. System Architecture", 1)
body("The system has three layers (Figure 1). External systems only speak HTTP and JSON. The REST layer is a "
     "stateless Spring Boot 3 application. One instance is bound to each business node: the Seller API on port 10050 "
     "uses RPC port 10006 and the Buyer API on port 10060 uses RPC port 10009. The Corda layer holds the nodes, which "
     "talk to each other and to the notary over Corda's P2P messaging (AMQP over TLS).")
figure(P("docs", "diagrams", "architecture.png"), "System architecture - External ERP/Postman -> REST API (Spring Boot) -> RPC -> Corda nodes + Notary")
doc.add_heading("6.1 Layers inside the REST API", 2)
bullets([
    ("RequestLoggingFilter - ", "gives every call a request id (X-Request-Id header) and logs method, path, status and time."),
    ("ApiKeyFilter - ", "checks the X-API-KEY header (constant-time compare) on every /api/** path except /api/health "
     "and CORS pre-flight, and answers 401 in the standard envelope."),
    ("Controllers - ", "NodeController (me, peers, notaries, health) and InvoiceController (issue, list, get, approve, "
     "pay, reject, history), with Bean Validation and OpenAPI annotations."),
    ("InvoiceService - ", "the only class that talks to Corda. It resolves parties, queries the vault, starts flows, "
     "waits with a timeout and converts Corda types to DTOs."),
    ("GlobalExceptionHandler - ", "maps exceptions to 400 / 404 / 422 / 503 / 504 / 500 with clear messages."),
    ("NodeRPCConnection - ", "creates the CordaRPCOps bean from config.rpc.* properties (chosen by Spring profile or "
     "command-line arguments) and closes the connection on shutdown."),
])
doc.add_heading("6.2 Invoice lifecycle", 2)
figure(P("docs", "diagrams", "lifecycle.png"), "InvoiceState lifecycle enforced by InvoiceContract", 15.5)
doc.add_heading("6.3 Endpoint map", 2)
figure(P("docs", "diagrams", "endpoint_map.png"), "REST endpoint map with the Corda call behind each endpoint", 16.4)

# =========================================================================== 7 METHODOLOGY
doc.add_heading("7. Methodology", 1)
body("I followed an incremental, test-first approach. Each layer was built and tested before the next one was "
     "started, so any failure could be traced to one layer.")
numbered([
    ("Environment set-up: ", "I checked JDK 17 (Temurin 17.0.20), cloned corda/cordapp-template-java (already on "
     "Corda 4.12 with Gradle 7.6), removed the IOU sample and renamed the packages to com.cordarest."),
    ("Ledger design: ", "I wrote InvoiceState and the four commands, then 15 contract tests with the MockServices "
     "ledger DSL covering valid and invalid cases for every command."),
    ("Flow design: ", "I wrote IssueInvoiceFlow with CollectSignaturesFlow + FinalityFlow and a shared "
     "InvoiceTransitionFlow base class for Approve/Pay/Reject, then 6 MockNetwork tests (issue -> approve -> pay, "
     "issue -> reject and three negative cases)."),
    ("API contract first: ", "I fixed the endpoint list, request/response DTOs, the response envelope and the "
     "status-code policy before writing the controllers."),
    ("API implementation and tests: ", "I built the Spring Boot module and 21 MockMvc tests in which CordaRPCOps is a "
     "Mockito mock, so routing, security, validation and error mapping are tested without a running node."),
    ("Deployment: ", "I ran deployNodes for Notary, SellerCorp and BuyerCorp, started each node headless "
     "(java -jar corda.jar) in the background, waited for \"started up\", then started both webservers."),
    ("External validation: ", "I drove the live network with external_erp_client.py, curl (api_demo.sh) and Swagger "
     "UI, and recorded all outputs as evidence."),
    ("Measurement: ", "latency_benchmark.py timed 20 sequential POST /api/invoices calls after 2 warm-up calls. I "
     "also timed 20 GET calls for comparison."),
])
figure(P("docs", "diagrams", "sequence_issue.png"), "Sequence of POST /api/invoices -> RPC startFlow -> CollectSignatures -> Notary -> Vault -> JSON")
body("A practical problem came up during deployment. My C: drive was 96 % full, and the Artemis broker embedded "
     "in every Corda node blocks all producers once the disk holding its journal is more than 90 % full (AMQ222212 "
     "\"Disk Full! Blocking message production\"). The RPC calls hung even though the nodes reported \"started "
     "up\". I diagnosed this from the node logs and added a -NodesDir option to start_network.ps1 that copies the "
     "deployed nodes to another drive (D:) and runs them there. This is a good example of an operational issue that "
     "an integration layer must expect: /api/health and the 504/503 mappings exist for exactly this kind of situation.")

# =========================================================================== 8 IMPLEMENTATION
doc.add_heading("8. Implementation", 1)
table(["Module", "Main classes", "Lines (approx.)"], [
    ["contracts", "InvoiceState, InvoiceStatus, InvoiceContract", "260"],
    ["workflows", "IssueInvoiceFlow, InvoiceTransitionFlow, Approve/Pay/RejectInvoiceFlow", "300"],
    ["clients/webserver", "Starter, NodeRPCConnection, ApiKeyFilter, RequestLoggingFilter, WebConfig, OpenApiConfig, "
     "NodeController, InvoiceController, InvoiceService, GlobalExceptionHandler, 6 DTOs", "900"],
    ["tests", "InvoiceContractTests (15), InvoiceFlowTests (6), InvoiceApiTests (21)", "750"],
    ["external tools", "external_erp_client.py, latency_benchmark.py, api_demo.sh/.ps1, Postman collection", "500"],
], [3.2, 10.6, 2.6], caption="Code organisation")
doc.add_heading("8.1 State - InvoiceState", 2)
code('''@BelongsToContract(InvoiceContract.class)
public class InvoiceState implements LinearState {
    private final UniqueIdentifier linearId;
    private final String invoiceNo;
    private final Party seller, buyer;
    private final BigDecimal amount;
    private final String currency, description;
    private final LocalDate dueDate;
    private final InvoiceStatus status;      // ISSUED, APPROVED, PAID, REJECTED
    private final String remarks;

    /** Copy with a new status - everything else stays the same. */
    public InvoiceState withStatus(InvoiceStatus newStatus, String newRemarks) {
        return new InvoiceState(linearId, invoiceNo, seller, buyer, amount, currency,
                                description, dueDate, newStatus, newRemarks);
    }
    @Override public List<AbstractParty> getParticipants() { return Arrays.asList(seller, buyer); }
}''', "Listing 1: InvoiceState (abridged)")
doc.add_heading("8.2 Contract - InvoiceContract", 2)
code('''public void verify(LedgerTransaction tx) {
    CommandWithParties<Commands> cmd = requireSingleCommand(tx.getCommands(), Commands.class);
    if (cmd.getValue() instanceof Commands.Issue)        verifyIssue(tx, cmd.getSigners());
    else if (cmd.getValue() instanceof Commands.Approve) verifyTransition(tx, signers, ISSUED,   APPROVED, "Approve");
    else if (cmd.getValue() instanceof Commands.Pay)     verifyTransition(tx, signers, APPROVED, PAID,     "Pay");
    else if (cmd.getValue() instanceof Commands.Reject)  verifyTransition(tx, signers, ISSUED,   REJECTED, "Reject");
}
private void verifyIssue(LedgerTransaction tx, List<PublicKey> signers) {
    requireThat(req -> {
        req.using("Issue: no input states should be consumed.", tx.getInputs().isEmpty());
        InvoiceState out = tx.outputsOfType(InvoiceState.class).get(0);
        req.using("Issue: the amount must be greater than zero.", out.getAmount().signum() > 0);
        req.using("Issue: the seller and the buyer must be different parties.", !out.getSeller().equals(out.getBuyer()));
        req.using("Issue: the seller must sign.", signers.contains(out.getSeller().getOwningKey()));
        req.using("Issue: the buyer must sign.",  signers.contains(out.getBuyer().getOwningKey()));
        return null;
    });
}
// verifyTransition: 1 in / 1 out, status from -> to, linearId, invoiceNo, amount, currency
// and parties unchanged, buyer must sign.''', "Listing 2: InvoiceContract.verify (abridged)")
doc.add_heading("8.3 Flow - IssueInvoiceFlow", 2)
code('''@InitiatingFlow @StartableByRPC
public class IssueInvoiceFlow extends FlowLogic<SignedTransaction> {
    @Suspendable @Override
    public SignedTransaction call() throws FlowException {
        Party seller = getOurIdentity();
        Party notary = getServiceHub().getNetworkMapCache().getNotaryIdentities().get(0);
        InvoiceState output = new InvoiceState(invoiceNo, seller, buyer, amount, currency, description, dueDate);
        TransactionBuilder builder = new TransactionBuilder(notary)
            .addOutputState(output, InvoiceContract.ID)
            .addCommand(new InvoiceContract.Commands.Issue(),
                        Arrays.asList(seller.getOwningKey(), buyer.getOwningKey()));
        builder.verify(getServiceHub());                                   // contract check
        SignedTransaction partSigned = getServiceHub().signInitialTransaction(builder);
        FlowSession buyerSession = initiateFlow(buyer);
        SignedTransaction fullySigned = subFlow(new CollectSignaturesFlow(partSigned, List.of(buyerSession)));
        return subFlow(new FinalityFlow(fullySigned, List.of(buyerSession)));   // notarise + record
    }
    @InitiatedBy(IssueInvoiceFlow.class)
    public static class Responder extends FlowLogic<SignedTransaction> {
        // SignTransactionFlow.checkTransaction(): output is an InvoiceState, I am the buyer,
        // the counterparty is the seller -> sign; then ReceiveFinalityFlow records it.
    }
}''', "Listing 3: IssueInvoiceFlow (abridged)")
body("ApproveInvoiceFlow, PayInvoiceFlow and RejectInvoiceFlow extend one base class, InvoiceTransitionFlow. It finds "
     "the unconsumed state by linearId, checks that the caller is the buyer and that the current status is the "
     "required one (which gives a clear error such as \"must be APPROVED to move to PAID\"), builds a one-input, "
     "one-output transaction signed by the buyer, and finalises it with the seller.")
doc.add_heading("8.4 REST controller and service", 2)
code('''@RestController @RequestMapping("/api/invoices")
public class InvoiceController {
    @PostMapping
    public ResponseEntity<ApiResponse<TransactionResult>> issue(@Valid @RequestBody CreateInvoiceRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.ok(service.issue(request)));
    }
    @PutMapping("/{linearId}/pay")
    public ApiResponse<TransactionResult> pay(@PathVariable String linearId,
                                              @Valid @RequestBody(required = false) RemarksRequest body) {
        return ApiResponse.ok(service.pay(linearId, remarks(body)));
    }
}
// InvoiceService - the only place that touches Corda
private SignedTransaction runFlow(Class<? extends FlowLogic<SignedTransaction>> flow, Object... args) {
    try {
        return rpc.startFlowDynamic(flow, args).getReturnValue().get(timeoutSeconds, TimeUnit.SECONDS);
    } catch (ExecutionException e) {                      // flow or contract rejected -> HTTP 422
        throw new FlowFailedException(cleanMessage(e.getCause()), e.getCause());
    } catch (TimeoutException e) {                        // -> HTTP 504
        throw new FlowTimeoutException(flow.getSimpleName() + " did not finish within " + timeoutSeconds + " s");
    }
}''', "Listing 4: InvoiceController and InvoiceService.runFlow (abridged)")
doc.add_heading("8.5 Security, validation and error handling", 2)
table(["Concern", "Implementation", "Result"], [
    ["Authentication", "ApiKeyFilter, X-API-KEY from application-<profile>.properties, MessageDigest.isEqual", "401 UNAUTHORIZED"],
    ["Validation", "Bean Validation on CreateInvoiceRequest: @NotBlank, @DecimalMin(0.01), @Pattern [A-Z]{3}, @FutureOrPresent, @Size", "400 VALIDATION_FAILED + details[]"],
    ["Bad input", "invalid UUID, unknown buyer, bad status filter, malformed JSON", "400 BAD_REQUEST / MALFORMED_JSON"],
    ["Unknown invoice", "vault query returns nothing for the linearId", "404 INVOICE_NOT_FOUND"],
    ["Ledger rejection", "FlowException / TransactionVerificationException from the flow", "422 FLOW_FAILED"],
    ["Node problems", "RPCException / flow timeout", "503 NODE_UNAVAILABLE / 504 FLOW_TIMEOUT"],
    ["Cross-origin", "WebMvcConfigurer CORS on /api/** (GET, POST, PUT, OPTIONS)", "browser clients allowed"],
    ["Documentation", "springdoc-openapi 2.5: /v3/api-docs and /swagger-ui.html with ApiKey scheme", "self-describing API"],
], [3.0, 9.0, 4.4], caption="Production-style concerns in the REST layer")

# =========================================================================== 9 RESULTS
doc.add_heading("9. Results", 1)
doc.add_heading("9.1 Automated tests", 2)
table(["Test suite", "Technique", "Tests", "Passed"], [
    ["InvoiceContractTests", "MockServices ledger DSL (valid + invalid cases for every command)", "15", "15"],
    ["InvoiceFlowTests", "MockNetwork with Notary, SellerCorp, BuyerCorp", "6", "6"],
    ["InvoiceApiTests", "Spring MockMvc + Mockito mock of CordaRPCOps", "21", "21"],
    ["Total", "gradlew test --rerun-tasks: BUILD SUCCESSFUL", "42", "42"],
], [4.2, 8.4, 1.8, 2.0], caption="Test results (evidence/test_results.txt)")
doc.add_heading("9.2 Live run with the external ERP client", 2)
body("With the three nodes and both APIs running, external_erp_client.py acted as two ERP systems (seller side and "
     "buyer side). Every one of its checks passed:")
table(["Step", "Call", "HTTP", "Outcome"], [
    ["Connectivity", "GET /api/health, /api/me, /api/peers, /api/notaries", "200", "both APIs UP, correct identities"],
    ["Issue x3", "POST /api/invoices on the Seller API", "201", "3 invoices, txHash + linearId returned"],
    ["Buyer view", "GET /api/invoices?status=ISSUED on the Buyer API", "200", "same 3 invoices in BuyerCorp's vault"],
    ["Approve + pay A", "PUT /approve then /pay", "200", "A: ISSUED -> APPROVED -> PAID"],
    ["Approve B", "PUT /approve", "200", "B: APPROVED (payment pending)"],
    ["Wrong key", "GET /api/invoices with a wrong X-API-KEY", "401", "UNAUTHORIZED: Invalid API key"],
    ["Invalid amount", "POST with amount -500", "400", "amount: amount must be greater than 0"],
    ["Pay too early", "PUT /pay on ISSUED invoice C", "422", "must be APPROVED to move to PAID"],
    ["Unknown id", "GET /api/invoices/{random UUID}", "404", "INVOICE_NOT_FOUND"],
    ["Reject C", "PUT /reject", "200", "C: REJECTED"],
    ["History A", "GET /history", "200", "ISSUED (consumed) -> APPROVED (consumed) -> PAID"],
    ["Consistency", "GET /api/invoices on both APIs", "200", "Seller and Buyer vaults identical"],
], [2.8, 6.4, 1.3, 5.9], caption="External ERP client run (evidence/erp_client_run.txt)", font=9)
body("The curl walk-through (scripts/api_demo.sh) and the Postman collection repeat the same lifecycle, and the "
     "request log of each API shows every call with its status and duration.")

# =========================================================================== 10 SCREENSHOTS
doc.add_heading("10. Screenshots", 1)
body("The images below are taken from the actual runs. Larger versions are in the evidence/ folder of the repository.")
figure_pair((P("evidence", "images", "test_results.png"), "gradlew test - 42 tests passed"),
            (P("evidence", "images", "node_startup.png"), "Notary, SellerCorp and BuyerCorp started headless"))
figure_pair((P("evidence", "images", "erp_client_run_1.png"), "ERP client - connectivity, issue, approve, pay"),
            (P("evidence", "images", "erp_client_run_2.png"), "ERP client - errors, audit trail, both vaults"))
figure_pair((P("evidence", "screenshots", "swagger_ui_top.png"), "Swagger UI generated by springdoc (Seller API)"),
            (P("evidence", "screenshots", "swagger_execute_crop.png"), "Swagger UI - executing GET /api/invoices"))
figure_pair((P("evidence", "screenshots", "browser_get_invoices_json_crop.png"), "Browser - JSON of GET /api/invoices?status=PAID"),
            (P("evidence", "images", "curl_errors.png"), "curl - 401, 400, 422 and 404 error envelopes"))

# =========================================================================== 11 ANALYSIS
doc.add_heading("11. Analysis", 1)
doc.add_heading("11.1 API latency", 2)
body("I timed 20 sequential POST /api/invoices calls against the Seller API, after two warm-up calls that were not "
     "counted. Each call is the complete write path: HTTP and validation, RPC to the node, transaction building and "
     "contract verification, seller signature, the buyer's signature over P2P, notarisation, recording in both "
     "vaults and the JSON response. For comparison I also timed 20 GET /api/invoices calls (a vault query only).")
table(["Metric", "POST /api/invoices (write, full flow)", "GET /api/invoices (read)"], [
    ["Calls measured", str(LS["calls"]), str(LG["calls"])],
    ["Average", f"{LS['average_ms']:.1f} ms", f"{LG['average_ms']:.1f} ms"],
    ["Minimum", f"{LS['min_ms']:.1f} ms", f"{LG['min_ms']:.1f} ms"],
    ["Maximum", f"{LS['max_ms']:.1f} ms", f"{LG['max_ms']:.1f} ms"],
    ["Median", f"{LS['median_ms']:.1f} ms", "-"],
    ["90th percentile", f"{LS['p90_ms']:.1f} ms", "-"],
    ["Standard deviation", f"{LS['stdev_ms']:.1f} ms", "-"],
    ["Sequential throughput", f"{LS['throughput_tx_per_s']:.2f} tx/s", "-"],
], [4.4, 6.4, 5.6], caption="Latency of 20 calls (local 3-node network on one laptop, JDK 17)")
figure(P("docs", "diagrams", "latency_chart.png"), "Per-call latency of the 20 POST /api/invoices calls", 16.0)
body(f"The average write took about {LS['average_ms']:.0f} ms, and calls ranged from {LS['min_ms']:.0f} ms to "
     f"{LS['max_ms']:.0f} ms. A read took about {LG['average_ms']:.0f} ms on average, roughly "
     f"{LS['average_ms'] / LG['average_ms']:.0f} times faster. So the REST layer itself adds very little. Almost "
     "all of the write time is spent in Corda's consensus steps: two signatures, a network round trip to the "
     "counterparty, notarisation and checkpointing of the flow. The very first call of a fresh API took about 8.4 s "
     "(class loading, JIT and opening the P2P sessions), which is why I excluded warm-up calls from the statistics. "
     "The spread (standard deviation of about 100 ms) comes from JVM garbage collection and from all five JVMs "
     "sharing one laptop with only about 2 GB of free memory.")
doc.add_heading("11.2 Design analysis", 2)
bullets([
    ("Correctness is enforced twice. ", "The flow checks the status before building the transaction, so the client "
     "gets a readable 422 message. The contract re-checks the same rules on every node, so a modified client or flow "
     "still cannot break them."),
    ("Errors carry meaning. ", "Mapping ledger failures to 422 (not 500) tells the ERP that its request was understood "
     "but rejected by business rules, so it should not retry. 503 and 504 tell it that retrying later may help."),
    ("Writes are synchronous. ", "The API waits for finality before answering. That makes the response trustworthy "
     "(the txHash is final), but a client thread is held for about 0.6 s. Webhooks or events would remove that wait."),
    ("Horizontal scaling. ", "The API is stateless, so several instances could share one node. The real limit is "
     "the node's flow throughput and the notary."),
])

# =========================================================================== 12 ADV / LIMITS
doc.add_heading("12. Advantages and Limitations", 1)
doc.add_heading("12.1 Advantages", 2)
bullets([
    "Any language or tool that speaks HTTP (ERP, web front end, Postman, curl, Python) can use the ledger. No Corda "
    "libraries are needed on the client side.",
    "A single, documented contract: OpenAPI/Swagger UI, one response envelope and clear status codes make "
    "integration fast and predictable.",
    "Security and validation at the edge: bad requests are rejected before they reach the node, saving flow resources.",
    "The ledger guarantees stay intact: two-party signatures, notarisation and contract rules still apply, and both "
    "companies' vaults stay identical.",
    "A complete audit trail through /history, built from consumed states, without any extra database.",
    "Well tested: 42 automated tests at three levels, plus a reproducible live demo and benchmark.",
])
doc.add_heading("12.2 Limitations", 2)
bullets([
    "A shared API key per node is coarse. There is no per-user identity, role-based access or key rotation yet.",
    "Write calls block until finality (about 0.6 s each). There is no asynchronous mode or push notification.",
    "List endpoints return up to 500 states without pagination parameters, and the status filter runs in memory.",
    "One RPC connection per API instance, with no automatic reconnect or circuit breaker if the node restarts.",
    "Measured on a single laptop with H2 databases and dev-mode certificates, so the numbers are not production figures.",
    "HTTP is used without TLS in the demo. In production the API must sit behind HTTPS.",
])

# =========================================================================== 13 CONCLUSION
doc.add_heading("13. Conclusion", 1)
body("I designed and implemented a complete external REST API integration for a Corda 4.12 CorDapp. On the ledger "
     "side, an InvoiceState with a strict four-status lifecycle is protected by InvoiceContract and driven by four "
     "flows that use CollectSignaturesFlow, a notary and FinalityFlow. On the integration side, a Spring Boot 3 "
     "gateway per node turns eleven JSON endpoints into RPC flow starts and vault queries. It adds API-key "
     "authentication, request validation, a consistent response envelope, meaningful status codes, CORS, "
     "Swagger UI and request logging.")
body("All 42 automated tests pass. On a live three-node network, a Python program acting as an outside ERP issued, "
     "approved, paid and rejected invoices, triggered every error path (401, 400, 422, 404), and confirmed that both "
     "companies' vaults agree. A write that goes through the whole consensus process takes about 0.58 s through the "
     "API, and a read takes about 0.08 s.")
body("The main lesson for me is that the value of a CorDapp in a real company depends on how easily other systems "
     "can reach it. A thin, well-behaved REST layer keeps all of Corda's guarantees and makes them usable by "
     "ordinary business software. As future scope, I would replace the API key with OAuth2/JWT, push ledger events "
     "to clients through webhooks or Kafka (from vaultTrack), add idempotency keys and pagination, and package the "
     "whole network with Docker Compose.")

# =========================================================================== 14 REFERENCES
doc.add_heading("14. References", 1)
refs = [
    "R3, \"Corda 4.12 Community Edition documentation\" - https://docs.r3.com/en/platform/corda/4.12/community.html",
    "R3, \"Writing CorDapp flows\" and \"API: Vault Query\", Corda 4.12 documentation - https://docs.r3.com/",
    "R3, \"CorDapp template - Java\" (cordapp-template-java), GitHub - https://github.com/corda/cordapp-template-java",
    "R3, \"Corda RPC client (CordaRPCClient / CordaRPCOps)\", Corda 4.12 API reference - https://docs.r3.com/",
    "VMware/Broadcom, \"Spring Boot 3.2 Reference Documentation\" - https://docs.spring.io/spring-boot/",
    "Spring, \"Spring Framework - Web MVC, CORS and Testing (MockMvc)\" - https://docs.spring.io/spring-framework/reference/",
    "springdoc-openapi project, \"springdoc-openapi v2 documentation\" - https://springdoc.org/",
    "Jakarta EE, \"Jakarta Bean Validation 3.0 specification\" - https://jakarta.ee/specifications/bean-validation/",
    "Apache ActiveMQ Artemis, \"Paging and max-disk-usage\" documentation - https://activemq.apache.org/components/artemis/documentation/",
    "M. Hearn and R. G. Brown, \"Corda: A Distributed Ledger\", R3 technical white paper, 2019.",
]
numbered(refs, "[{}]", justify=False)

doc.save(OUT)
print("saved", OUT)
