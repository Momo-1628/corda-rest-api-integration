package com.cordarest.webserver.controller;

import com.cordarest.webserver.dto.*;
import com.cordarest.webserver.service.InvoiceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST endpoints for the invoice lifecycle. Each write endpoint starts a Corda flow over RPC and
 * returns the transaction hash plus the new invoice state.
 */
@RestController
@RequestMapping("/api/invoices")
@Tag(name = "Invoices", description = "Issue, approve, pay, reject and audit invoices on the Corda ledger")
public class InvoiceController {

    private final InvoiceService service;

    public InvoiceController(InvoiceService service) { this.service = service; }

    @Operation(summary = "Issue a new invoice (seller node) - starts IssueInvoiceFlow")
    @ApiResponses({
            @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "201", description = "Invoice recorded on the ledger"),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "400", description = "Validation failed"),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "401", description = "Missing or wrong API key"),
            @io.swagger.v3.oas.annotations.responses.ApiResponse(responseCode = "422", description = "Flow or contract rejected the invoice")})
    @PostMapping
    public ResponseEntity<ApiResponse<TransactionResult>> issue(@Valid @RequestBody CreateInvoiceRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.ok(service.issue(request)));
    }

    @Operation(summary = "List current (unconsumed) invoices, optionally filtered by status")
    @GetMapping
    public ApiResponse<List<InvoiceDto>> list(
            @Parameter(description = "ISSUED, APPROVED, PAID or REJECTED") @RequestParam(required = false) String status) {
        return ApiResponse.ok(service.list(status));
    }

    @Operation(summary = "Get one invoice by its linearId")
    @GetMapping("/{linearId}")
    public ApiResponse<InvoiceDto> get(@PathVariable String linearId) {
        return ApiResponse.ok(service.get(linearId));
    }

    @Operation(summary = "Approve an ISSUED invoice (buyer node) - starts ApproveInvoiceFlow")
    @PutMapping("/{linearId}/approve")
    public ApiResponse<TransactionResult> approve(@PathVariable String linearId,
                                                  @Valid @RequestBody(required = false) RemarksRequest body) {
        return ApiResponse.ok(service.approve(linearId, remarks(body)));
    }

    @Operation(summary = "Pay an APPROVED invoice (buyer node) - starts PayInvoiceFlow")
    @PutMapping("/{linearId}/pay")
    public ApiResponse<TransactionResult> pay(@PathVariable String linearId,
                                              @Valid @RequestBody(required = false) RemarksRequest body) {
        return ApiResponse.ok(service.pay(linearId, remarks(body)));
    }

    @Operation(summary = "Reject an ISSUED invoice (buyer node) - starts RejectInvoiceFlow")
    @PutMapping("/{linearId}/reject")
    public ApiResponse<TransactionResult> reject(@PathVariable String linearId,
                                                 @Valid @RequestBody(required = false) RemarksRequest body) {
        return ApiResponse.ok(service.reject(linearId, remarks(body)));
    }

    @Operation(summary = "Full audit trail: every consumed and unconsumed version of the invoice")
    @GetMapping("/{linearId}/history")
    public ApiResponse<List<HistoryEntry>> history(@PathVariable String linearId) {
        return ApiResponse.ok(service.history(linearId));
    }

    private static String remarks(RemarksRequest body) {
        return body == null ? null : body.remarks();
    }
}
