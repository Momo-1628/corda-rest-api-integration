package com.cordarest.webserver.exception;

import com.cordarest.webserver.dto.ApiResponse;
import com.cordarest.webserver.exception.ApiExceptions.*;
import jakarta.validation.ConstraintViolationException;
import net.corda.client.rpc.RPCException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

import java.util.List;

/**
 * Maps every failure to the standard envelope with a meaningful HTTP status:
 * 400 validation, 404 unknown invoice, 422 flow/contract rejection, 503 node down, 504 timeout, 500 other.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> validation(MethodArgumentNotValidException e) {
        List<String> details = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .sorted()
                .toList();
        return build(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", "Request validation failed", details);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiResponse<Void>> constraint(ConstraintViolationException e) {
        List<String> details = e.getConstraintViolations().stream().map(v -> v.getMessage()).toList();
        return build(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", "Request validation failed", details);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> unreadable(HttpMessageNotReadableException e) {
        return build(HttpStatus.BAD_REQUEST, "MALFORMED_JSON",
                "Request body is missing or is not valid JSON (dates use yyyy-MM-dd)", null);
    }

    @ExceptionHandler({BadRequestException.class, MethodArgumentTypeMismatchException.class})
    public ResponseEntity<ApiResponse<Void>> badRequest(Exception e) {
        return build(HttpStatus.BAD_REQUEST, "BAD_REQUEST", e.getMessage(), null);
    }

    @ExceptionHandler(InvoiceNotFoundException.class)
    public ResponseEntity<ApiResponse<Void>> notFound(InvoiceNotFoundException e) {
        return build(HttpStatus.NOT_FOUND, "INVOICE_NOT_FOUND", e.getMessage(), null);
    }

    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<ApiResponse<Void>> noRoute(NoResourceFoundException e) {
        return build(HttpStatus.NOT_FOUND, "NOT_FOUND", "No endpoint " + e.getResourcePath(), null);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ApiResponse<Void>> method(HttpRequestMethodNotSupportedException e) {
        return build(HttpStatus.METHOD_NOT_ALLOWED, "METHOD_NOT_ALLOWED", e.getMessage(), null);
    }

    @ExceptionHandler(FlowFailedException.class)
    public ResponseEntity<ApiResponse<Void>> flowFailed(FlowFailedException e) {
        log.warn("Flow rejected: {}", e.getMessage());
        return build(HttpStatus.UNPROCESSABLE_ENTITY, "FLOW_FAILED", e.getMessage(), null);
    }

    @ExceptionHandler(FlowTimeoutException.class)
    public ResponseEntity<ApiResponse<Void>> timeout(FlowTimeoutException e) {
        return build(HttpStatus.GATEWAY_TIMEOUT, "FLOW_TIMEOUT", e.getMessage(), null);
    }

    @ExceptionHandler(RPCException.class)
    public ResponseEntity<ApiResponse<Void>> rpcDown(RPCException e) {
        log.error("RPC failure", e);
        return build(HttpStatus.SERVICE_UNAVAILABLE, "NODE_UNAVAILABLE", "The Corda node is not reachable over RPC", null);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> other(Exception e) {
        log.error("Unexpected error", e);
        return build(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", e.getMessage(), null);
    }

    private ResponseEntity<ApiResponse<Void>> build(HttpStatus status, String code, String message, List<String> details) {
        return ResponseEntity.status(status).body(ApiResponse.fail(status.value(), code, message, details));
    }
}
