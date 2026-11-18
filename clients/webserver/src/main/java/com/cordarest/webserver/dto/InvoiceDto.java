package com.cordarest.webserver.dto;

import com.cordarest.states.InvoiceState;

import java.math.BigDecimal;
import java.time.LocalDate;

/** JSON view of an InvoiceState. Parties are shown as X.500 names. */
public record InvoiceDto(
        String linearId,
        String invoiceNo,
        String seller,
        String buyer,
        BigDecimal amount,
        String currency,
        String description,
        LocalDate dueDate,
        String status,
        String remarks
) {
    public static InvoiceDto from(InvoiceState s) {
        return new InvoiceDto(
                s.getLinearId().getId().toString(),
                s.getInvoiceNo(),
                s.getSeller().getName().toString(),
                s.getBuyer().getName().toString(),
                s.getAmount(),
                s.getCurrency(),
                s.getDescription(),
                s.getDueDate(),
                s.getStatus().name(),
                s.getRemarks());
    }
}
