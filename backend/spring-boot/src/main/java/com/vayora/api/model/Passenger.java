package com.vayora.api.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "passengers")
public class Passenger {

    @Id
    private UUID id;

    @Column(name = "travel_preferences", columnDefinition = "jsonb")
    private String travelPreferences = "{}";

    @Column(name = "wheelchair_required")
    private Boolean wheelchairRequired = false;

    @Column(name = "allows_pets")
    private Boolean allowsPets = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public Passenger() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getTravelPreferences() { return travelPreferences; }
    public void setTravelPreferences(String travelPreferences) { this.travelPreferences = travelPreferences; }

    public Boolean getWheelchairRequired() { return wheelchairRequired; }
    public void setWheelchairRequired(Boolean wheelchairRequired) { this.wheelchairRequired = wheelchairRequired; }

    public Boolean getAllowsPets() { return allowsPets; }
    public void setAllowsPets(Boolean allowsPets) { this.allowsPets = allowsPets; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
