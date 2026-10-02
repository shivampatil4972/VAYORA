package com.vayora.api.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public class SOSRequest {
    @NotNull
    private UUID rideId;

    private Double currentLatitude;
    private Double currentLongitude;

    public UUID getRideId() { return rideId; }
    public void setRideId(UUID rideId) { this.rideId = rideId; }

    public Double getCurrentLatitude() { return currentLatitude; }
    public void setCurrentLatitude(Double currentLatitude) { this.currentLatitude = currentLatitude; }

    public Double getCurrentLongitude() { return currentLongitude; }
    public void setCurrentLongitude(Double currentLongitude) { this.currentLongitude = currentLongitude; }
}
