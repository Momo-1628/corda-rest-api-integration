package com.cordarest.webserver.dto;

import java.time.Instant;
import java.util.List;

/**
 * The one response envelope used by every endpoint:
 * { "success": true|false, "data": ..., "error": {status, code, message, details}, "timestamp": "..." }
 */
public record ApiResponse<T>(boolean success, T data, ApiError error, String timestamp) {

    public record ApiError(int status, String code, String message, List<String> details) { }

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(true, data, null, Instant.now().toString());
    }

    public static <T> ApiResponse<T> fail(int status, String code, String message, List<String> details) {
        return new ApiResponse<>(false, null, new ApiError(status, code, message, details), Instant.now().toString());
    }
}
