package com.vayora.api.controller;

import com.vayora.api.dto.CreateRideRequest;
import com.vayora.api.dto.RideSearchRequest;
import com.vayora.api.model.Ride;
import com.vayora.api.security.services.UserDetailsImpl;
import com.vayora.api.service.RideService;
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
@RequestMapping("/api/rides")
public class RideController {

    @Autowired
    private RideService rideService;

    /**
     * POST /api/rides
     * Driver creates a new ride.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @PostMapping
    public ResponseEntity<?> createRide(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @Valid @RequestBody CreateRideRequest request) {
        try {
            Ride ride = rideService.createRide(userDetails.getId(), request);
            return ResponseEntity.ok(ride);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * POST /api/rides/search
     * Passenger searches for available rides (B0 baseline: spatial + temporal + seat filter).
     */
    @PreAuthorize("hasRole('PASSENGER')")
    @PostMapping("/search")
    public ResponseEntity<?> searchRides(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @Valid @RequestBody RideSearchRequest request) {
        try {
            List<Ride> results = rideService.searchRides(userDetails.getId(), request);
            return ResponseEntity.ok(Map.of(
                    "results", results,
                    "count", results.size()
            ));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * GET /api/rides/my
     * Driver gets their own rides.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @GetMapping("/my")
    public ResponseEntity<List<Ride>> getMyRides(
            @AuthenticationPrincipal UserDetailsImpl userDetails) {
        return ResponseEntity.ok(rideService.getMyRides(userDetails.getId()));
    }

    /**
     * GET /api/rides/{id}
     * Get a specific ride (authenticated users).
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getRide(@PathVariable UUID id) {
        try {
            return ResponseEntity.ok(rideService.getRideById(id));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * PATCH /api/rides/{id}/status
     * Driver updates ride status (e.g., OPEN → STARTED, STARTED → COMPLETED).
     */
    @PreAuthorize("hasRole('DRIVER')")
    @PatchMapping("/{id}/status")
    public ResponseEntity<?> updateRideStatus(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id,
            @RequestBody Map<String, String> body) {
        try {
            Ride.RideStatus newStatus = Ride.RideStatus.valueOf(body.get("status"));
            Ride ride = rideService.updateRideStatus(id, userDetails.getId(), newStatus);
            return ResponseEntity.ok(ride);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", "Invalid status value."));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * DELETE /api/rides/{id}/cancel
     * Driver cancels their ride.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @DeleteMapping("/{id}/cancel")
    public ResponseEntity<?> cancelRide(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id) {
        try {
            rideService.cancelRide(id, userDetails.getId());
            return ResponseEntity.ok(Map.of("message", "Ride cancelled successfully."));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
}
