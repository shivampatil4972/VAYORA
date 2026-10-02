package com.vayora.api.controller;

import com.vayora.api.dto.LocationMessage;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

import java.time.Instant;

@Controller
public class LocationController {

    private final SimpMessagingTemplate messagingTemplate;

    public LocationController(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * Driver sends location updates to /app/location
     * We broadcast it to /topic/ride.{rideId}
     */
    @MessageMapping("/location")
    public void processLocationUpdate(@Payload LocationMessage message) {
        if (message.getTimestamp() == null) {
            message.setTimestamp(Instant.now());
        }
        // Broadcast the location to all subscribers of this specific ride
        String destination = "/topic/ride." + message.getRideId();
        messagingTemplate.convertAndSend(destination, message);
    }
}
