package com.vayora.api.controller;

import com.vayora.api.dto.SOSRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sos")
public class SOSController {

    private final SimpMessagingTemplate messagingTemplate;

    public SOSController(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    @PostMapping("/trigger")
    public ResponseEntity<?> triggerSOS(
            @Valid @RequestBody SOSRequest request,
            @AuthenticationPrincipal UUID userId
    ) {
        // 1. In a real system, we would log this to the DB, update ride status, etc.
        // 2. Broadcast the SOS alert to the ride's topic so the driver/passengers/admin get notified immediately.
        
        Map<String, Object> sosAlert = Map.of(
                "type", "SOS_ALERT",
                "rideId", request.getRideId(),
                "triggeredByUserId", userId,
                "timestamp", Instant.now(),
                "latitude", request.getCurrentLatitude() != null ? request.getCurrentLatitude() : "UNKNOWN",
                "longitude", request.getCurrentLongitude() != null ? request.getCurrentLongitude() : "UNKNOWN",
                "message", "Emergency SOS triggered for this ride!"
        );

        String destination = "/topic/ride." + request.getRideId();
        messagingTemplate.convertAndSend(destination, sosAlert);

        // Also broadcast to an admin topic
        messagingTemplate.convertAndSend("/topic/admin.sos", sosAlert);

        return ResponseEntity.ok(Map.of(
            "status", "SOS_TRIGGERED",
            "message", "Emergency services and admins have been notified.",
            "timestamp", Instant.now()
        ));
    }
}
