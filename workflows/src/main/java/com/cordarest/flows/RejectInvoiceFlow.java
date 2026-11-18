package com.cordarest.flows;

import com.cordarest.contracts.InvoiceContract;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.contracts.CommandData;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.flows.FlowSession;
import net.corda.core.flows.InitiatedBy;
import net.corda.core.flows.InitiatingFlow;
import net.corda.core.flows.StartableByRPC;

/** Rejects an ISSUED invoice. Started by the BUYER. Transition: ISSUED -> REJECTED. */
@InitiatingFlow
@StartableByRPC
public class RejectInvoiceFlow extends InvoiceTransitionFlow {

    public RejectInvoiceFlow(UniqueIdentifier linearId, String remarks) {
        super(linearId, remarks);
    }

    @Override protected InvoiceStatus requiredStatus() { return InvoiceStatus.ISSUED; }
    @Override protected InvoiceStatus targetStatus() { return InvoiceStatus.REJECTED; }
    @Override protected CommandData command() { return new InvoiceContract.Commands.Reject(); }

    /** Runs on the SELLER and records the finalised transaction. */
    @InitiatedBy(RejectInvoiceFlow.class)
    public static class Responder extends InvoiceTransitionFlow.AbstractResponder {
        public Responder(FlowSession counterparty) { super(counterparty); }
    }
}
