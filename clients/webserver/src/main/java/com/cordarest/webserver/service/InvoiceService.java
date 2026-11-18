package com.cordarest.webserver.service;

import com.cordarest.flows.ApproveInvoiceFlow;
import com.cordarest.flows.IssueInvoiceFlow;
import com.cordarest.flows.PayInvoiceFlow;
import com.cordarest.flows.RejectInvoiceFlow;
import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import com.cordarest.webserver.dto.CreateInvoiceRequest;
import com.cordarest.webserver.dto.HistoryEntry;
import com.cordarest.webserver.dto.InvoiceDto;
import com.cordarest.webserver.dto.TransactionResult;
import com.cordarest.webserver.exception.ApiExceptions.*;
import net.corda.core.CordaException;
import net.corda.core.CordaRuntimeException;
import net.corda.core.contracts.StateAndRef;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.flows.FlowLogic;
import net.corda.core.identity.CordaX500Name;
import net.corda.core.identity.Party;
import net.corda.core.messaging.CordaRPCOps;
import net.corda.core.node.services.Vault;
import net.corda.core.node.services.vault.PageSpecification;
import net.corda.core.node.services.vault.QueryCriteria;
import net.corda.core.node.services.vault.Sort;
import net.corda.core.transactions.SignedTransaction;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * The bridge between HTTP and Corda. Every method talks to the node only through CordaRPCOps:
 * vault queries for reads and startFlowDynamic(...) for writes.
 */
@Service
public class InvoiceService {

    private static final PageSpecification PAGE = new PageSpecification(1, 500);
    private static final Sort NO_SORT = new Sort(Collections.emptySet());

    private final CordaRPCOps rpc;
    private final long timeoutSeconds;

    public InvoiceService(CordaRPCOps rpc, @Value("${api.flow.timeout-seconds:60}") long timeoutSeconds) {
        this.rpc = rpc;
        this.timeoutSeconds = timeoutSeconds;
    }

    // ------------------------------------------------------------------ reads

    public List<InvoiceDto> list(String status) {
        InvoiceStatus filter = parseStatus(status);
        QueryCriteria criteria = new QueryCriteria.VaultQueryCriteria(Vault.StateStatus.UNCONSUMED);
        return rpc.vaultQueryBy(criteria, PAGE, NO_SORT, InvoiceState.class).getStates().stream()
                .map(s -> s.getState().getData())
                .filter(s -> filter == null || s.getStatus() == filter)
                .sorted(Comparator.comparing(InvoiceState::getInvoiceNo))
                .map(InvoiceDto::from)
                .toList();
    }

    public InvoiceDto get(String linearId) {
        return InvoiceDto.from(findUnconsumed(parseId(linearId)).getState().getData());
    }

    public List<HistoryEntry> history(String linearId) {
        UniqueIdentifier id = parseId(linearId);
        QueryCriteria criteria = new QueryCriteria.LinearStateQueryCriteria(null, Collections.singletonList(id.getId()), null, Vault.StateStatus.ALL);
        Vault.Page<InvoiceState> page = rpc.vaultQueryBy(criteria, PAGE, NO_SORT, InvoiceState.class);
        if (page.getStates().isEmpty()) throw new InvoiceNotFoundException(linearId);

        List<HistoryEntry> entries = new ArrayList<>();
        for (int i = 0; i < page.getStates().size(); i++) {
            StateAndRef<InvoiceState> sar = page.getStates().get(i);
            Vault.StateMetadata meta = page.getStatesMetadata().size() > i ? page.getStatesMetadata().get(i) : null;
            InvoiceState s = sar.getState().getData();
            entries.add(new HistoryEntry(0, s.getStatus().name(), s.getRemarks(),
                    sar.getRef().getTxhash().toString(),
                    meta == null ? "UNKNOWN" : meta.getStatus().name(),
                    meta == null || meta.getRecordedTime() == null ? null : meta.getRecordedTime().toString(),
                    meta == null || meta.getConsumedTime() == null ? null : meta.getConsumedTime().toString()));
        }
        // order by lifecycle: ISSUED first, latest last
        entries.sort(Comparator.comparing((HistoryEntry e) -> e.recordedTime() == null ? "" : e.recordedTime())
                .thenComparing(e -> InvoiceStatus.valueOf(e.status()).ordinal()));
        List<HistoryEntry> numbered = new ArrayList<>();
        for (int i = 0; i < entries.size(); i++) {
            HistoryEntry e = entries.get(i);
            numbered.add(new HistoryEntry(i + 1, e.status(), e.remarks(), e.txHash(), e.stateStatus(),
                    e.recordedTime(), e.consumedTime()));
        }
        return numbered;
    }

    // ----------------------------------------------------------------- writes

