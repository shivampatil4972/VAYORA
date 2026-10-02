# VAYORA Database Architecture

## Technology Stack
- **Database:** PostgreSQL 16
- **Geospatial Extension:** PostGIS 3.4
- **Migrations:** Flyway
- **ORM:** Spring Data JPA (Hibernate)

## Core Principles
1. **No manual schema changes:** All changes MUST go through Flyway (`V[X]__description.sql`).
2. **UUID Primary Keys:** Used across all tables for distributed uniqueness and security (unguessable IDs).
3. **Auditing:** `created_at` and `updated_at` (where applicable) exist on major entities.
4. **Geospatial Types:** 
   - `GEOGRAPHY(Point, 4326)` for precise earth-surface locations (lat/long coordinates).
   - `GEOMETRY` for bounding boxes, zones, or road routes where 2D Cartesian approximations are faster or required.

## Main Schemas & Tables

### Identity & Profiles
- `users`: Core identity and auth base (RBAC: PASSENGER, DRIVER, ADMIN).
- `passengers`: Passenger-specific profile traits (preferences). References `users(id)`.
- `drivers`: Driver-specific metrics (completed rides, cancellations, license). References `users(id)`.

### Core Mobility
- `vehicles` & `ev_vehicles`: Assets owned by drivers.
- `locations`: Saved passenger/driver locations.
- `routes`: Pre-computed origin-to-destination paths with OSRM geometries.
- `rides`: Driver-created journeys.
- `ride_requests`: Passenger-created demand (zero-result tracking).
- `bookings`: Join table between `rides` and `passengers`.

### Smart AI & Reliability
- `reliability_events`: Logs of late starts, no-shows, etc.
- `ml_predictions`: Stores outputs from AI service (P_CANCEL, P_BOOK, SHAP values).
- `demand_predictions`: AI-generated expected demand heatmaps.
- `recovery_candidates` & `recovery_attempts`: The signature recovery match system.

### Real-time & Telemetry
- `gps_points`: High-volume stream of live tracking points.
- `safety_events`: Output from the SafeRide module (route deviation, SOS).
- `event_logs`: Unified event schema for research metrics (B0-B7 KPI generation).

## Database Initialization
On a fresh install, Flyway automatically runs `V1__init_vayora_schema.sql` on Spring Boot startup.

To access the database locally:
```bash
psql -h localhost -p 5432 -U vayora_user -d vayora
```
