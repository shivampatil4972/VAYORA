package com.vayora.api.service;

import com.vayora.api.dto.VehicleRequest;
import com.vayora.api.model.EvVehicle;
import com.vayora.api.model.Vehicle;
import com.vayora.api.repository.DriverRepository;
import com.vayora.api.repository.EvVehicleRepository;
import com.vayora.api.repository.VehicleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class VehicleService {

    @Autowired
    private VehicleRepository vehicleRepository;

    @Autowired
    private EvVehicleRepository evVehicleRepository;

    @Autowired
    private DriverRepository driverRepository;

    @Transactional
    public Vehicle registerVehicle(UUID driverId, VehicleRequest req) {
        if (!driverRepository.existsById(driverId)) {
            throw new RuntimeException("Driver profile not found for user: " + driverId);
        }
        if (vehicleRepository.existsByLicensePlate(req.getLicensePlate())) {
            throw new RuntimeException("A vehicle with license plate '" + req.getLicensePlate() + "' already exists.");
        }

        Vehicle vehicle = new Vehicle();
        vehicle.setDriverId(driverId);
        vehicle.setMake(req.getMake());
        vehicle.setModel(req.getModel());
        vehicle.setLicensePlate(req.getLicensePlate().toUpperCase().trim());
        vehicle.setTotalSeats(req.getTotalSeats());
        vehicle.setLuggageCapacity(req.getLuggageCapacity());
        vehicle.setIsWheelchairAccessible(req.getIsWheelchairAccessible() != null ? req.getIsWheelchairAccessible() : false);
        vehicle.setAllowsPets(req.getAllowsPets() != null ? req.getAllowsPets() : false);
        vehicle.setIsEv(req.getIsEv() != null ? req.getIsEv() : false);

        vehicle = vehicleRepository.save(vehicle);

        // If this is an EV, save additional EV data
        if (Boolean.TRUE.equals(vehicle.getIsEv()) && req.getBatteryCapacityKwh() != null) {
            EvVehicle ev = new EvVehicle();
            ev.setVehicleId(vehicle.getId());
            ev.setBatteryCapacityKwh(req.getBatteryCapacityKwh());
            ev.setConsumptionPerKmKwh(req.getConsumptionPerKmKwh());
            ev.setCurrentSocPercentage(req.getCurrentSocPercentage());
            ev.setSupportedChargerTypes(req.getSupportedChargerTypes());
            evVehicleRepository.save(ev);
        }

        return vehicle;
    }

    public List<Vehicle> getMyVehicles(UUID driverId) {
        return vehicleRepository.findByDriverId(driverId);
    }

    public Vehicle getVehicleById(UUID vehicleId, UUID driverId) {
        Vehicle vehicle = vehicleRepository.findById(vehicleId)
                .orElseThrow(() -> new RuntimeException("Vehicle not found: " + vehicleId));
        if (!vehicle.getDriverId().equals(driverId)) {
            throw new RuntimeException("Access denied: vehicle does not belong to you.");
        }
        return vehicle;
    }

    @Transactional
    public void deleteVehicle(UUID vehicleId, UUID driverId) {
        Vehicle vehicle = getVehicleById(vehicleId, driverId);
        vehicleRepository.delete(vehicle);
    }
}
