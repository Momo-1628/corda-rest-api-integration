package com.cordarest.webserver.dto;

/** Returned by every write endpoint: the Corda transaction hash, the invoice id and its new state. */
public record TransactionResult(String txHash, String linearId, InvoiceDto invoice) { }
