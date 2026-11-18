package com.cordarest.flows;

import co.paralleluniverse.fibers.Suspendable;
import com.cordarest.contracts.InvoiceContract;
import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.contracts.Command;
import net.corda.core.contracts.CommandData;
import net.corda.core.contracts.StateAndRef;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.flows.*;
import net.corda.core.node.services.Vault;
import net.corda.core.node.services.vault.QueryCriteria;
import net.corda.core.transactions.SignedTransaction;
import net.corda.core.transactions.TransactionBuilder;
import net.corda.core.utilities.ProgressTracker;

import java.util.Collections;
import java.util.List;

/**
 * Shared logic for the buyer-side transitions (Approve, Pay, Reject).
 * The buyer finds the current invoice by linearId, moves it to the next status, signs alone,
 * notarises it and sends the result to the seller through FinalityFlow.
 */
public abstract class InvoiceTransitionFlow extends FlowLogic<SignedTransaction> {

    protected final UniqueIdentifier linearId;
    protected final String remarks;

    private final ProgressTracker.Step FINDING = new ProgressTracker.Step("Finding the invoice in the vault.");
    private final ProgressTracker.Step BUILDING = new ProgressTracker.Step("Building the transition transaction.");
    private final ProgressTracker.Step SIGNING = new ProgressTracker.Step("Signing with the buyer's key.");
    private final ProgressTracker.Step FINALISING = new ProgressTracker.Step("Notarising and recording.") {
        @Override public ProgressTracker childProgressTracker() { return FinalityFlow.Companion.tracker(); }
    };
    private final ProgressTracker progressTracker = new ProgressTracker(FINDING, BUILDING, SIGNING, FINALISING);

    protected InvoiceTransitionFlow(UniqueIdentifier linearId, String remarks) {
        this.linearId = linearId;
        this.remarks = remarks;
    }

    protected abstract InvoiceStatus requiredStatus();
    protected abstract InvoiceStatus targetStatus();
    protected abstract CommandData command();

    @Override
    public ProgressTracker getProgressTracker() { return progressTracker; }

    @Suspendable
    @Override
    public SignedTransaction call() throws FlowException {
        progressTracker.setCurrentStep(FINDING);
        final StateAndRef<InvoiceState> inRef = findUnconsumed(linearId);
        final InvoiceState in = inRef.getState().getData();

        if (!in.getBuyer().equals(getOurIdentity())) {
            throw new FlowException("Only the buyer (" + in.getBuyer().getName().getOrganisation()
                    + ") can " + command().getClass().getSimpleName().toLowerCase() + " this invoice.");
        }
        if (in.getStatus() != requiredStatus()) {
            throw new FlowException("Invoice " + in.getInvoiceNo() + " must be " + requiredStatus()
                    + " to move to " + targetStatus() + " (current status: " + in.getStatus() + ").");
        }

        progressTracker.setCurrentStep(BUILDING);
        final InvoiceState out = in.withStatus(targetStatus(), remarks);
        final TransactionBuilder builder = new TransactionBuilder(inRef.getState().getNotary())
                .addInputState(inRef)
                .addOutputState(out, InvoiceContract.ID)
                .addCommand(new Command<>(command(), in.getBuyer().getOwningKey()));
        builder.verify(getServiceHub());

        progressTracker.setCurrentStep(SIGNING);
        final SignedTransaction signed = getServiceHub().signInitialTransaction(builder);

        progressTracker.setCurrentStep(FINALISING);
        final FlowSession sellerSession = initiateFlow(in.getSeller());
        return subFlow(new FinalityFlow(signed, Collections.singletonList(sellerSession),
                FINALISING.childProgressTracker()));
    }

    @Suspendable
    protected StateAndRef<InvoiceState> findUnconsumed(UniqueIdentifier id) throws FlowException {
        QueryCriteria criteria = new QueryCriteria.LinearStateQueryCriteria(null, Collections.singletonList(id.getId()), null, Vault.StateStatus.UNCONSUMED);
        List<StateAndRef<InvoiceState>> found = getServiceHub().getVaultService()
                .queryBy(InvoiceState.class, criteria).getStates();
        if (found.isEmpty()) throw new FlowException("No unconsumed invoice found with linearId " + id);
        return found.get(0);
    }

    /** Seller side of every transition: simply record the finalised transaction. */
    public abstract static class AbstractResponder extends FlowLogic<SignedTransaction> {
        private final FlowSession counterparty;

        protected AbstractResponder(FlowSession counterparty) { this.counterparty = counterparty; }

        @Suspendable
        @Override
        public SignedTransaction call() throws FlowException {
            return subFlow(new ReceiveFinalityFlow(counterparty));
        }
    }
}
