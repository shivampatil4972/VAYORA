package com.vayora.api.model;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "ride_requests")
public class RideRequest {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "passenger_id", nullable = false)
    private UUID passengerId;

    // WKT "POINT(lng lat)" — PostGIS geography
    @Column(name = "origin_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String originGeom;

    @Column(name = "destination_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String destinationGeom;

    @Column(name = "requested_departure_time", nullable = false)
    private Instant requestedDepartureTime;

    @Column(name = "seats_needed", nullable = false)
    private Integer seatsNeeded;

    @Column(name = "is_fulfilled")
    private Boolean isFulfilled = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    public RideRequest() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getPassengerId() { return passengerId; }
    public void setPassengerId(UUID passengerId) { this.passengerId = passengerId; }

    public String getOriginGeom() { return originGeom; }
    public void setOriginGeom(String originGeom) { this.originGeom = originGeom; }

    public String getDestinationGeom() { return destinationGeom; }
    public void setDestinationGeom(String destinationGeom) { this.destinationGeom = destinationGeom; }

    public Instant getRequestedDepartureTime() { return requestedDepartureTime; }
    public void setRequestedDepartureTime(Instant requestedDepartureTime) { this.requestedDepartureTime = requestedDepartureTime; }

    public Integer getSeatsNeeded() { return seatsNeeded; }
    public void setSeatsNeeded(Integer seatsNeeded) { this.seatsNeeded = seatsNeeded; }

    public Boolean getIsFulfilled() { return isFulfilled; }
    public void setIsFulfilled(Boolean isFulfilled) { this.isFulfilled = isFulfilled; }

    public Instant getCreatedAt() { return createdAt; }
}
