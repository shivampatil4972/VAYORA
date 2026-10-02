package com.vayora.api.dto;

import jakarta.validation.constraints.*;

public class VehicleRequest {

    @NotBlank
    private String make;

    @NotBlank
    private String model;

    @NotBlank
    private String licensePlate;

    @NotNull
    @Min(1)
    @Max(8)
    private Integer totalSeats;

    private String luggageCapacity; // SMALL, MEDIUM, LARGE

    private Boolean isWheelchairAccessible = false;
    private Boolean allowsPets = false;
    private Boolean isEv = false;

    // EV fields (only used if isEv == true)
    private java.math.BigDecimal batteryCapacityKwh;
    private java.math.BigDecimal consumptionPerKmKwh;
    private java.math.BigDecimal currentSocPercentage;
    private String[] supportedChargerTypes;

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
    public void setIsWheelchairAccessible(Boolean isWheelchairAccessible) { this.isWheelchairAccessible = isWheelchairAccessible; }

    public Boolean getAllowsPets() { return allowsPets; }
    public void setAllowsPets(Boolean allowsPets) { this.allowsPets = allowsPets; }

    public Boolean getIsEv() { return isEv; }
    public void setIsEv(Boolean isEv) { this.isEv = isEv; }

    public java.math.BigDecimal getBatteryCapacityKwh() { return batteryCapacityKwh; }
    public void setBatteryCapacityKwh(java.math.BigDecimal batteryCapacityKwh) { this.batteryCapacityKwh = batteryCapacityKwh; }

    public java.math.BigDecimal getConsumptionPerKmKwh() { return consumptionPerKmKwh; }
    public void setConsumptionPerKmKwh(java.math.BigDecimal consumptionPerKmKwh) { this.consumptionPerKmKwh = consumptionPerKmKwh; }

    public java.math.BigDecimal getCurrentSocPercentage() { return currentSocPercentage; }
    public void setCurrentSocPercentage(java.math.BigDecimal currentSocPercentage) { this.currentSocPercentage = currentSocPercentage; }

    public String[] getSupportedChargerTypes() { return supportedChargerTypes; }
    public void setSupportedChargerTypes(String[] supportedChargerTypes) { this.supportedChargerTypes = supportedChargerTypes; }
}
