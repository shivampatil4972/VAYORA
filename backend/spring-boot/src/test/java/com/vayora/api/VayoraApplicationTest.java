package com.vayora.api;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

/**
 * Module 0 — Smoke test: Spring Boot context loads successfully.
 */
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "spring.flyway.enabled=false",
    "spring.jpa.hibernate.ddl-auto=create-drop"
})
class VayoraApplicationTest {

    @Test
    void contextLoads() {
        // If this passes, the Spring context assembles without errors.
    }
}
