package com.cordarest.webserver;

import com.cordarest.contracts.InvoiceContract;
import com.cordarest.flows.ApproveInvoiceFlow;
import com.cordarest.flows.IssueInvoiceFlow;
import com.cordarest.flows.PayInvoiceFlow;
import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.concurrent.CordaFuture;
import net.corda.core.contracts.StateAndRef;
import net.corda.core.contracts.StateRef;
import net.corda.core.contracts.TransactionState;
import net.corda.core.crypto.Crypto;
import net.corda.core.crypto.SecureHash;
import net.corda.core.flows.FlowException;
import net.corda.core.identity.CordaX500Name;
import net.corda.core.identity.Party;
import net.corda.core.messaging.CordaRPCOps;
import net.corda.core.messaging.FlowHandle;
import net.corda.core.node.NodeInfo;
import net.corda.core.node.services.Vault;
import net.corda.core.node.services.vault.PageSpecification;
import net.corda.core.node.services.vault.QueryCriteria;
import net.corda.core.node.services.vault.Sort;
import net.corda.core.transactions.SignedTransaction;
import net.corda.core.transactions.WireTransaction;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * API tests for the REST layer. The Corda node is replaced by a Mockito mock of CordaRPCOps,
 * so these tests check routing, JSON, API-key security, validation and error mapping in isolation.
 */
@SpringBootTest(properties = {"api.security.key=test-key", "config.rpc.port=1"})
@AutoConfigureMockMvc
class InvoiceApiTests {

    private static final String KEY = "test-key";

    @Autowired private MockMvc mvc;
    @MockBean private CordaRPCOps rpc;

    private final Party seller = party("O=SellerCorp,L=Mumbai,C=IN");
    private final Party buyer = party("O=BuyerCorp,L=Bengaluru,C=IN");
    private final Party notary = party("O=Notary,L=London,C=GB");
    private InvoiceState invoice;

    private static Party party(String name) {
        return new Party(CordaX500Name.parse(name), Crypto.generateKeyPair().getPublic());
    }

    @BeforeEach
    void setUp() {
        invoice = new InvoiceState("INV-001", seller, buyer, new BigDecimal("1500.00"), "INR",
                "Steel rods", LocalDate.of(2026, 12, 31));
        NodeInfo info = mock(NodeInfo.class);
        when(info.getLegalIdentities()).thenReturn(List.of(seller));
        when(info.getPlatformVersion()).thenReturn(12);
        when(rpc.nodeInfo()).thenReturn(info);
        when(rpc.currentNodeTime()).thenReturn(Instant.parse("2026-11-18T10:00:00Z"));
        when(rpc.wellKnownPartyFromX500Name(buyer.getName())).thenReturn(buyer);
        when(rpc.partiesFromName("BuyerCorp", false)).thenReturn(Set.of(buyer));
        when(rpc.notaryIdentities()).thenReturn(List.of(notary));
        NodeInfo buyerInfo = mock(NodeInfo.class);
        when(buyerInfo.getLegalIdentities()).thenReturn(List.of(buyer));
        NodeInfo notaryInfo = mock(NodeInfo.class);
        when(notaryInfo.getLegalIdentities()).thenReturn(List.of(notary));
        when(rpc.networkMapSnapshot()).thenReturn(List.of(info, buyerInfo, notaryInfo));
        vaultReturns(List.of(invoice));
    }

