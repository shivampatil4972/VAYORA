package com.vayora.api.model;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "bookings")
public class Booking {

    public enum BookingStatus {
        PENDING, CONFIRMED, CANCELLED, COMPLETED, RECOVERED
    }

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "ride_id", nullable = false)
    private UUID rideId;

    @Column(name = "passenger_id", nullable = false)
    private UUID passengerId;

    @Column(name = "seats_booked", nullable = false)
    private Integer seatsBooked;

    @Column(name = "total_price", nullable = false)
    private BigDecimal totalPrice;

    @Enumerated(EnumType.STRING)
    @Column
    private BookingStatus status = BookingStatus.PENDING;

    // WKT "POINT(lng lat)" — PostGIS geography
    @Column(name = "pickup_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String pickupGeom;

    @Column(name = "dropoff_geom", columnDefinition = "geography(Point, 4326)", nullable = false)
    private String dropoffGeom;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public Booking() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getRideId() { return rideId; }
    public void setRideId(UUID rideId) { this.rideId = rideId; }

    public UUID getPassengerId() { return passengerId; }
    public void setPassengerId(UUID passengerId) { this.passengerId = passengerId; }

    public Integer getSeatsBooked() { return seatsBooked; }
    public void setSeatsBooked(Integer seatsBooked) { this.seatsBooked = seatsBooked; }

    public BigDecimal getTotalPrice() { return totalPrice; }
    public void setTotalPrice(BigDecimal totalPrice) { this.totalPrice = totalPrice; }

    public BookingStatus getStatus() { return status; }
    public void setStatus(BookingStatus status) { this.status = status; }

    public String getPickupGeom() { return pickupGeom; }
    public void setPickupGeom(String pickupGeom) { this.pickupGeom = pickupGeom; }

    public String getDropoffGeom() { return dropoffGeom; }
    public void setDropoffGeom(String dropoffGeom) { this.dropoffGeom = dropoffGeom; }

    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
