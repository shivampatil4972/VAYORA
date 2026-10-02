package com.vayora.api.repository;

import com.vayora.api.model.RideRequest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface RideRequestRepository extends JpaRepository<RideRequest, UUID> {
    List<RideRequest> findByPassengerId(UUID passengerId);
    List<RideRequest> findByIsFulfilled(boolean isFulfilled);
}
