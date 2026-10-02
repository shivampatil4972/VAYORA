-- ============================================================
-- VAYORA PostgreSQL Initialization
-- This script runs when the PostgreSQL container first starts.
-- Enables PostGIS extension and sets up the database.
-- ============================================================

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable btree_gist for constraint exclusion
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Confirm
SELECT PostGIS_Version();
