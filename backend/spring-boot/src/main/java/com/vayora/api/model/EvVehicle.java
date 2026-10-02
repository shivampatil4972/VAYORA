package com.vayora.api.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "ev_vehicles")
public class EvVehicle {

    @Id
    @Column(name = "vehicle_id")
    private UUID vehicleId;

    @Column(name = "battery_capacity_kwh", nullable = false)
    private BigDecimal batteryCapacityKwh;

    @Column(name = "consumption_per_km_kwh", nullable = false)
    private BigDecimal consumptionPerKmKwh;

    @Column(name = "current_soc_percentage")
    private BigDecimal currentSocPercentage;

    @Column(name = "supported_charger_types", columnDefinition = "text[]")
    private String[] supportedChargerTypes;

    public EvVehicle() {}

    public UUID getVehicleId() { return vehicleId; }
    public void setVehicleId(UUID vehicleId) { this.vehicleId = vehicleId; }

    public BigDecimal getBatteryCapacityKwh() { return batteryCapacityKwh; }
    public void setBatteryCapacityKwh(BigDecimal batteryCapacityKwh) { this.batteryCapacityKwh = batteryCapacityKwh; }

    public BigDecimal getConsumptionPerKmKwh() { return consumptionPerKmKwh; }
    public void setConsumptionPerKmKwh(BigDecimal consumptionPerKmKwh) { this.consumptionPerKmKwh = consumptionPerKmKwh; }

    public BigDecimal getCurrentSocPercentage() { return currentSocPercentage; }
    public void setCurrentSocPercentage(BigDecimal currentSocPercentage) { this.currentSocPercentage = currentSocPercentage; }

    public String[] getSupportedChargerTypes() { return supportedChargerTypes; }
    public void setSupportedChargerTypes(String[] supportedChargerTypes) { this.supportedChargerTypes = supportedChargerTypes; }
}