    @SuppressWarnings("unchecked")
    private void vaultReturns(List<InvoiceState> states) {
        List<StateAndRef<InvoiceState>> refs = states.stream()
                .map(s -> new StateAndRef<>(new TransactionState<>(s, InvoiceContract.ID, notary),
                        new StateRef(SecureHash.randomSHA256(), 0)))
                .toList();
        Vault.Page<InvoiceState> page = mock(Vault.Page.class);
        when(page.getStates()).thenReturn(refs);
        List<Vault.StateMetadata> metas = states.stream().map(s -> {
            Vault.StateMetadata m = mock(Vault.StateMetadata.class);
            when(m.getStatus()).thenReturn(s.getStatus() == InvoiceStatus.ISSUED && states.size() > 1
                    ? Vault.StateStatus.CONSUMED : Vault.StateStatus.UNCONSUMED);
            when(m.getRecordedTime()).thenReturn(Instant.parse("2026-11-18T10:00:00Z").plusSeconds(s.getStatus().ordinal()));
            return m;
        }).toList();
        when(page.getStatesMetadata()).thenReturn(metas);
        when(rpc.vaultQueryBy(any(QueryCriteria.class), any(PageSpecification.class), any(Sort.class), eq(InvoiceState.class)))
                .thenReturn(page);
    }

    @SuppressWarnings("unchecked")
    private void flowReturns(Class<?> flowClass, InvoiceState output) throws Exception {
        SignedTransaction stx = mock(SignedTransaction.class);
        WireTransaction wtx = mock(WireTransaction.class);
        when(stx.getId()).thenReturn(SecureHash.parse("A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F60718293A4B5C6D7E8F90"));
        when(stx.getTx()).thenReturn(wtx);
        when(wtx.outputsOfType(InvoiceState.class)).thenReturn(List.of(output));
        CordaFuture<SignedTransaction> future = mock(CordaFuture.class);
        when(future.get(anyLong(), any(TimeUnit.class))).thenReturn(stx);
        FlowHandle<SignedTransaction> handle = mock(FlowHandle.class);
        when(handle.getReturnValue()).thenReturn(future);
        doReturn(handle).when(rpc).startFlowDynamic(eq((Class) flowClass), any(Object[].class));
    }

    @SuppressWarnings("unchecked")
    private void flowFails(Class<?> flowClass, Exception cause) throws Exception {
        CordaFuture<SignedTransaction> future = mock(CordaFuture.class);
        when(future.get(anyLong(), any(TimeUnit.class))).thenThrow(new ExecutionException(cause));
        FlowHandle<SignedTransaction> handle = mock(FlowHandle.class);
        when(handle.getReturnValue()).thenReturn(future);
        doReturn(handle).when(rpc).startFlowDynamic(eq((Class) flowClass), any(Object[].class));
    }

    private String id() { return invoice.getLinearId().getId().toString(); }

    private static final String VALID_BODY = """
            {"invoiceNo":"INV-001","buyer":"O=BuyerCorp,L=Bengaluru,C=IN","amount":1500.00,
             "currency":"INR","description":"Steel rods","dueDate":"2099-12-31"}""";

    // ------------------------------------------------------------- security

    @Test @DisplayName("GET /api/health is public and reports UP")
    void healthIsPublic() throws Exception {
        mvc.perform(get("/api/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.status").value("UP"))
                .andExpect(jsonPath("$.timestamp").exists());
    }

    @Test @DisplayName("Missing X-API-KEY -> 401 with envelope")
    void missingKeyIs401() throws Exception {
        mvc.perform(get("/api/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.error.code").value("UNAUTHORIZED"))
                .andExpect(jsonPath("$.error.message").value(containsString("Missing")));
    }

