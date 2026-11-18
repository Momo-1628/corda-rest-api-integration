package com.cordarest.flows;

import co.paralleluniverse.fibers.Suspendable;
import com.cordarest.contracts.InvoiceContract;
import com.cordarest.states.InvoiceState;
import net.corda.core.contracts.Command;
import net.corda.core.contracts.ContractState;
import net.corda.core.crypto.SecureHash;
import net.corda.core.flows.*;
import net.corda.core.identity.Party;
import net.corda.core.transactions.SignedTransaction;
import net.corda.core.transactions.TransactionBuilder;
import net.corda.core.utilities.ProgressTracker;
import org.jetbrains.annotations.NotNull;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;

import static net.corda.core.contracts.ContractsDSL.requireThat;

/**
 * Started by the SELLER. Creates a new ISSUED invoice that both the seller and the buyer sign,
 * then notarises it and records it in both vaults.
 */
@InitiatingFlow
@StartableByRPC
public class IssueInvoiceFlow extends FlowLogic<SignedTransaction> {

    private final String invoiceNo;
    private final Party buyer;
    private final BigDecimal amount;
    private final String currency;
    private final String description;
    private final LocalDate dueDate;

    private final ProgressTracker.Step BUILDING = new ProgressTracker.Step("Building the invoice transaction.");
    private final ProgressTracker.Step VERIFYING = new ProgressTracker.Step("Verifying the contract rules.");
    private final ProgressTracker.Step SIGNING = new ProgressTracker.Step("Signing with the seller's key.");
    private final ProgressTracker.Step COLLECTING = new ProgressTracker.Step("Collecting the buyer's signature.") {
        @Override public ProgressTracker childProgressTracker() { return CollectSignaturesFlow.Companion.tracker(); }
    };
    private final ProgressTracker.Step FINALISING = new ProgressTracker.Step("Notarising and recording.") {
        @Override public ProgressTracker childProgressTracker() { return FinalityFlow.Companion.tracker(); }
    };
    private final ProgressTracker progressTracker = new ProgressTracker(BUILDING, VERIFYING, SIGNING, COLLECTING, FINALISING);

    public IssueInvoiceFlow(String invoiceNo, Party buyer, BigDecimal amount, String currency,
                            String description, LocalDate dueDate) {
        this.invoiceNo = invoiceNo;
        this.buyer = buyer;
        this.amount = amount;
        this.currency = currency;
        this.description = description;
        this.dueDate = dueDate;
    }

    @Override
    public ProgressTracker getProgressTracker() { return progressTracker; }

    @Suspendable
    @Override
    public SignedTransaction call() throws FlowException {
        final Party seller = getOurIdentity();
        if (seller.equals(buyer)) throw new FlowException("The buyer must be a different party from the seller.");

        progressTracker.setCurrentStep(BUILDING);
        final Party notary = getServiceHub().getNetworkMapCache().getNotaryIdentities().get(0);
        final InvoiceState output = new InvoiceState(invoiceNo, seller, buyer, amount, currency, description, dueDate);
        final Command<InvoiceContract.Commands.Issue> cmd = new Command<>(new InvoiceContract.Commands.Issue(),
                Arrays.asList(seller.getOwningKey(), buyer.getOwningKey()));
        final TransactionBuilder builder = new TransactionBuilder(notary)
                .addOutputState(output, InvoiceContract.ID)
                .addCommand(cmd);

        progressTracker.setCurrentStep(VERIFYING);
        builder.verify(getServiceHub());

        progressTracker.setCurrentStep(SIGNING);
        final SignedTransaction partSigned = getServiceHub().signInitialTransaction(builder);

        progressTracker.setCurrentStep(COLLECTING);
        final FlowSession buyerSession = initiateFlow(buyer);
        final SignedTransaction fullySigned = subFlow(new CollectSignaturesFlow(partSigned,
                Collections.singletonList(buyerSession), COLLECTING.childProgressTracker()));

        progressTracker.setCurrentStep(FINALISING);
        return subFlow(new FinalityFlow(fullySigned, Collections.singletonList(buyerSession),
                FINALISING.childProgressTracker()));
    }

    /** Runs on the BUYER: checks the proposal before signing, then records the final transaction. */
    @InitiatedBy(IssueInvoiceFlow.class)
    public static class Responder extends FlowLogic<SignedTransaction> {
        private final FlowSession counterparty;

        public Responder(FlowSession counterparty) { this.counterparty = counterparty; }

        @Suspendable
        @Override
        public SignedTransaction call() throws FlowException {
            final Party me = getOurIdentity();
            class SignInvoice extends SignTransactionFlow {
                SignInvoice(FlowSession session) { super(session); }

                @Override
                protected void checkTransaction(@NotNull SignedTransaction stx) {
                    requireThat(req -> {
                        ContractState out = stx.getTx().getOutputs().get(0).getData();
                        req.using("The output must be an InvoiceState.", out instanceof InvoiceState);
                        InvoiceState inv = (InvoiceState) out;
                        req.using("I must be the buyer on this invoice.", inv.getBuyer().equals(me));
                        req.using("The counterparty must be the seller.",
                                inv.getSeller().equals(counterparty.getCounterparty()));
                        return null;
                    });
                }
            }
            final SecureHash txId = subFlow(new SignInvoice(counterparty)).getId();
            return subFlow(new ReceiveFinalityFlow(counterparty, txId));
        }
    }
}
