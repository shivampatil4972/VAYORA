package com.vayora.api.controller;

import com.vayora.api.dto.VehicleRequest;
import com.vayora.api.model.Vehicle;
import com.vayora.api.security.services.UserDetailsImpl;
import com.vayora.api.service.VehicleService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/vehicles")
public class VehicleController {

    @Autowired
    private VehicleService vehicleService;

    /**
     * POST /api/vehicles
     * Register a new vehicle. Driver only.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @PostMapping
    public ResponseEntity<?> registerVehicle(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @Valid @RequestBody VehicleRequest request) {
        try {
            Vehicle vehicle = vehicleService.registerVehicle(userDetails.getId(), request);
            return ResponseEntity.ok(vehicle);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * GET /api/vehicles/my
     * Get all vehicles registered by the current driver.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @GetMapping("/my")
    public ResponseEntity<List<Vehicle>> getMyVehicles(
            @AuthenticationPrincipal UserDetailsImpl userDetails) {
        return ResponseEntity.ok(vehicleService.getMyVehicles(userDetails.getId()));
    }

    /**
     * GET /api/vehicles/{id}
     * Get a specific vehicle owned by the current driver.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @GetMapping("/{id}")
    public ResponseEntity<?> getVehicle(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id) {
        try {
            Vehicle vehicle = vehicleService.getVehicleById(id, userDetails.getId());
            return ResponseEntity.ok(vehicle);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * DELETE /api/vehicles/{id}
     * Remove a vehicle. Driver only.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteVehicle(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id) {
        try {
            vehicleService.deleteVehicle(id, userDetails.getId());
            return ResponseEntity.ok(Map.of("message", "Vehicle deleted successfully."));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
}