    @Test @DisplayName("Wrong X-API-KEY -> 401")
    void wrongKeyIs401() throws Exception {
        mvc.perform(get("/api/invoices").header("X-API-KEY", "nope"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error.message").value("Invalid API key"));
        verify(rpc, never()).vaultQueryBy(any(QueryCriteria.class), any(PageSpecification.class), any(Sort.class), eq(InvoiceState.class));
    }

    @Test @DisplayName("CORS pre-flight is allowed without a key")
    void corsPreflight() throws Exception {
        mvc.perform(options("/api/invoices").header("Origin", "http://erp.example.com")
                        .header("Access-Control-Request-Method", "POST"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", "http://erp.example.com"));
    }

    // ---------------------------------------------------------- node info

    @Test @DisplayName("GET /api/me, /api/peers, /api/notaries")
    void nodeEndpoints() throws Exception {
        mvc.perform(get("/api/me").header("X-API-KEY", KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.name").value("O=SellerCorp, L=Mumbai, C=IN"))
                .andExpect(jsonPath("$.data.organisation").value("SellerCorp"));
        mvc.perform(get("/api/peers").header("X-API-KEY", KEY))
                .andExpect(jsonPath("$.data.peers", hasSize(1)))
                .andExpect(jsonPath("$.data.peers[0]").value("O=BuyerCorp, L=Bengaluru, C=IN"));
        mvc.perform(get("/api/notaries").header("X-API-KEY", KEY))
                .andExpect(jsonPath("$.data.notaries[0]").value("O=Notary, L=London, C=GB"));
    }

    // ------------------------------------------------------------- issue

    @Test @DisplayName("POST /api/invoices -> 201 with txHash and linearId")
    void issueInvoice() throws Exception {
        flowReturns(IssueInvoiceFlow.class, invoice);
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.txHash").value(org.hamcrest.Matchers.startsWith("A1B2C3")))
                .andExpect(jsonPath("$.data.linearId").value(id()))
                .andExpect(jsonPath("$.data.invoice.status").value("ISSUED"))
                .andExpect(jsonPath("$.error").value(nullValue()));
        verify(rpc).startFlowDynamic(eq(IssueInvoiceFlow.class), any(Object[].class));
    }

    @Test @DisplayName("POST with amount <= 0 -> 400 with field message")
    void invalidAmountIs400() throws Exception {
        String body = VALID_BODY.replace("1500.00", "-5");
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.error.details", hasItem("amount: amount must be greater than 0")));
        verify(rpc, never()).startFlowDynamic(any(), any(Object[].class));
    }

    @Test @DisplayName("POST with several missing/invalid fields -> 400 listing all of them")
    void manyValidationErrors() throws Exception {
        String body = "{\"invoiceNo\":\"\",\"buyer\":\"BuyerCorp\",\"amount\":10,\"currency\":\"rupees\"}";
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.details", hasSize(3)))
                .andExpect(jsonPath("$.error.details", hasItem(containsString("currency"))))
                .andExpect(jsonPath("$.error.details", hasItem(containsString("dueDate"))))
                .andExpect(jsonPath("$.error.details", hasItem(containsString("invoiceNo"))));
    }

    @Test @DisplayName("POST with malformed JSON -> 400")
    void malformedJson() throws Exception {
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content("{not json"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("MALFORMED_JSON"));
    }

    @Test @DisplayName("POST with an unknown buyer -> 400")
    void unknownBuyer() throws Exception {
        String body = VALID_BODY.replace("O=BuyerCorp,L=Bengaluru,C=IN", "O=Ghost,L=Pune,C=IN");
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.message").value(containsString("not known")));
    }

    @Test @DisplayName("Buyer given as organisation name only is resolved")
    void buyerByOrganisationName() throws Exception {
        flowReturns(IssueInvoiceFlow.class, invoice);
        String body = VALID_BODY.replace("O=BuyerCorp,L=Bengaluru,C=IN", "BuyerCorp");
        mvc.perform(post("/api/invoices").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isCreated());
    }

    // -------------------------------------------------------------- reads

    @Test @DisplayName("GET /api/invoices?status= filters")
    void listWithFilter() throws Exception {
        InvoiceState approved = new InvoiceState("INV-002", seller, buyer, new BigDecimal("99"), "INR", "x",
                LocalDate.of(2026, 12, 31)).withStatus(InvoiceStatus.APPROVED, null);
        vaultReturns(List.of(invoice, approved));
        mvc.perform(get("/api/invoices").header("X-API-KEY", KEY))
                .andExpect(jsonPath("$.data", hasSize(2)));
        mvc.perform(get("/api/invoices?status=approved").header("X-API-KEY", KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(1)))
                .andExpect(jsonPath("$.data[0].invoiceNo").value("INV-002"));
    }

    @Test @DisplayName("GET /api/invoices?status=BOGUS -> 400")
    void badStatusFilter() throws Exception {
        mvc.perform(get("/api/invoices?status=BOGUS").header("X-API-KEY", KEY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.message").value(containsString("status must be one of")));
    }

    @Test @DisplayName("GET /api/invoices/{id} -> 200")
    void getOne() throws Exception {
        mvc.perform(get("/api/invoices/" + id()).header("X-API-KEY", KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.invoiceNo").value("INV-001"))
                .andExpect(jsonPath("$.data.amount").value(1500.00))
                .andExpect(jsonPath("$.data.dueDate").value("2026-12-31"));
    }

    @Test @DisplayName("Unknown linearId -> 404")
    void unknownIdIs404() throws Exception {
        vaultReturns(Collections.emptyList());
        mvc.perform(get("/api/invoices/0f8fad5b-d9cb-469f-a165-70867728950e").header("X-API-KEY", KEY))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("INVOICE_NOT_FOUND"));
        mvc.perform(put("/api/invoices/0f8fad5b-d9cb-469f-a165-70867728950e/approve").header("X-API-KEY", KEY))
                .andExpect(status().isNotFound());
    }

    @Test @DisplayName("linearId that is not a UUID -> 400")
    void badUuidIs400() throws Exception {
        mvc.perform(get("/api/invoices/not-a-uuid").header("X-API-KEY", KEY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.message").value(containsString("not a valid UUID")));
    }

    @Test @DisplayName("GET /api/invoices/{id}/history returns every version in order")
    void history() throws Exception {
        vaultReturns(List.of(invoice.withStatus(InvoiceStatus.APPROVED, "ok"), invoice));
        mvc.perform(get("/api/invoices/" + id() + "/history").header("X-API-KEY", KEY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data", hasSize(2)))
                .andExpect(jsonPath("$.data[0].status").value("ISSUED"))
                .andExpect(jsonPath("$.data[0].stateStatus").value("CONSUMED"))
                .andExpect(jsonPath("$.data[1].status").value("APPROVED"))
                .andExpect(jsonPath("$.data[1].version").value(2));
    }

    // -------------------------------------------------------- transitions

    @Test @DisplayName("PUT /approve -> 200 with new status")
    void approve() throws Exception {
        flowReturns(ApproveInvoiceFlow.class, invoice.withStatus(InvoiceStatus.APPROVED, "Goods received"));
        mvc.perform(put("/api/invoices/" + id() + "/approve").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content("{\"remarks\":\"Goods received\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.invoice.status").value("APPROVED"))
                .andExpect(jsonPath("$.data.invoice.remarks").value("Goods received"));
    }

    @Test @DisplayName("Flow / contract failure (pay an un-approved invoice) -> 422")
    void flowFailureIs422() throws Exception {
        flowFails(PayInvoiceFlow.class,
                new FlowException("Invoice INV-001 must be APPROVED to move to PAID (current status: ISSUED)."));
        mvc.perform(put("/api/invoices/" + id() + "/pay").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content("{\"remarks\":\"UTR-1\"}"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.error.code").value("FLOW_FAILED"))
                .andExpect(jsonPath("$.error.message").value(containsString("must be APPROVED")));
    }

    @Test @DisplayName("Remarks longer than 500 chars -> 400")
    void remarksTooLong() throws Exception {
        String body = "{\"remarks\":\"" + "x".repeat(501) + "\"}";
        mvc.perform(put("/api/invoices/" + id() + "/reject").header("X-API-KEY", KEY)
                        .contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest());
    }

    @Test @DisplayName("OpenAPI document is served")
    void openApiDocs() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.paths['/api/invoices']").exists())
                .andExpect(jsonPath("$.components.securitySchemes.ApiKey.name").value("X-API-KEY"));
    }
}
