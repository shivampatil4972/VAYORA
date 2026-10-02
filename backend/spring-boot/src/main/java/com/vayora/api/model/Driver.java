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
@Table(name = "drivers")
public class Driver {

    @Id
    private UUID id;

    @Column(name = "verification_status")
    private String verificationStatus = "PENDING";

    @Column(name = "driver_license_number", unique = true)
    private String driverLicenseNumber;

    @Column(name = "completed_rides")
    private Integer completedRides = 0;

    @Column(name = "cancellations")
    private Integer cancellations = 0;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private Instant updatedAt;

    public Driver() {}

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getVerificationStatus() { return verificationStatus; }
    public void setVerificationStatus(String verificationStatus) { this.verificationStatus = verificationStatus; }

    public String getDriverLicenseNumber() { return driverLicenseNumber; }
    public void setDriverLicenseNumber(String driverLicenseNumber) { this.driverLicenseNumber = driverLicenseNumber; }

    public Integer getCompletedRides() { return completedRides; }
    public void setCompletedRides(Integer completedRides) { this.completedRides = completedRides; }

    public Integer getCancellations() { return cancellations; }
    public void setCancellations(Integer cancellations) { this.cancellations = cancellations; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
