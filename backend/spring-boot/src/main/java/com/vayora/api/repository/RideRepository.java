package com.vayora.api.repository;

import com.vayora.api.model.Ride;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Repository
public interface RideRepository extends JpaRepository<Ride, UUID> {

    List<Ride> findByDriverId(UUID driverId);

    List<Ride> findByStatus(Ride.RideStatus status);
    
    long countByStatus(Ride.RideStatus status);

    /**
     * Find rides that match a search by departure time window.
     * Spatial proximity search delegated to PostGIS via native query.
     */
    @Query(value = """
            SELECT * FROM rides
            WHERE status IN ('CREATED', 'OPEN')
              AND available_seats >= :seatsNeeded
              AND departure_time BETWEEN :fromTime AND :toTime
              AND ST_DWithin(origin_geom, ST_SetSRID(ST_MakePoint(:originLng, :originLat), 4326)::geography, :radiusMeters)
              AND ST_DWithin(destination_geom, ST_SetSRID(ST_MakePoint(:destLng, :destLat), 4326)::geography, :radiusMeters)
            ORDER BY departure_time ASC
            """, nativeQuery = true)
    List<Ride> searchRides(
            @Param("originLat") double originLat,
            @Param("originLng") double originLng,
            @Param("destLat") double destLat,
            @Param("destLng") double destLng,
            @Param("seatsNeeded") int seatsNeeded,
            @Param("fromTime") Instant fromTime,
            @Param("toTime") Instant toTime,
            @Param("radiusMeters") double radiusMeters
    );

    List<Ride> findByDriverIdAndStatus(UUID driverId, Ride.RideStatus status);
}
