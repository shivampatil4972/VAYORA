-- ============================================================
-- VAYORA V1 Schema Initialization
-- Flyway Migration Script
-- ============================================================

-- Ensure PostGIS is available (handled in init script, but good to ensure logic)
-- Extension creation is typically done by superuser in 00_extensions.sql

-- 1. ENUMS
CREATE TYPE role_type AS ENUM ('PASSENGER', 'DRIVER', 'ADMIN');
CREATE TYPE ride_status AS ENUM ('CREATED', 'OPEN', 'FULL', 'STARTED', 'COMPLETED', 'CANCELLED');
CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'RECOVERED');
CREATE TYPE safety_event_type AS ENUM ('ROUTE_DEVIATION', 'LONG_STOP', 'UNEXPECTED_TERMINATION', 'SOS');
CREATE TYPE recovery_status AS ENUM ('PENDING', 'OFFERED', 'ACCEPTED', 'REJECTED', 'FAILED');

-- 2. USERS & IDENTITY
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    role role_type NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    refresh_token VARCHAR(255),
    refresh_token_expiry TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE passengers (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    travel_preferences JSONB DEFAULT '{}',
    wheelchair_required BOOLEAN DEFAULT FALSE,
    allows_pets BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE drivers (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    verification_status VARCHAR(50) DEFAULT 'PENDING',
    driver_license_number VARCHAR(100) UNIQUE,
    completed_rides INT DEFAULT 0,
    cancellations INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. VEHICLES & EV
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    license_plate VARCHAR(50) UNIQUE NOT NULL,
    total_seats INT NOT NULL CHECK (total_seats > 0),
    luggage_capacity VARCHAR(50), -- SMALL, MEDIUM, LARGE
    is_wheelchair_accessible BOOLEAN DEFAULT FALSE,
    allows_pets BOOLEAN DEFAULT FALSE,
    is_ev BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ev_vehicles (
    vehicle_id UUID PRIMARY KEY REFERENCES vehicles(id) ON DELETE CASCADE,
    battery_capacity_kwh DECIMAL(8, 2) NOT NULL,
    consumption_per_km_kwh DECIMAL(8, 4) NOT NULL,
    current_soc_percentage DECIMAL(5, 2) CHECK (current_soc_percentage >= 0 AND current_soc_percentage <= 100),
    supported_charger_types TEXT[]
);

-- 4. LOCATIONS & ROUTES
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    coordinates GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_locations_geom ON locations USING GIST (coordinates);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_name VARCHAR(255) NOT NULL,
    destination_name VARCHAR(255) NOT NULL,
    origin_geom GEOGRAPHY(Point, 4326) NOT NULL,
    destination_geom GEOGRAPHY(Point, 4326) NOT NULL,
    route_geometry GEOMETRY(LineString, 4326),
    distance_meters DECIMAL(12, 2) NOT NULL,
    duration_seconds INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_routes_geom ON routes USING GIST (route_geometry);

-- 5. RIDES
CREATE TABLE rides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    route_id UUID REFERENCES routes(id),
    origin_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    origin_geom GEOGRAPHY(Point, 4326) NOT NULL,
    destination_geom GEOGRAPHY(Point, 4326) NOT NULL,
    departure_time TIMESTAMPTZ NOT NULL,
    available_seats INT NOT NULL CHECK (available_seats >= 0),
    price_per_seat DECIMAL(10, 2) NOT NULL CHECK (price_per_seat >= 0),
    max_detour_minutes INT DEFAULT 20,
    status ride_status DEFAULT 'CREATED',
    journey_confidence_score DECIMAL(5, 4), -- 0.0 to 1.0
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_rides_departure ON rides(departure_time);
CREATE INDEX idx_rides_origin_geom ON rides USING GIST(origin_geom);
CREATE INDEX idx_rides_destination_geom ON rides USING GIST(destination_geom);

-- 6. BOOKINGS & PASSENGER DEMAND
CREATE TABLE ride_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_id UUID NOT NULL REFERENCES passengers(id),
    origin_geom GEOGRAPHY(Point, 4326) NOT NULL,
    destination_geom GEOGRAPHY(Point, 4326) NOT NULL,
    requested_departure_time TIMESTAMPTZ NOT NULL,
    seats_needed INT NOT NULL CHECK (seats_needed > 0),
    is_fulfilled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ride_requests_geom ON ride_requests USING GIST(origin_geom);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id),
    passenger_id UUID NOT NULL REFERENCES passengers(id),
    seats_booked INT NOT NULL CHECK (seats_booked > 0),
    total_price DECIMAL(10, 2) NOT NULL,
    status booking_status DEFAULT 'PENDING',
    pickup_geom GEOGRAPHY(Point, 4326) NOT NULL,
    dropoff_geom GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. CANCELLATIONS
CREATE TABLE cancellation_reasons (
    id SERIAL PRIMARY KEY,
    reason_code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_driver_fault BOOLEAN DEFAULT FALSE,
    is_passenger_fault BOOLEAN DEFAULT FALSE
);

CREATE TABLE cancellations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID REFERENCES rides(id), -- If driver cancels whole ride
    booking_id UUID REFERENCES bookings(id), -- If passenger cancels booking
    cancelled_by UUID NOT NULL REFERENCES users(id),
    reason_id INT REFERENCES cancellation_reasons(id),
    cancellation_time TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- 8. RECOVERY SYSTEM (Signature feature)
CREATE TABLE recovery_candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_booking_id UUID NOT NULL REFERENCES bookings(id),
    backup_ride_id UUID NOT NULL REFERENCES rides(id),
    match_score DECIMAL(5, 4) NOT NULL,
    estimated_detour_mins INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE recovery_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    triggered_by_cancellation_id UUID REFERENCES cancellations(id),
    selected_candidate_id UUID REFERENCES recovery_candidates(id),
    status recovery_status DEFAULT 'PENDING',
    passenger_notified_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. AI/ML PREDICTIONS & RELIABILITY
CREATE TABLE reliability_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    ride_id UUID REFERENCES rides(id),
    event_type VARCHAR(100) NOT NULL, -- 'LATE_START', 'NO_SHOW', etc.
    event_time TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE demand_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_zone GEOMETRY(Polygon, 4326) NOT NULL,
    destination_zone GEOMETRY(Polygon, 4326) NOT NULL,
    prediction_time_window TSTZRANGE NOT NULL,
    expected_demand INT NOT NULL,
    expected_supply INT NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL, -- polymorphic (ride_id, booking_id, etc.)
    target_entity_type VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL, -- 'P_BOOK', 'P_ACCEPT', 'P_CANCEL'
    prediction_value DECIMAL(10, 8) NOT NULL,
    features_json JSONB,
    shap_values JSONB, -- For Explainable AI
    experiment_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. REAL-TIME & SAFETY
CREATE TABLE safety_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id),
    event_type safety_event_type NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE gps_points (
    -- High volume table. Often partitioned in production.
    id BIGSERIAL PRIMARY KEY,
    ride_id UUID NOT NULL REFERENCES rides(id),
    location GEOGRAPHY(Point, 4326) NOT NULL,
    speed_kmh DECIMAL(5, 2),
    heading INT,
    recorded_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_gps_ride ON gps_points(ride_id);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id),
    sender_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    type VARCHAR(50), -- 'INFO', 'WARNING', 'RECOVERY', 'DEMAND_NUDGE'
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. EV & CHARGING
CREATE TABLE charging_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    charger_types TEXT[],
    max_kw DECIMAL(8, 2),
    is_operational BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_charging_location ON charging_stations USING GIST(location);