    public TransactionResult issue(CreateInvoiceRequest req) {
        Party buyer = resolveParty(req.buyer());
        Party me = rpc.nodeInfo().getLegalIdentities().get(0);
        if (buyer.equals(me)) throw new BadRequestException("buyer must be a different party from this node (" + me.getName() + ")");
        SignedTransaction stx = runFlow(IssueInvoiceFlow.class, req.invoiceNo().trim(), buyer, req.amount(),
                req.currency(), req.description() == null ? "" : req.description(), req.dueDate());
        return toResult(stx);
    }

    public TransactionResult approve(String linearId, String remarks) {
        return transition(ApproveInvoiceFlow.class, linearId, remarks);
    }

    public TransactionResult pay(String linearId, String remarks) {
        return transition(PayInvoiceFlow.class, linearId, remarks);
    }

    public TransactionResult reject(String linearId, String remarks) {
        return transition(RejectInvoiceFlow.class, linearId, remarks);
    }

    private TransactionResult transition(Class<? extends FlowLogic<SignedTransaction>> flow, String linearId, String remarks) {
        UniqueIdentifier id = parseId(linearId);
        findUnconsumed(id); // 404 before we bother the flow framework
        return toResult(runFlow(flow, id, remarks == null ? "" : remarks));
    }

    // ---------------------------------------------------------------- helpers

    private SignedTransaction runFlow(Class<? extends FlowLogic<SignedTransaction>> flow, Object... args) {
        try {
            return rpc.startFlowDynamic(flow, args).getReturnValue().get(timeoutSeconds, TimeUnit.SECONDS);
        } catch (ExecutionException e) {
            Throwable cause = e.getCause() == null ? e : e.getCause();
            throw new FlowFailedException(cleanMessage(cause), cause);
        } catch (TimeoutException e) {
            throw new FlowTimeoutException(flow.getSimpleName() + " did not finish within " + timeoutSeconds + " s");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new FlowTimeoutException("Interrupted while waiting for " + flow.getSimpleName());
        } catch (CordaRuntimeException e) {
            // e.g. a flow that throws while being started on the node
            throw new FlowFailedException(cleanMessage(e), e);
        }
    }

    /** Corda wraps contract errors as "Contract verification failed: <rule>, contract: ..."; keep the useful part. */
    static String cleanMessage(Throwable t) {
        String msg = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
        if (t instanceof CordaException || t instanceof CordaRuntimeException) {
            int idx = msg.indexOf(", contract:");
            if (idx > 0) msg = msg.substring(0, idx);
            msg = msg.replace("java.lang.IllegalArgumentException: ", "").replace("Failed requirement: ", "");
        }
        return msg.trim();
    }

    private TransactionResult toResult(SignedTransaction stx) {
        InvoiceState out = stx.getTx().outputsOfType(InvoiceState.class).get(0);
        return new TransactionResult(stx.getId().toString(), out.getLinearId().getId().toString(), InvoiceDto.from(out));
    }

    private StateAndRef<InvoiceState> findUnconsumed(UniqueIdentifier id) {
        QueryCriteria criteria = new QueryCriteria.LinearStateQueryCriteria(null, Collections.singletonList(id.getId()), null, Vault.StateStatus.UNCONSUMED);
        List<StateAndRef<InvoiceState>> states = rpc.vaultQueryBy(criteria, PAGE, NO_SORT, InvoiceState.class).getStates();
        if (states.isEmpty()) throw new InvoiceNotFoundException(id.getId().toString());
        return states.get(0);
    }

    private UniqueIdentifier parseId(String linearId) {
        try {
            return new UniqueIdentifier(null, UUID.fromString(linearId));
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("linearId '" + linearId + "' is not a valid UUID");
        }
    }

    private InvoiceStatus parseStatus(String status) {
        if (status == null || status.isBlank()) return null;
        try {
            return InvoiceStatus.valueOf(status.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("status must be one of " + Arrays.toString(InvoiceStatus.values()));
        }
    }

    /** Accepts a full X.500 name ("O=BuyerCorp,L=Bengaluru,C=IN") or just the organisation ("BuyerCorp"). */
    Party resolveParty(String name) {
        Party party = null;
        if (name.contains("=")) {
            try {
                party = rpc.wellKnownPartyFromX500Name(CordaX500Name.parse(name));
            } catch (IllegalArgumentException e) {
                throw new BadRequestException("buyer '" + name + "' is not a valid X.500 name");
            }
        } else {
            Set<Party> matches = rpc.partiesFromName(name, false);
            if (matches.size() > 1) throw new BadRequestException("buyer '" + name + "' matches more than one party");
            if (matches.size() == 1) party = matches.iterator().next();
        }
        if (party == null) throw new BadRequestException("buyer '" + name + "' is not known on the network");
        return party;
    }
}
