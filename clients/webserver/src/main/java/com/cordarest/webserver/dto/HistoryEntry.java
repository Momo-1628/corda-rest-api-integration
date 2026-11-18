package com.cordarest.webserver.dto;

/** One version of an invoice in its audit trail (consumed or unconsumed). */
public record HistoryEntry(
        int version,
        String status,
        String remarks,
        String txHash,
        String stateStatus,
        String recordedTime,
        String consumedTime
) { }
