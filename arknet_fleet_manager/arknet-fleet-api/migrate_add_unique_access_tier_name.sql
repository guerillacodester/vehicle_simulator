-- Migration: Add unique constraint to access_tiers.name
ALTER TABLE access_tiers
ADD CONSTRAINT access_tiers_name_unique UNIQUE (name);