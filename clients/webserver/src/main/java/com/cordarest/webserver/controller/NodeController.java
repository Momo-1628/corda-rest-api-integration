package com.cordarest.webserver.controller;

import com.cordarest.webserver.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import net.corda.core.identity.CordaX500Name;
import net.corda.core.identity.Party;
import net.corda.core.messaging.CordaRPCOps;
import net.corda.core.node.NodeInfo;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/** Node and network information: who am I, who are my peers, which notaries exist, is the node alive. */
@RestController
@RequestMapping("/api")
@Tag(name = "Node", description = "Identity, network map and health of the connected Corda node")
public class NodeController {

    private final CordaRPCOps rpc;

    public NodeController(CordaRPCOps rpc) { this.rpc = rpc; }

    @Operation(summary = "Legal identity of the node this API is connected to")
    @GetMapping("/me")
    public ApiResponse<Map<String, Object>> me() {
        NodeInfo info = rpc.nodeInfo();
        Party me = info.getLegalIdentities().get(0);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("name", me.getName().toString());
        data.put("organisation", me.getName().getOrganisation());
        data.put("locality", me.getName().getLocality());
        data.put("country", me.getName().getCountry());
        data.put("platformVersion", info.getPlatformVersion());
        return ApiResponse.ok(data);
    }

    @Operation(summary = "Other business nodes on the network (excluding this node and the notaries)")
    @GetMapping("/peers")
    public ApiResponse<Map<String, List<String>>> peers() {
        CordaX500Name myName = rpc.nodeInfo().getLegalIdentities().get(0).getName();
        Set<CordaX500Name> notaries = rpc.notaryIdentities().stream().map(Party::getName).collect(Collectors.toSet());
        List<String> peers = rpc.networkMapSnapshot().stream()
                .map(n -> n.getLegalIdentities().get(0).getName())
                .filter(n -> !n.equals(myName) && !notaries.contains(n))
                .map(CordaX500Name::toString)
                .sorted()
                .toList();
        return ApiResponse.ok(Map.of("peers", peers));
    }

    @Operation(summary = "Notaries available on the network")
    @GetMapping("/notaries")
    public ApiResponse<Map<String, List<String>>> notaries() {
        List<String> names = rpc.notaryIdentities().stream().map(p -> p.getName().toString()).sorted().toList();
        return ApiResponse.ok(Map.of("notaries", names));
    }

    @Operation(summary = "Liveness check - also verifies the RPC connection (no API key needed)")
    @GetMapping("/health")
    public ResponseEntity<ApiResponse<Map<String, Object>>> health() {
        Map<String, Object> data = new LinkedHashMap<>();
        try {
            data.put("status", "UP");
            data.put("node", rpc.nodeInfo().getLegalIdentities().get(0).getName().toString());
            data.put("nodeTime", rpc.currentNodeTime().toString());
            return ResponseEntity.ok(ApiResponse.ok(data));
        } catch (Exception e) {
            data.put("status", "DOWN");
            data.put("reason", e.getMessage());
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(ApiResponse.ok(data));
        }
    }
}
