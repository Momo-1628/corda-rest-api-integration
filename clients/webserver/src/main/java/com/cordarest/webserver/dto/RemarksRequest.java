package com.cordarest.webserver.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;

/** Optional body of PUT /api/invoices/{linearId}/approve | pay | reject. */
public record RemarksRequest(
        @Schema(example = "Goods received in good condition")
        @Size(max = 500, message = "remarks must be at most 500 characters")
        String remarks
) { }
