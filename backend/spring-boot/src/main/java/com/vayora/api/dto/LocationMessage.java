package com.vayora.api.dto;

import java.time.Instant;
import java.util.UUID;

public class LocationMessage {
    private UUID rideId;
    private UUID driverId;
    private double latitude;
    private double longitude;
    private double speedKmph;
    private double heading; // 0-360 degrees
    private Instant timestamp;

    public LocationMessage() {
    }

    public UUID getRideId() { return rideId; }
    public void setRideId(UUID rideId) { this.rideId = rideId; }

    public UUID getDriverId() { return driverId; }
    public void setDriverId(UUID driverId) { this.driverId = driverId; }

    public double getLatitude() { return latitude; }
    public void setLatitude(double latitude) { this.latitude = latitude; }

    public double getLongitude() { return longitude; }
    public void setLongitude(double longitude) { this.longitude = longitude; }

    public double getSpeedKmph() { return speedKmph; }
    public void setSpeedKmph(double speedKmph) { this.speedKmph = speedKmph; }

    public double getHeading() { return heading; }
    public void setHeading(double heading) { this.heading = heading; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
