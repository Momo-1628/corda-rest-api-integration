package com.cordarest.webserver.exception;

/** Small, typed exceptions that the GlobalExceptionHandler maps to HTTP status codes. */
public final class ApiExceptions {
    private ApiExceptions() { }

    /** 404 - no invoice with that linearId in this node's vault. */
    public static class InvoiceNotFoundException extends RuntimeException {
        public InvoiceNotFoundException(String linearId) {
            super("No invoice found with linearId " + linearId);
        }
    }

    /** 400 - the request is well-formed JSON but cannot be used (bad UUID, unknown buyer, bad status filter...). */
    public static class BadRequestException extends RuntimeException {
        public BadRequestException(String message) { super(message); }
    }

    /** 422 - the request reached Corda but the flow or the contract refused it. */
    public static class FlowFailedException extends RuntimeException {
        public FlowFailedException(String message, Throwable cause) { super(message, cause); }
    }

    /** 504 - the flow did not finish in time. */
    public static class FlowTimeoutException extends RuntimeException {
        public FlowTimeoutException(String message) { super(message); }
    }
}
