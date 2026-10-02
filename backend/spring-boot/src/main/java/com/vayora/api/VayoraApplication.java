package com.vayora.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * VAYORA — AI-Powered Intercity Shared Mobility Platform
 * Spring Boot Application Entry Point
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class VayoraApplication {

    public static void main(String[] args) {
        SpringApplication.run(VayoraApplication.class, args);
    }
}
