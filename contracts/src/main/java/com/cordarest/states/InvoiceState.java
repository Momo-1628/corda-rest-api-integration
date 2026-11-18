package com.cordarest.states;

import com.cordarest.contracts.InvoiceContract;
import net.corda.core.contracts.BelongsToContract;
import net.corda.core.contracts.LinearState;
import net.corda.core.contracts.UniqueIdentifier;
import net.corda.core.identity.AbstractParty;
import net.corda.core.identity.Party;
import net.corda.core.serialization.ConstructorForDeserialization;
import org.jetbrains.annotations.NotNull;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * An invoice shared between a seller and a buyer.
 * It is a LinearState, so every version of the same invoice shares one linearId.
 */
@BelongsToContract(InvoiceContract.class)
public class InvoiceState implements LinearState {

    private final UniqueIdentifier linearId;
    private final String invoiceNo;
    private final Party seller;
    private final Party buyer;
    private final BigDecimal amount;
    private final String currency;
    private final String description;
    private final LocalDate dueDate;
    private final InvoiceStatus status;
    private final String remarks;

    @ConstructorForDeserialization
    public InvoiceState(UniqueIdentifier linearId, String invoiceNo, Party seller, Party buyer,
                        BigDecimal amount, String currency, String description, LocalDate dueDate,
                        InvoiceStatus status, String remarks) {
        this.linearId = linearId;
        this.invoiceNo = invoiceNo;
        this.seller = seller;
        this.buyer = buyer;
        this.amount = amount;
        this.currency = currency;
        this.description = description;
        this.dueDate = dueDate;
        this.status = status;
        this.remarks = remarks;
    }

    /** Convenience constructor for a brand new invoice (status ISSUED, fresh linearId). */
    public InvoiceState(String invoiceNo, Party seller, Party buyer, BigDecimal amount, String currency,
                        String description, LocalDate dueDate) {
        this(new UniqueIdentifier(invoiceNo), invoiceNo, seller, buyer, amount, currency, description,
                dueDate, InvoiceStatus.ISSUED, null);
    }

    /** Returns a copy of this invoice with a new status and remarks; everything else stays the same. */
    public InvoiceState withStatus(InvoiceStatus newStatus, String newRemarks) {
        return new InvoiceState(linearId, invoiceNo, seller, buyer, amount, currency, description, dueDate,
                newStatus, newRemarks);
    }

    @NotNull
    @Override
    public UniqueIdentifier getLinearId() { return linearId; }

    @NotNull
    @Override
    public List<AbstractParty> getParticipants() { return Arrays.asList(seller, buyer); }

    public String getInvoiceNo() { return invoiceNo; }
    public Party getSeller() { return seller; }
    public Party getBuyer() { return buyer; }
    public BigDecimal getAmount() { return amount; }
    public String getCurrency() { return currency; }
    public String getDescription() { return description; }
    public LocalDate getDueDate() { return dueDate; }
    public InvoiceStatus getStatus() { return status; }
    public String getRemarks() { return remarks; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof InvoiceState)) return false;
        InvoiceState that = (InvoiceState) o;
        return Objects.equals(linearId, that.linearId) && Objects.equals(invoiceNo, that.invoiceNo)
                && Objects.equals(seller, that.seller) && Objects.equals(buyer, that.buyer)
                && Objects.equals(amount, that.amount) && Objects.equals(currency, that.currency)
                && Objects.equals(description, that.description) && Objects.equals(dueDate, that.dueDate)
                && status == that.status && Objects.equals(remarks, that.remarks);
    }

    @Override
    public int hashCode() {
        return Objects.hash(linearId, invoiceNo, seller, buyer, amount, currency, description, dueDate, status, remarks);
    }

    @Override
    public String toString() {
        return "InvoiceState{" + invoiceNo + ", " + amount + " " + currency + ", " + status + ", id=" + linearId + "}";
    }
}
