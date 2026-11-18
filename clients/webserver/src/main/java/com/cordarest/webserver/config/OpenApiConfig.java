package com.cordarest.webserver.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** OpenAPI 3 description served by springdoc at /v3/api-docs and /swagger-ui.html. */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI cordaOpenAPI(@Value("${api.security.header:X-API-KEY}") String header,
                                @Value("${spring.profiles.active:default}") String profile) {
        return new OpenAPI()
                .info(new Info()
                        .title("Corda Invoice REST API (" + profile + " node)")
                        .version("1.0.0")
                        .description("REST gateway in front of a Corda 4.12 node. External systems (ERP, web apps) "
                                + "issue, approve, pay and reject invoices on the ledger through JSON calls.")
                        .contact(new Contact().name("Suraj Patel (24BTRBT029)")))
                .components(new Components().addSecuritySchemes("ApiKey",
                        new SecurityScheme().type(SecurityScheme.Type.APIKEY).in(SecurityScheme.In.HEADER).name(header)))
                .addSecurityItem(new SecurityRequirement().addList("ApiKey"));
    }
}
