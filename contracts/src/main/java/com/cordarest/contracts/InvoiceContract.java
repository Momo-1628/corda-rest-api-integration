package com.cordarest.contracts;

import com.cordarest.states.InvoiceState;
import com.cordarest.states.InvoiceStatus;
import net.corda.core.contracts.CommandData;
import net.corda.core.contracts.CommandWithParties;
import net.corda.core.contracts.Contract;
import net.corda.core.contracts.TypeOnlyCommandData;
import net.corda.core.transactions.LedgerTransaction;
import org.jetbrains.annotations.NotNull;

import java.math.BigDecimal;
import java.security.PublicKey;
import java.util.List;
import java.util.Objects;

import static net.corda.core.contracts.ContractsDSL.requireSingleCommand;
import static net.corda.core.contracts.ContractsDSL.requireThat;

/**
 * Rules that every invoice transaction must obey.
 *
 *  Issue   : no input, 1 output ISSUED, amount > 0, seller != buyer, signed by seller AND buyer
 *  Approve : ISSUED   -> APPROVED, signed by buyer
 *  Pay     : APPROVED -> PAID,     signed by buyer
 *  Reject  : ISSUED   -> REJECTED, signed by buyer
 *  For every transition the invoiceNo, amount, currency, parties and linearId must not change.
 */
public class InvoiceContract implements Contract {

    public static final String ID = "com.cordarest.contracts.InvoiceContract";

    public interface Commands extends CommandData {
        class Issue extends TypeOnlyCommandData implements Commands { }
        class Approve extends TypeOnlyCommandData implements Commands { }
        class Pay extends TypeOnlyCommandData implements Commands { }
        class Reject extends TypeOnlyCommandData implements Commands { }
    }

    @Override
    public void verify(@NotNull LedgerTransaction tx) {
        final CommandWithParties<Commands> command = requireSingleCommand(tx.getCommands(), Commands.class);
        final List<PublicKey> signers = command.getSigners();
        final Commands value = command.getValue();

        if (value instanceof Commands.Issue) {
            verifyIssue(tx, signers);
        } else if (value instanceof Commands.Approve) {
            verifyTransition(tx, signers, InvoiceStatus.ISSUED, InvoiceStatus.APPROVED, "Approve");
        } else if (value instanceof Commands.Pay) {
            verifyTransition(tx, signers, InvoiceStatus.APPROVED, InvoiceStatus.PAID, "Pay");
        } else if (value instanceof Commands.Reject) {
            verifyTransition(tx, signers, InvoiceStatus.ISSUED, InvoiceStatus.REJECTED, "Reject");
        } else {
            throw new IllegalArgumentException("Unrecognised command.");
        }
    }

    private void verifyIssue(LedgerTransaction tx, List<PublicKey> signers) {
        requireThat(req -> {
            req.using("Issue: no input states should be consumed.", tx.getInputs().isEmpty());
            req.using("Issue: exactly one output state should be created.", tx.getOutputs().size() == 1);
            final List<InvoiceState> outs = tx.outputsOfType(InvoiceState.class);
            req.using("Issue: the output must be an InvoiceState.", outs.size() == 1);
            final InvoiceState out = outs.get(0);
            req.using("Issue: the output status must be ISSUED.", out.getStatus() == InvoiceStatus.ISSUED);
            req.using("Issue: the invoice number must not be blank.",
                    out.getInvoiceNo() != null && !out.getInvoiceNo().isBlank());
            req.using("Issue: the amount must be greater than zero.",
                    out.getAmount() != null && out.getAmount().compareTo(BigDecimal.ZERO) > 0);
            req.using("Issue: the seller and the buyer must be different parties.",
                    !out.getSeller().equals(out.getBuyer()));
            req.using("Issue: the seller must sign.", signers.contains(out.getSeller().getOwningKey()));
            req.using("Issue: the buyer must sign.", signers.contains(out.getBuyer().getOwningKey()));
            return null;
        });
    }

    private void verifyTransition(LedgerTransaction tx, List<PublicKey> signers,
                                  InvoiceStatus from, InvoiceStatus to, String name) {
        requireThat(req -> {
            req.using(name + ": exactly one input state should be consumed.", tx.getInputs().size() == 1);
            req.using(name + ": exactly one output state should be created.", tx.getOutputs().size() == 1);
            final List<InvoiceState> ins = tx.inputsOfType(InvoiceState.class);
            final List<InvoiceState> outs = tx.outputsOfType(InvoiceState.class);
            req.using(name + ": input and output must be InvoiceStates.", ins.size() == 1 && outs.size() == 1);
            final InvoiceState in = ins.get(0);
            final InvoiceState out = outs.get(0);
            req.using(name + ": the input status must be " + from + ".", in.getStatus() == from);
            req.using(name + ": the output status must be " + to + ".", out.getStatus() == to);
            req.using(name + ": the linearId must not change.", in.getLinearId().equals(out.getLinearId()));
            req.using(name + ": the invoice number must not change.", Objects.equals(in.getInvoiceNo(), out.getInvoiceNo()));
            req.using(name + ": the amount must not change.",
                    in.getAmount() != null && out.getAmount() != null && in.getAmount().compareTo(out.getAmount()) == 0);
            req.using(name + ": the currency must not change.", Objects.equals(in.getCurrency(), out.getCurrency()));
            req.using(name + ": the parties must not change.",
                    in.getSeller().equals(out.getSeller()) && in.getBuyer().equals(out.getBuyer()));
            req.using(name + ": the buyer must sign.", signers.contains(out.getBuyer().getOwningKey()));
            return null;
        });
    }
}
