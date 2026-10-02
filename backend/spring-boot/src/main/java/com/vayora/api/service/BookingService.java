package com.vayora.api.service;

import com.vayora.api.dto.BookRideRequest;
import com.vayora.api.model.Booking;
import com.vayora.api.model.Ride;
import com.vayora.api.repository.BookingRepository;
import com.vayora.api.repository.PassengerRepository;
import com.vayora.api.repository.RideRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class BookingService {

    @Autowired
    private BookingRepository bookingRepository;

    @Autowired
    private RideRepository rideRepository;

    @Autowired
    private PassengerRepository passengerRepository;

    private static String toWkt(double lng, double lat) {
        return String.format("POINT(%f %f)", lng, lat);
    }

    @Transactional
    public Booking createBooking(UUID passengerId, BookRideRequest req) {
        if (!passengerRepository.existsById(passengerId)) {
            throw new RuntimeException("Passenger profile not found.");
        }

        Ride ride = rideRepository.findById(req.getRideId())
                .orElseThrow(() -> new RuntimeException("Ride not found: " + req.getRideId()));

        if (ride.getStatus() == Ride.RideStatus.CANCELLED || ride.getStatus() == Ride.RideStatus.COMPLETED) {
            throw new RuntimeException("Cannot book a ride with status: " + ride.getStatus());
        }

        if (ride.getAvailableSeats() < req.getSeatsNeeded()) {
            throw new RuntimeException("Not enough available seats. Available: " + ride.getAvailableSeats());
        }

        if (bookingRepository.existsByRideIdAndPassengerId(req.getRideId(), passengerId)) {
            throw new RuntimeException("You have already booked this ride.");
        }

        BigDecimal totalPrice = ride.getPricePerSeat().multiply(BigDecimal.valueOf(req.getSeatsNeeded()));

        Booking booking = new Booking();
        booking.setRideId(req.getRideId());
        booking.setPassengerId(passengerId);
        booking.setSeatsBooked(req.getSeatsNeeded());
        booking.setTotalPrice(totalPrice);
        booking.setPickupGeom(toWkt(req.getPickupLng(), req.getPickupLat()));
        booking.setDropoffGeom(toWkt(req.getDropoffLng(), req.getDropoffLat()));
        booking.setStatus(Booking.BookingStatus.CONFIRMED);

        booking = bookingRepository.save(booking);

        // Decrement available seats on the ride
        ride.setAvailableSeats(ride.getAvailableSeats() - req.getSeatsNeeded());
        if (ride.getAvailableSeats() == 0) {
            ride.setStatus(Ride.RideStatus.FULL);
        } else if (ride.getStatus() == Ride.RideStatus.CREATED) {
            ride.setStatus(Ride.RideStatus.OPEN);
        }
        rideRepository.save(ride);

        return booking;
    }

    public List<Booking> getMyBookings(UUID passengerId) {
        return bookingRepository.findByPassengerId(passengerId);
    }

    public Booking getBookingById(UUID bookingId, UUID passengerId) {
        Booking booking = bookingRepository.findById(bookingId)
                .orElseThrow(() -> new RuntimeException("Booking not found: " + bookingId));
        if (!booking.getPassengerId().equals(passengerId)) {
            throw new RuntimeException("Access denied: booking does not belong to you.");
        }
        return booking;
    }

    @Transactional
    public Booking cancelBooking(UUID bookingId, UUID passengerId) {
        Booking booking = getBookingById(bookingId, passengerId);

        if (booking.getStatus() == Booking.BookingStatus.CANCELLED) {
            throw new RuntimeException("Booking is already cancelled.");
        }
        if (booking.getStatus() == Booking.BookingStatus.COMPLETED) {
            throw new RuntimeException("Cannot cancel a completed booking.");
        }

        booking.setStatus(Booking.BookingStatus.CANCELLED);
        bookingRepository.save(booking);

        // Restore seats on ride
        Ride ride = rideRepository.findById(booking.getRideId()).orElse(null);
        if (ride != null && ride.getStatus() != Ride.RideStatus.CANCELLED) {
            ride.setAvailableSeats(ride.getAvailableSeats() + booking.getSeatsBooked());
            if (ride.getStatus() == Ride.RideStatus.FULL) {
                ride.setStatus(Ride.RideStatus.OPEN);
            }
            rideRepository.save(ride);
        }

        return booking;
    }

    public List<Booking> getRideBookings(UUID rideId, UUID driverId) {
        // Driver can see all bookings for their ride
        return bookingRepository.findByRideId(rideId);
    }
}
