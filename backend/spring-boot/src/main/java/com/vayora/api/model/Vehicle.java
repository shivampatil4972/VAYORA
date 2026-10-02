package com.vayora.api.model;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "vehicles")
public class Vehicle {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "driver_id", nullable = false)
    private UUID driverId;

    @Column(nullable = false)
    private String make;

    @Column(nullable = false)
    private String model;

    @Column(name = "license_plate", unique = true, nullable = false)
    private String licensePlate;

    @Column(name = "total_seats", nullable = false)
    private Integer totalSeats;

    @Column(name = "luggage_capacity")
    private String luggageCapacity; // SMALL, MEDIUM, LARGE

    @Column(name = "is_wheelchair_accessible")
    private Boolean isWheelchairAccessible = false;

    @Column(name = "allows_pets")
    private Boolean allowsPets = false;

    @Column(name = "is_ev")
    private Boolean isEv = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public Vehicle() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getDriverId() { return driverId; }
    public void setDriverId(UUID driverId) { this.driverId = driverId; }

    public String getMake() { return make; }
    public void setMake(String make) { this.make = make; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }

    public String getLicensePlate() { return licensePlate; }
    public void setLicensePlate(String licensePlate) { this.licensePlate = licensePlate; }

    public Integer getTotalSeats() { return totalSeats; }
    public void setTotalSeats(Integer totalSeats) { this.totalSeats = totalSeats; }

    public String getLuggageCapacity() { return luggageCapacity; }
    public void setLuggageCapacity(String luggageCapacity) { this.luggageCapacity = luggageCapacity; }

    public Boolean getIsWheelchairAccessible() { return isWheelchairAccessible; }
    public void setIsWheelchairAccessible(Boolean wheelchairAccessible) { isWheelchairAccessible = wheelchairAccessible; }

    public Boolean getAllowsPets() { return allowsPets; }
    public void setAllowsPets(Boolean allowsPets) { this.allowsPets = allowsPets; }

    public Boolean getIsEv() { return isEv; }
    public void setIsEv(Boolean isEv) { this.isEv = isEv; }

    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}
