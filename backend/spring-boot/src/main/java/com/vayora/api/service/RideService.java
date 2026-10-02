package com.vayora.api.service;

import com.vayora.api.dto.CreateRideRequest;
import com.vayora.api.dto.RideSearchRequest;
import com.vayora.api.model.Ride;
import com.vayora.api.model.RideRequest;
import com.vayora.api.repository.DriverRepository;
import com.vayora.api.repository.RideRepository;
import com.vayora.api.repository.RideRequestRepository;
import com.vayora.api.repository.VehicleRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;

@Service
public class RideService {

    @Autowired
    private RideRepository rideRepository;

    @Autowired
    private RideRequestRepository rideRequestRepository;

    @Autowired
    private DriverRepository driverRepository;

    @Autowired
    private VehicleRepository vehicleRepository;

    // Helper: convert lat/lng to PostGIS WKT point string
    private static String toWkt(double lng, double lat) {
        return String.format("POINT(%f %f)", lng, lat);
    }

    @Transactional
    public Ride createRide(UUID driverId, CreateRideRequest req) {
        if (!driverRepository.existsById(driverId)) {
            throw new RuntimeException("Driver profile not found.");
        }
        var vehicle = vehicleRepository.findById(req.getVehicleId())
                .orElseThrow(() -> new RuntimeException("Vehicle not found: " + req.getVehicleId()));
        if (!vehicle.getDriverId().equals(driverId)) {
            throw new RuntimeException("Vehicle does not belong to you.");
        }

        Ride ride = new Ride();
        ride.setDriverId(driverId);
        ride.setVehicleId(req.getVehicleId());
        ride.setOriginAddress(req.getOriginAddress());
        ride.setDestinationAddress(req.getDestinationAddress());
        ride.setOriginGeom(toWkt(req.getOriginLng(), req.getOriginLat()));
        ride.setDestinationGeom(toWkt(req.getDestinationLng(), req.getDestinationLat()));
        ride.setDepartureTime(req.getDepartureTime());
        ride.setAvailableSeats(req.getAvailableSeats());
        ride.setPricePerSeat(req.getPricePerSeat());
        ride.setMaxDetourMinutes(req.getMaxDetourMinutes() != null ? req.getMaxDetourMinutes() : 20);
        ride.setStatus(Ride.RideStatus.CREATED);

        return rideRepository.save(ride);
    }

    /**
     * B0 baseline search: spatial + temporal + seat filter.
     * Also logs a RideRequest for demand intelligence tracking.
     */
    @Transactional
    public List<Ride> searchRides(UUID passengerId, RideSearchRequest req) {
        var fromTime = req.getDepartureTime().minus(req.getToleranceHours(), ChronoUnit.HOURS);
        var toTime = req.getDepartureTime().plus(req.getToleranceHours(), ChronoUnit.HOURS);

        List<Ride> results = rideRepository.searchRides(
                req.getOriginLat(), req.getOriginLng(),
                req.getDestinationLat(), req.getDestinationLng(),
                req.getSeatsNeeded(),
                fromTime, toTime,
                req.getRadiusMeters()
        );

        // Log the ride request for DemandAI (zero-result tracking)
        RideRequest rideRequest = new RideRequest();
        rideRequest.setPassengerId(passengerId);
        rideRequest.setOriginGeom(toWkt(req.getOriginLng(), req.getOriginLat()));
        rideRequest.setDestinationGeom(toWkt(req.getDestinationLng(), req.getDestinationLat()));
        rideRequest.setRequestedDepartureTime(req.getDepartureTime());
        rideRequest.setSeatsNeeded(req.getSeatsNeeded());
        rideRequest.setIsFulfilled(!results.isEmpty());
        rideRequestRepository.save(rideRequest);

        return results;
    }

    public Ride getRideById(UUID rideId) {
        return rideRepository.findById(rideId)
                .orElseThrow(() -> new RuntimeException("Ride not found: " + rideId));
    }

    public List<Ride> getMyRides(UUID driverId) {
        return rideRepository.findByDriverId(driverId);
    }

    @Transactional
    public Ride updateRideStatus(UUID rideId, UUID driverId, Ride.RideStatus newStatus) {
        Ride ride = getRideById(rideId);
        if (!ride.getDriverId().equals(driverId)) {
            throw new RuntimeException("Access denied: ride does not belong to you.");
        }
        ride.setStatus(newStatus);
        return rideRepository.save(ride);
    }

    @Transactional
    public void cancelRide(UUID rideId, UUID driverId) {
        updateRideStatus(rideId, driverId, Ride.RideStatus.CANCELLED);
    }
}