CREATE TABLE energy_estimates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    estimated_kwh_required DECIMAL(8, 2) NOT NULL,
    charging_required BOOLEAN DEFAULT FALSE,
    recommended_station_id UUID REFERENCES charging_stations(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. RESEARCH & EXPERIMENTS
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE, -- e.g. 'B0', 'B2', 'B6'
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE experiment_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id),
    seed INT NOT NULL,
    status VARCHAR(50) DEFAULT 'RUNNING',
    metrics_json JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE event_logs (
    -- Central analytics / logging table for all critical system events (Research KPI tracking)
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- e.g., 'SEARCH', 'MATCH_GENERATED', 'BOOKING_CONFIRMED'
    user_id UUID REFERENCES users(id),
    ride_id UUID REFERENCES rides(id),
    booking_id UUID REFERENCES bookings(id),
    experiment_id UUID REFERENCES experiments(id),
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_event_logs_type ON event_logs(event_type);
CREATE INDEX idx_event_logs_created ON event_logs(created_at);

-- 13. RATINGS & TRUST
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id UUID NOT NULL REFERENCES rides(id),
    reviewer_id UUID NOT NULL REFERENCES users(id),
    reviewee_id UUID NOT NULL REFERENCES users(id),
    score INT NOT NULL CHECK (score >= 1 AND score <= 5),
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
