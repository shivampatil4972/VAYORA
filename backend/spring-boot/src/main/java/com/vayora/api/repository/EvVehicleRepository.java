package com.vayora.api.repository;

import com.vayora.api.model.EvVehicle;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface EvVehicleRepository extends JpaRepository<EvVehicle, UUID> {
}
