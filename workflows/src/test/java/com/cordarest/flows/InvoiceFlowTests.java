package com.cordarest.flows;

import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.concurrent.CordaFuture;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.identity.CordaX500Name;
import net.corda.core.identity.Party;
import net.corda.core.node.services.Vault;
import net.corda.core.node.services.vault.QueryCriteria;
import net.corda.core.transactions.SignedTransaction;
import net.corda.testing.node.*;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutionException;

import static org.junit.Assert.*;

/** End-to-end flow tests on an in-memory MockNetwork (SellerCorp, BuyerCorp, Notary). */
public class InvoiceFlowTests {

    private MockNetwork network;
    private StartedMockNode seller;
    private StartedMockNode buyer;
    private Party buyerParty;

    @Before
    public void setup() {
        network = new MockNetwork(new MockNetworkParameters()
                .withCordappsForAllNodes(Arrays.asList(
                        TestCordapp.findCordapp("com.cordarest.contracts"),
                        TestCordapp.findCordapp("com.cordarest.flows")))
                .withNotarySpecs(Collections.singletonList(
                        new MockNetworkNotarySpec(CordaX500Name.parse("O=Notary,L=London,C=GB")))));
        seller = network.createPartyNode(CordaX500Name.parse("O=SellerCorp,L=Mumbai,C=IN"));
        buyer = network.createPartyNode(CordaX500Name.parse("O=BuyerCorp,L=Bengaluru,C=IN"));
        buyerParty = buyer.getInfo().getLegalIdentities().get(0);
        network.runNetwork();
    }

    @After
    public void tearDown() { network.stopNodes(); }

    private <T> T run(StartedMockNode node, net.corda.core.flows.FlowLogic<T> flow) throws Exception {
        CordaFuture<T> f = node.startFlow(flow);
        network.runNetwork();
        return f.get();
    }

    private InvoiceState issue(String no) throws Exception {
        SignedTransaction stx = run(seller, new IssueInvoiceFlow(no, buyerParty, new BigDecimal("2500.50"), "INR",
                "Laptop batch", LocalDate.of(2026, 12, 31)));
        return stx.getTx().outputsOfType(InvoiceState.class).get(0);
    }

    private InvoiceState vaultState(StartedMockNode node, UniqueIdentifier id) {
        QueryCriteria c = new QueryCriteria.LinearStateQueryCriteria(null, Collections.singletonList(id.getId()), null, Vault.StateStatus.UNCONSUMED);
        List<net.corda.core.contracts.StateAndRef<InvoiceState>> states =
                node.getServices().getVaultService().queryBy(InvoiceState.class, c).getStates();
        assertEquals(1, states.size());
        return states.get(0).getState().getData();
    }

    @Test
    public void issueIsSignedByBothPartiesAndRecordedInBothVaults() throws Exception {
        SignedTransaction stx = run(seller, new IssueInvoiceFlow("INV-100", buyerParty, new BigDecimal("1000"), "INR",
                "Desks", LocalDate.of(2026, 12, 1)));
        stx.verifyRequiredSignatures();
        InvoiceState out = stx.getTx().outputsOfType(InvoiceState.class).get(0);
        assertEquals(InvoiceStatus.ISSUED, vaultState(seller, out.getLinearId()).getStatus());
        assertEquals(InvoiceStatus.ISSUED, vaultState(buyer, out.getLinearId()).getStatus());
    }

    @Test
    public void issueApprovePayLifecycle() throws Exception {
        InvoiceState inv = issue("INV-101");
        run(buyer, new ApproveInvoiceFlow(inv.getLinearId(), "Goods received"));
        assertEquals(InvoiceStatus.APPROVED, vaultState(seller, inv.getLinearId()).getStatus());

        run(buyer, new PayInvoiceFlow(inv.getLinearId(), "UTR-778899"));
        InvoiceState paidAtSeller = vaultState(seller, inv.getLinearId());
        InvoiceState paidAtBuyer = vaultState(buyer, inv.getLinearId());
        assertEquals(InvoiceStatus.PAID, paidAtSeller.getStatus());
        assertEquals(InvoiceStatus.PAID, paidAtBuyer.getStatus());
        assertEquals("UTR-778899", paidAtSeller.getRemarks());
        assertEquals(0, new BigDecimal("2500.50").compareTo(paidAtSeller.getAmount()));
    }

    @Test
    public void issueRejectLifecycle() throws Exception {
        InvoiceState inv = issue("INV-102");
        run(buyer, new RejectInvoiceFlow(inv.getLinearId(), "Wrong quantity"));
        assertEquals(InvoiceStatus.REJECTED, vaultState(seller, inv.getLinearId()).getStatus());
        assertEquals(InvoiceStatus.REJECTED, vaultState(buyer, inv.getLinearId()).getStatus());
    }

    @Test
    public void payingAnUnapprovedInvoiceFails() throws Exception {
        InvoiceState inv = issue("INV-103");
        try {
            run(buyer, new PayInvoiceFlow(inv.getLinearId(), null));
            fail("Expected the flow to fail");
        } catch (ExecutionException e) {
            assertTrue(e.getCause().getMessage().contains("must be APPROVED"));
        }
    }

    @Test
    public void sellerCannotApproveItsOwnInvoice() throws Exception {
        InvoiceState inv = issue("INV-104");
        try {
            run(seller, new ApproveInvoiceFlow(inv.getLinearId(), null));
            fail("Expected the flow to fail");
        } catch (ExecutionException e) {
            assertTrue(e.getCause().getMessage().contains("Only the buyer"));
        }
    }

    @Test
    public void issuingWithZeroAmountFailsContractVerification() {
        try {
            run(seller, new IssueInvoiceFlow("INV-105", buyerParty, BigDecimal.ZERO, "INR", "Free", LocalDate.of(2026, 12, 1)));
            fail("Expected the flow to fail");
        } catch (Exception e) {
            String msg = e.getCause() != null ? e.getCause().getMessage() : e.getMessage();
            assertTrue(msg, msg.contains("amount must be greater than zero"));
        }
    }
}
