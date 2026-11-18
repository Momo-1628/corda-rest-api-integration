package com.cordarest.flows;

import com.cordarest.contracts.InvoiceContract;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.contracts.CommandData;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.flows.FlowSession;
import net.corda.core.flows.InitiatedBy;
import net.corda.core.flows.InitiatingFlow;
import net.corda.core.flows.StartableByRPC;

/** Marks an APPROVED invoice as PAID. Started by the BUYER. Transition: APPROVED -> PAID. */
@InitiatingFlow
@StartableByRPC
public class PayInvoiceFlow extends InvoiceTransitionFlow {

    public PayInvoiceFlow(UniqueIdentifier linearId, String remarks) {
        super(linearId, remarks);
    }

    @Override protected InvoiceStatus requiredStatus() { return InvoiceStatus.APPROVED; }
    @Override protected InvoiceStatus targetStatus() { return InvoiceStatus.PAID; }
    @Override protected CommandData command() { return new InvoiceContract.Commands.Pay(); }

    /** Runs on the SELLER and records the finalised transaction. */
    @InitiatedBy(PayInvoiceFlow.class)
    public static class Responder extends InvoiceTransitionFlow.AbstractResponder {
        public Responder(FlowSession counterparty) { super(counterparty); }
    }
}
