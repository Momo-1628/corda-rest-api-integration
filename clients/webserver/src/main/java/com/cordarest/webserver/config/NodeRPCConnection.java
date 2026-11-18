package com.cordarest.webserver.config;

import jakarta.annotation.PreDestroy;
import net.corda.client.rpc.CordaRPCClient;
import net.corda.client.rpc.CordaRPCConnection;
import net.corda.core.messaging.CordaRPCOps;
import net.corda.core.utilities.NetworkHostAndPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Opens one RPC connection to the Corda node chosen in the application properties
 * (config.rpc.host / port / username / password) and exposes the CordaRPCOps proxy as a bean.
 * In the API tests this bean is replaced with a Mockito mock.
 */
@Configuration
public class NodeRPCConnection {

    private static final Logger log = LoggerFactory.getLogger(NodeRPCConnection.class);

    @Value("${config.rpc.host}") private String host;
    @Value("${config.rpc.port}") private int rpcPort;
    @Value("${config.rpc.username}") private String username;
    @Value("${config.rpc.password}") private String password;

    private CordaRPCConnection connection;

    @Bean
    public CordaRPCOps cordaRPCOps() {
        NetworkHostAndPort address = new NetworkHostAndPort(host, rpcPort);
        log.info("Connecting to Corda node RPC at {} as '{}'", address, username);
        connection = new CordaRPCClient(address).start(username, password);
        CordaRPCOps proxy = connection.getProxy();
        log.info("Connected to {}", proxy.nodeInfo().getLegalIdentities().get(0).getName());
        return proxy;
    }

    @PreDestroy
    public void close() {
        if (connection != null) {
            log.info("Closing the RPC connection");
            connection.notifyServerAndClose();
        }
    }
}
