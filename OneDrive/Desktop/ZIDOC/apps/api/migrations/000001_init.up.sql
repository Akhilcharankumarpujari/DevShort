-- Zidoc Phase 1 Database Schema Init
-- This file acts as a baseline placeholder for Phase 1.
CREATE TABLE IF NOT EXISTS schema_versions (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
