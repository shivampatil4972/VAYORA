package com.vayora.api.controller;

import com.vayora.api.dto.BookRideRequest;
import com.vayora.api.model.Booking;
import com.vayora.api.security.services.UserDetailsImpl;
import com.vayora.api.service.BookingService;
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
@RequestMapping("/api/bookings")
public class BookingController {

    @Autowired
    private BookingService bookingService;

    /**
     * POST /api/bookings
     * Passenger books a ride.
     */
    @PreAuthorize("hasRole('PASSENGER')")
    @PostMapping
    public ResponseEntity<?> bookRide(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @Valid @RequestBody BookRideRequest request) {
        try {
            Booking booking = bookingService.createBooking(userDetails.getId(), request);
            return ResponseEntity.ok(booking);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * GET /api/bookings/my
     * Passenger views their own bookings.
     */
    @PreAuthorize("hasRole('PASSENGER')")
    @GetMapping("/my")
    public ResponseEntity<List<Booking>> getMyBookings(
            @AuthenticationPrincipal UserDetailsImpl userDetails) {
        return ResponseEntity.ok(bookingService.getMyBookings(userDetails.getId()));
    }

    /**
     * GET /api/bookings/{id}
     * Passenger views a specific booking.
     */
    @PreAuthorize("hasRole('PASSENGER')")
    @GetMapping("/{id}")
    public ResponseEntity<?> getBooking(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id) {
        try {
            Booking booking = bookingService.getBookingById(id, userDetails.getId());
            return ResponseEntity.ok(booking);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * DELETE /api/bookings/{id}/cancel
     * Passenger cancels their booking.
     */
    @PreAuthorize("hasRole('PASSENGER')")
    @DeleteMapping("/{id}/cancel")
    public ResponseEntity<?> cancelBooking(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID id) {
        try {
            Booking booking = bookingService.cancelBooking(id, userDetails.getId());
            return ResponseEntity.ok(Map.of("message", "Booking cancelled.", "booking", booking));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * GET /api/bookings/ride/{rideId}
     * Driver views all bookings for one of their rides.
     */
    @PreAuthorize("hasRole('DRIVER')")
    @GetMapping("/ride/{rideId}")
    public ResponseEntity<?> getRideBookings(
            @AuthenticationPrincipal UserDetailsImpl userDetails,
            @PathVariable UUID rideId) {
        try {
            List<Booking> bookings = bookingService.getRideBookings(rideId, userDetails.getId());
            return ResponseEntity.ok(bookings);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
}
