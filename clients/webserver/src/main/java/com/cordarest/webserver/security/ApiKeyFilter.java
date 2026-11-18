package com.cordarest.webserver.security;

import com.cordarest.webserver.dto.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Simple API-key authentication. Every /api/** call (except /api/health and CORS pre-flight)
 * must send the configured key in the X-API-KEY header, otherwise the API answers 401.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class ApiKeyFilter extends OncePerRequestFilter {

    private final String expectedKey;
    private final String headerName;
    private final ObjectMapper mapper;

    public ApiKeyFilter(@Value("${api.security.key}") String expectedKey,
                        @Value("${api.security.header:X-API-KEY}") String headerName,
                        ObjectMapper mapper) {
        this.expectedKey = expectedKey;
        this.headerName = headerName;
        this.mapper = mapper;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return !path.startsWith("/api/") || path.equals("/api/health")
                || "OPTIONS".equalsIgnoreCase(request.getMethod());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String provided = req.getHeader(headerName);
        if (provided == null || provided.isBlank()) {
            reject(res, "Missing " + headerName + " header");
            return;
        }
        // constant-time comparison so the key cannot be guessed from response timing
        if (!MessageDigest.isEqual(provided.getBytes(StandardCharsets.UTF_8),
                expectedKey.getBytes(StandardCharsets.UTF_8))) {
            reject(res, "Invalid API key");
            return;
        }
        chain.doFilter(req, res);
    }

    private void reject(HttpServletResponse res, String message) throws IOException {
        res.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        res.setContentType(MediaType.APPLICATION_JSON_VALUE);
        res.setCharacterEncoding("UTF-8");
        mapper.writeValue(res.getOutputStream(), ApiResponse.fail(401, "UNAUTHORIZED", message, null));
    }
}
