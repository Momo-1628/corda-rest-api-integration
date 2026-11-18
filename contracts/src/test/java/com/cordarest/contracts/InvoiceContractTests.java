package com.cordarest.contracts;

import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.identity.CordaX500Name;
import net.corda.testing.core.TestIdentity;
import net.corda.testing.node.MockServices;
import org.junit.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;

import static net.corda.testing.node.NodeTestUtils.ledger;
import static net.corda.testing.node.NodeTestUtils.transaction;

/** Contract tests for {@link InvoiceContract} using the MockServices ledger DSL. */
public class InvoiceContractTests {

    private final TestIdentity seller = new TestIdentity(new CordaX500Name("SellerCorp", "Mumbai", "IN"));
    private final TestIdentity buyer = new TestIdentity(new CordaX500Name("BuyerCorp", "Bengaluru", "IN"));
    private final TestIdentity other = new TestIdentity(new CordaX500Name("OtherCorp", "Delhi", "IN"));
    private final MockServices ledgerServices = new MockServices(Collections.singletonList("com.cordarest.contracts"));

    // one fixed invoice per test instance, so input and output share the same linearId
    private final InvoiceState base = new InvoiceState("INV-001", seller.getParty(), buyer.getParty(), new BigDecimal("1500.00"), "INR",
                "Steel rods", LocalDate.of(2026, 12, 31));

    private InvoiceState issued() {
        return base;
    }

    // ---------------- Issue ----------------

    @Test
    public void issueIsValidWhenSignedByBothParties() {
        transaction(ledgerServices, tx -> {
            tx.output(InvoiceContract.ID, issued());
            tx.command(Arrays.asList(seller.getPublicKey(), buyer.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.verifies();
        });
    }

    @Test
    public void issueFailsWhenAmountIsZeroOrNegative() {
        transaction(ledgerServices, tx -> {
            tx.output(InvoiceContract.ID, new InvoiceState("INV-002", seller.getParty(), buyer.getParty(),
                    new BigDecimal("-10"), "INR", "Bad", LocalDate.of(2026, 12, 31)));
            tx.command(Arrays.asList(seller.getPublicKey(), buyer.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.failsWith("amount must be greater than zero");
        });
    }

    @Test
    public void issueFailsWhenSellerEqualsBuyer() {
        transaction(ledgerServices, tx -> {
            tx.output(InvoiceContract.ID, new InvoiceState("INV-003", seller.getParty(), seller.getParty(),
                    new BigDecimal("100"), "INR", "Self", LocalDate.of(2026, 12, 31)));
            tx.command(Collections.singletonList(seller.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.failsWith("seller and the buyer must be different");
        });
    }

    @Test
    public void issueFailsWithoutBuyerSignature() {
        transaction(ledgerServices, tx -> {
            tx.output(InvoiceContract.ID, issued());
            tx.command(Collections.singletonList(seller.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.failsWith("buyer must sign");
        });
    }

    @Test
    public void issueFailsWithAnInput() {
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, issued());
            tx.output(InvoiceContract.ID, issued());
            tx.command(Arrays.asList(seller.getPublicKey(), buyer.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.failsWith("no input states should be consumed");
        });
    }

    @Test
    public void issueFailsWhenOutputIsNotIssued() {
        transaction(ledgerServices, tx -> {
            tx.output(InvoiceContract.ID, issued().withStatus(InvoiceStatus.PAID, null));
            tx.command(Arrays.asList(seller.getPublicKey(), buyer.getPublicKey()), new InvoiceContract.Commands.Issue());
            return tx.failsWith("output status must be ISSUED");
        });
    }

    // ---------------- Approve / Pay / Reject ----------------

    @Test
    public void approveIsValidWhenSignedByBuyer() {
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, issued());
            tx.output(InvoiceContract.ID, issued().withStatus(InvoiceStatus.APPROVED, "OK"));
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Approve());
            return tx.verifies();
        });
    }

    @Test
    public void approveFailsWhenOnlySellerSigns() {
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, issued());
            tx.output(InvoiceContract.ID, issued().withStatus(InvoiceStatus.APPROVED, "OK"));
            tx.command(Collections.singletonList(seller.getPublicKey()), new InvoiceContract.Commands.Approve());
            return tx.failsWith("buyer must sign");
        });
    }

    @Test
    public void approveFailsWhenAmountChanges() {
        InvoiceState in = issued();
        InvoiceState tampered = new InvoiceState(in.getLinearId(), in.getInvoiceNo(), in.getSeller(), in.getBuyer(),
                new BigDecimal("99999"), in.getCurrency(), in.getDescription(), in.getDueDate(), InvoiceStatus.APPROVED, null);
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, in);
            tx.output(InvoiceContract.ID, tampered);
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Approve());
            return tx.failsWith("amount must not change");
        });
    }

    @Test
    public void approveFailsWhenPartiesChange() {
        InvoiceState in = issued();
        InvoiceState tampered = new InvoiceState(in.getLinearId(), in.getInvoiceNo(), other.getParty(), in.getBuyer(),
                in.getAmount(), in.getCurrency(), in.getDescription(), in.getDueDate(), InvoiceStatus.APPROVED, null);
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, in);
            tx.output(InvoiceContract.ID, tampered);
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Approve());
            return tx.failsWith("parties must not change");
        });
    }

    @Test
    public void payIsValidFromApproved() {
        InvoiceState approved = issued().withStatus(InvoiceStatus.APPROVED, null);
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, approved);
            tx.output(InvoiceContract.ID, approved.withStatus(InvoiceStatus.PAID, "UTR-123"));
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Pay());
            return tx.verifies();
        });
    }

    @Test
    public void payFailsWhenInvoiceIsNotApproved() {
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, issued());
            tx.output(InvoiceContract.ID, issued().withStatus(InvoiceStatus.PAID, null));
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Pay());
            return tx.failsWith("input status must be APPROVED");
        });
    }

    @Test
    public void rejectIsValidFromIssued() {
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, issued());
            tx.output(InvoiceContract.ID, issued().withStatus(InvoiceStatus.REJECTED, "Wrong quantity"));
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Reject());
            return tx.verifies();
        });
    }

    @Test
    public void rejectFailsFromApproved() {
        InvoiceState approved = issued().withStatus(InvoiceStatus.APPROVED, null);
        transaction(ledgerServices, tx -> {
            tx.input(InvoiceContract.ID, approved);
            tx.output(InvoiceContract.ID, approved.withStatus(InvoiceStatus.REJECTED, null));
            tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Reject());
            return tx.failsWith("input status must be ISSUED");
        });
    }

    @Test
    public void fullLifecycleInOneLedger() {
        InvoiceState inv = issued();
        ledger(ledgerServices, l -> {
            l.transaction(tx -> {
                tx.output(InvoiceContract.ID, "issued", inv);
                tx.command(Arrays.asList(seller.getPublicKey(), buyer.getPublicKey()), new InvoiceContract.Commands.Issue());
                return tx.verifies();
            });
            l.transaction(tx -> {
                tx.input("issued");
                tx.output(InvoiceContract.ID, "approved", inv.withStatus(InvoiceStatus.APPROVED, null));
                tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Approve());
                return tx.verifies();
            });
            l.transaction(tx -> {
                tx.input("approved");
                tx.output(InvoiceContract.ID, inv.withStatus(InvoiceStatus.PAID, null));
                tx.command(Collections.singletonList(buyer.getPublicKey()), new InvoiceContract.Commands.Pay());
                return tx.verifies();
            });
            return null;
        });
    }
}
