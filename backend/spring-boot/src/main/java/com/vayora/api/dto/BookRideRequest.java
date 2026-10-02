package com.vayora.api.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.util.UUID;

public class BookRideRequest {

    @NotNull
    private UUID rideId;

    @NotNull
    @Min(1)
    private Integer seatsNeeded;

    // Pickup coordinates (may differ from ride origin for flexible pickup)
    @NotNull @DecimalMin("-90.0") @DecimalMax("90.0")
    private Double pickupLat;

    @NotNull @DecimalMin("-180.0") @DecimalMax("180.0")
    private Double pickupLng;

    @NotNull @DecimalMin("-90.0") @DecimalMax("90.0")
    private Double dropoffLat;

    @NotNull @DecimalMin("-180.0") @DecimalMax("180.0")
    private Double dropoffLng;

    public UUID getRideId() { return rideId; }
    public void setRideId(UUID rideId) { this.rideId = rideId; }

    public Integer getSeatsNeeded() { return seatsNeeded; }
    public void setSeatsNeeded(Integer seatsNeeded) { this.seatsNeeded = seatsNeeded; }

    public Double getPickupLat() { return pickupLat; }
    public void setPickupLat(Double pickupLat) { this.pickupLat = pickupLat; }

    public Double getPickupLng() { return pickupLng; }
    public void setPickupLng(Double pickupLng) { this.pickupLng = pickupLng; }

    public Double getDropoffLat() { return dropoffLat; }
    public void setDropoffLat(Double dropoffLat) { this.dropoffLat = dropoffLat; }

    public Double getDropoffLng() { return dropoffLng; }
    public void setDropoffLng(Double dropoffLng) { this.dropoffLng = dropoffLng; }
}
