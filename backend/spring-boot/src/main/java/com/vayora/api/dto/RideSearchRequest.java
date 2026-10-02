package com.vayora.api.dto;

import jakarta.validation.constraints.*;
import java.time.Instant;

public class RideSearchRequest {

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
    private Integer seatsNeeded;

    /** Search radius in meters. Default 5 km. */
    private Double radiusMeters = 5000.0;

    /** Window: rides departing within ± toleranceHours of departureTime */
    private Integer toleranceHours = 2;

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

    public Integer getSeatsNeeded() { return seatsNeeded; }
    public void setSeatsNeeded(Integer seatsNeeded) { this.seatsNeeded = seatsNeeded; }

    public Double getRadiusMeters() { return radiusMeters; }
    public void setRadiusMeters(Double radiusMeters) { this.radiusMeters = radiusMeters; }

    public Integer getToleranceHours() { return toleranceHours; }
    public void setToleranceHours(Integer toleranceHours) { this.toleranceHours = toleranceHours; }
}
