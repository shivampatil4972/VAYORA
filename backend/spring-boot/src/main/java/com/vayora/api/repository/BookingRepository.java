package com.vayora.api.repository;

import com.vayora.api.model.Booking;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface BookingRepository extends JpaRepository<Booking, UUID> {
    List<Booking> findByPassengerId(UUID passengerId);
    List<Booking> findByRideId(UUID rideId);
    List<Booking> findByRideIdAndStatus(UUID rideId, Booking.BookingStatus status);
    boolean existsByRideIdAndPassengerId(UUID rideId, UUID passengerId);
}
