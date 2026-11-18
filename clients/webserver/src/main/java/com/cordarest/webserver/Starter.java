package com.cordarest.webserver;

import org.springframework.boot.Banner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import static org.springframework.boot.WebApplicationType.SERVLET;

/**
 * Spring Boot entry point for the Corda REST API.
 * One instance runs per node, e.g. --spring.profiles.active=seller (port 10050)
 * or --spring.profiles.active=buyer (port 10060).
 */
@SpringBootApplication
public class Starter {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(Starter.class);
        app.setBannerMode(Banner.Mode.OFF);
        app.setWebApplicationType(SERVLET);
        app.run(args);
    }
}
