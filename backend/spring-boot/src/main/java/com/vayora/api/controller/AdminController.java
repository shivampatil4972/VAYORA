package com.vayora.api.controller;

import com.vayora.api.dto.AdminDashboardStats;
import com.vayora.api.model.Ride;
import com.vayora.api.repository.*;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    private final UserRepository userRepository;
    private final DriverRepository driverRepository;
    private final PassengerRepository passengerRepository;
    private final RideRepository rideRepository;
    private final BookingRepository bookingRepository;

    public AdminController(UserRepository userRepository,
                           DriverRepository driverRepository,
                           PassengerRepository passengerRepository,
                           RideRepository rideRepository,
                           BookingRepository bookingRepository) {
        this.userRepository = userRepository;
        this.driverRepository = driverRepository;
        this.passengerRepository = passengerRepository;
        this.rideRepository = rideRepository;
        this.bookingRepository = bookingRepository;
    }

    @GetMapping("/dashboard/stats")
    public ResponseEntity<AdminDashboardStats> getDashboardStats() {
        AdminDashboardStats stats = new AdminDashboardStats();
        
        stats.setTotalUsers(userRepository.count());
        stats.setTotalDrivers(driverRepository.count());
        stats.setTotalPassengers(passengerRepository.count());
        
        stats.setTotalRides(rideRepository.count());
        stats.setActiveRides(rideRepository.countByStatus(Ride.RideStatus.IN_PROGRESS));
        
        stats.setTotalBookings(bookingRepository.count());

        // In a full implementation, we'd query the AI Service or a local replica for simulation metrics
        stats.setAiMetrics(Map.of(
                "smartmatch_baseline", "B1/B2 Enabled",
                "optimization_baseline", "B3 Enabled",
                "reliability_baseline", "B4 Enabled",
                "demand_baseline", "B5 Enabled",
                "recovery_baseline", "B6 Enabled",
                "ev_feasibility_baseline", "B7 Enabled"
        ));

        return ResponseEntity.ok(stats);
    }
}
