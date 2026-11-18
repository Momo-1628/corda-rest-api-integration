package com.cordarest.webserver.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.LocalDate;

/** Body of POST /api/invoices. Bean Validation turns every broken rule into a 400 response. */
public record CreateInvoiceRequest(
        @Schema(example = "INV-2026-001")
        @NotBlank(message = "invoiceNo is required")
        @Size(max = 40, message = "invoiceNo must be at most 40 characters")
        String invoiceNo,

        @Schema(example = "O=BuyerCorp,L=Bengaluru,C=IN", description = "X.500 name or organisation name of the buyer")
        @NotBlank(message = "buyer is required")
        String buyer,

        @Schema(example = "125000.00")
        @NotNull(message = "amount is required")
        @DecimalMin(value = "0.01", message = "amount must be greater than 0")
        @Digits(integer = 15, fraction = 2, message = "amount can have at most 2 decimal places")
        BigDecimal amount,

        @Schema(example = "INR")
        @NotBlank(message = "currency is required")
        @Pattern(regexp = "^[A-Z]{3}$", message = "currency must be a 3-letter ISO code such as INR or USD")
        String currency,

        @Schema(example = "50 units of industrial steel rods")
        @Size(max = 255, message = "description must be at most 255 characters")
        String description,

        @Schema(example = "2026-12-31")
        @NotNull(message = "dueDate is required (yyyy-MM-dd)")
        @FutureOrPresent(message = "dueDate cannot be in the past")
        LocalDate dueDate
) { }
