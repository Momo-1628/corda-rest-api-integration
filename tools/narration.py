"""Speaker-notes narration (first person singular), one entry per slide. Used by make_ppt.py."""
NOTES = [
    # 1 Title
    "Hello, I am Suraj Patel, USN 24BTRBT029, from B.Tech Computer Science with specialisation in Blockchain "
    "Technology, Semester five, at Jain University. My Corda Development mini project is topic twenty five: "
    "Implementation of an External REST API Integration with a Corda CorDapp. I built an invoice application on "
    "Corda 4.12 and put a Spring Boot REST API in front of it, so outside systems like an ERP or a web app can use "
    "the ledger with simple JSON calls.",
    # 2 Problem
    "When two companies trade, the seller and the buyer each keep their own copy of the same invoice in separate ERP "
    "systems. These copies drift apart, and finance teams waste days reconciling them. Corda fixes this with one "
    "shared, signed and notarised invoice. But a Corda node is only reachable through Corda RPC, which needs Java "
    "libraries and Corda classes on the client. So my problem was to build a secure REST bridge that normal "
    "business software can call.",
    # 3 Objectives
    "I set five objectives. First, model the invoice as a linear state with four statuses: issued, approved, paid "
    "and rejected. Second, enforce the rules in a contract and four flows. Third, the core of the topic, build a "
    "production style REST API with authentication, validation and clear error codes. Fourth, prove it works from "
    "outside, using a Python ERP client, Postman and curl. And fifth, test everything automatically and measure "
    "the API latency.",
    # 4 Why REST
    "Why REST in front of Corda? Corda RPC is designed for Java and Kotlin clients. It needs the RPC library and the "
    "CorDapp classes, it talks AMQP, and it returns Corda specific types. A browser cannot use it, and an SAP or "
    "dot net system cannot easily use it either. REST works from any language, JSON is universal, and Swagger "
    "documents the contract. So I kept RPC inside the trusted server and exposed only REST to the outside world.",
    # 5 Concepts
    "These are the Corda concepts I used. The invoice is a LinearState, so every version keeps the same linear ID, "
    "which the API uses in its URLs. Following the UTXO model, each approve, pay or reject consumes the old state "
    "and creates a new one, which gives a free audit trail. The contract runs on every node, flows collect "
    "signatures, a notary prevents double spends, and RPC is the only door into the vault.",
    # 6 Architecture
    "Here is the architecture. On the left are the external systems: my Python ERP client, Postman or curl, and web "
    "dashboards. They only speak HTTP and JSON. In the middle, I run one Spring Boot instance per node, the Seller "
    "API on port 10050 and the Buyer API on port 10060. Each request passes logging and API key filters, the "
    "controller and the service, which calls the node through CordaRPCOps. On the right, the nodes talk peer to peer.",
    # 7 State & contract
    "This is the ledger design. The InvoiceState holds the linear ID, invoice number, seller and buyer, amount, "
    "currency, description, due date, status and remarks, and both companies are participants. Issue needs an "
    "amount above zero, different parties and both signatures. Approve, pay and reject need only the buyer's "
    "signature and must follow the lifecycle on the right. On every transition, the invoice number, amount and "
    "parties can never change.",
    # 8 Flow design
    "This sequence shows a new invoice. The API checks the key and validates the body, then calls startFlowDynamic "
    "on the seller node. IssueInvoiceFlow builds the transaction, verifies the contract and signs it. Through "
    "CollectSignaturesFlow, the buyer checks the proposal and signs too. FinalityFlow gets the notary signature and "
    "records the transaction in both vaults. The API then returns 201 with the transaction hash. Approve, pay and "
    "reject share one buyer side flow.",
    # 9 API design
    "The API has eleven endpoints. Four describe the node: me, peers, notaries and a public health check. POST on "
    "the invoices path issues an invoice and returns 201. GET lists invoices, optionally filtered by status, or "
    "fetches one by linear ID. PUT approve, pay and reject start the matching flows on the buyer node, and history "
    "returns every version. Every response uses one envelope: success, data, error and timestamp.",
    # 10 Security
    "Because this API is the front door to a ledger, I added production style protection. Every call except health "
    "needs an X-API-KEY header, otherwise the answer is 401. Bean validation rejects a negative amount or a wrong "
    "currency with 400 and a clear list of problems. A global handler maps an unknown linear ID to 404, and a flow "
    "or contract rejection to 422. I also enabled CORS and request logging.",
    # 11 Tech stack
    "My tech stack is Corda 4.12 Community Edition on Java 17, starting from the official R3 Java template and built "
    "with Gradle 7.6. The REST layer uses Spring Boot 3.2 with Spring Web, Bean Validation and springdoc for "
    "Swagger. For testing I used the Corda ledger DSL, MockNetwork, and Spring MockMvc with Mockito. The ERP "
    "simulation is written in Python with requests, and I also provide Postman and curl scripts.",
    # 12 Tests
    "Now the results. I wrote forty two automated tests, and all of them pass. Fifteen contract tests use the ledger "
    "DSL to cover valid and invalid cases, like a zero amount, a missing buyer signature or a changed amount. Six "
    "flow tests run on an in memory network with a notary and both companies. And twenty one API tests use MockMvc "
    "with a mocked CordaRPCOps to check routing, security, validation and error mapping.",
    # 13 Live demo
    "For the live demo, I deployed the notary, SellerCorp and BuyerCorp, started them headless, and started both "
    "APIs. On the left is the Swagger UI for the seller API. On the right, my ERP client has issued three invoices, "
    "approved and paid one, approved another and rejected the third. It also showed every error case: 401, 400, "
    "422 and 404. Finally, both vaults held exactly the same invoices.",
    # 14 Performance
    "For performance, I timed twenty POST calls to the invoices endpoint after two warm up calls. Each call runs the "
    "whole flow, including the buyer signature and notarisation. The average was 583 milliseconds, the fastest 391 "
    "and the slowest 766. A simple read took only about 78 milliseconds. So the REST layer adds very little; almost "
    "all the write time is Corda consensus. Everything ran on one laptop.",
    # 15 Advantages & limitations
    "The big advantage is reach: any system that can send HTTP can now use the ledger, without Corda libraries. The "
    "API is documented, validated and secured at the edge, and the ledger guarantees stay intact. On the other "
    "hand, one shared API key per node is coarse, write calls wait about half a second for finality, list "
    "endpoints have no pagination yet, and I measured on a single laptop.",
    # 16 Conclusion
    "To conclude, I built a complete REST integration for a Corda CorDapp. A contract and four flows protect the "
    "invoice lifecycle, and a Spring Boot gateway turns eleven JSON endpoints into flows and vault queries. All "
    "forty two tests pass, and a Python ERP ran the full lifecycle on a live network. In future, I would add OAuth2, "
    "webhooks or Kafka events, idempotency keys, pagination and Docker Compose.",
    # 17 Thank you
    "That brings me to the end. All the code, tests, evidence and the Postman collection are in my public GitHub "
    "repository, corda rest api integration, under the account Momo-1628. My main references were the Corda 4.12 "
    "documentation, the R3 CorDapp template, the Spring Boot reference and springdoc. Thank you very much for "
    "watching. I am Suraj Patel, USN 24BTRBT029, and I am happy to answer any questions.",
]
