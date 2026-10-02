package com.vayora.api.model;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "rides")
public class Ride {

    public enum RideStatus {
        CREATED, OPEN, FULL, STARTED, COMPLETED, CANCELLED
    }

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "driver_id", nullable = false)
    private UUID driverId;

    @Column(name = "vehicle_id", nullable = false)
    private UUID vehicleId;

    @Column(name = "route_id")
    private UUID routeId;

    @Column(name = "origin_address", nullable = false)
    private String originAddress;

    @Column(name = "destination_address", nullable = false)
    private String destinationAddress;

    // Stored as "POINT(lng lat)" WKT — PostGIS geography
    @Column(name = "origin_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String originGeom;

    @Column(name = "destination_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String destinationGeom;

    @Column(name = "departure_time", nullable = false)
    private Instant departureTime;

    @Column(name = "available_seats", nullable = false)
    private Integer availableSeats;

    @Column(name = "price_per_seat", nullable = false)
    private java.math.BigDecimal pricePerSeat;

    @Column(name = "max_detour_minutes")
    private Integer maxDetourMinutes = 20;

    @Enumerated(EnumType.STRING)
    @Column
    private RideStatus status = RideStatus.CREATED;

    @Column(name = "journey_confidence_score")
    private java.math.BigDecimal journeyConfidenceScore;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @org.hibernate.annotations.UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public Ride() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getDriverId() { return driverId; }
    public void setDriverId(UUID driverId) { this.driverId = driverId; }

    public UUID getVehicleId() { return vehicleId; }
    public void setVehicleId(UUID vehicleId) { this.vehicleId = vehicleId; }

    public UUID getRouteId() { return routeId; }
    public void setRouteId(UUID routeId) { this.routeId = routeId; }

    public String getOriginAddress() { return originAddress; }
    public void setOriginAddress(String originAddress) { this.originAddress = originAddress; }

    public String getDestinationAddress() { return destinationAddress; }
    public void setDestinationAddress(String destinationAddress) { this.destinationAddress = destinationAddress; }

    public String getOriginGeom() { return originGeom; }
    public void setOriginGeom(String originGeom) { this.originGeom = originGeom; }

    public String getDestinationGeom() { return destinationGeom; }
    public void setDestinationGeom(String destinationGeom) { this.destinationGeom = destinationGeom; }

    public Instant getDepartureTime() { return departureTime; }
    public void setDepartureTime(Instant departureTime) { this.departureTime = departureTime; }

    public Integer getAvailableSeats() { return availableSeats; }
    public void setAvailableSeats(Integer availableSeats) { this.availableSeats = availableSeats; }

    public java.math.BigDecimal getPricePerSeat() { return pricePerSeat; }
    public void setPricePerSeat(java.math.BigDecimal pricePerSeat) { this.pricePerSeat = pricePerSeat; }

    public Integer getMaxDetourMinutes() { return maxDetourMinutes; }
    public void setMaxDetourMinutes(Integer maxDetourMinutes) { this.maxDetourMinutes = maxDetourMinutes; }

    public RideStatus getStatus() { return status; }
    public void setStatus(RideStatus status) { this.status = status; }

    public java.math.BigDecimal getJourneyConfidenceScore() { return journeyConfidenceScore; }
    public void setJourneyConfidenceScore(java.math.BigDecimal journeyConfidenceScore) { this.journeyConfidenceScore = journeyConfidenceScore; }

    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
