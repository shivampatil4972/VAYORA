package com.vayora.api.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.Instant;

public class CreateRideRequest {

    @NotNull
    private java.util.UUID vehicleId;

    @NotBlank
    private String originAddress;

    @NotBlank
    private String destinationAddress;

    @NotNull
    @DecimalMin("-90.0") @DecimalMax("90.0")
    private Double originLat;

    @NotNull
    @DecimalMin("-180.0") @DecimalMax("180.0")
    private Double originLng;

    @NotNull
    @DecimalMin("-90.0") @DecimalMax("90.0")
    private Double destinationLat;

    @NotNull
    @DecimalMin("-180.0") @DecimalMax("180.0")
    private Double destinationLng;

    @NotNull
    private Instant departureTime;

    @NotNull
    @Min(1)
    private Integer availableSeats;

    @NotNull
    @DecimalMin("0.0")
    private BigDecimal pricePerSeat;

    private Integer maxDetourMinutes = 20;

    // Getters & setters
    public java.util.UUID getVehicleId() { return vehicleId; }
    public void setVehicleId(java.util.UUID vehicleId) { this.vehicleId = vehicleId; }

    public String getOriginAddress() { return originAddress; }
    public void setOriginAddress(String originAddress) { this.originAddress = originAddress; }

    public String getDestinationAddress() { return destinationAddress; }
    public void setDestinationAddress(String destinationAddress) { this.destinationAddress = destinationAddress; }

    public Double getOriginLat() { return originLat; }
    public void setOriginLat(Double originLat) { this.originLat = originLat; }

    public Double getOriginLng() { return originLng; }
    public void setOriginLng(Double originLng) { this.originLng = originLng; }

    public Double getDestinationLat() { return destinationLat; }
    public void setDestinationLat(Double destinationLat) { this.destinationLat = destinationLat; }

    public Double getDestinationLng() { return destinationLng; }
    public void setDestinationLng(Double destinationLng) { this.destinationLng = destinationLng; }

    public Instant getDepartureTime() { return departureTime; }
    public void setDepartureTime(Instant departureTime) { this.departureTime = departureTime; }

    public Integer getAvailableSeats() { return availableSeats; }
    public void setAvailableSeats(Integer availableSeats) { this.availableSeats = availableSeats; }

    public BigDecimal getPricePerSeat() { return pricePerSeat; }
    public void setPricePerSeat(BigDecimal pricePerSeat) { this.pricePerSeat = pricePerSeat; }

    public Integer getMaxDetourMinutes() { return maxDetourMinutes; }
    public void setMaxDetourMinutes(Integer maxDetourMinutes) { this.maxDetourMinutes = maxDetourMinutes; }
}
