package com.cordarest.states;

import net.corda.core.serialization.CordaSerializable;

/**
 * Lifecycle of an invoice on the ledger.
 * ISSUED -> APPROVED -> PAID, or ISSUED -> REJECTED.
 */
@CordaSerializable
public enum InvoiceStatus {
    ISSUED,
    APPROVED,
    PAID,
    REJECTED
}
