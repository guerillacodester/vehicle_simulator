-- PostgreSQL Trigger for Active Passengers NOTIFY Events
-- 
-- This file contains PostgreSQL-specific syntax (plpgsql, pg_notify, jsonb)
-- and should NOT be linted with MSSQL/SQL Server tools.
--
-- Create a trigger to publish NOTIFY events on inserts/updates to active_passengers
-- Assumes Strapi uses table public.active_passengers with common columns shown below.
-- Adjust field names if your schema differs.

-- 1) Function to send a JSON payload
CREATE OR REPLACE FUNCTION public.notify_active_passengers() RETURNS trigger AS $$
DECLARE
  payload jsonb;
  action text;
BEGIN
  action := TG_OP; -- 'INSERT' or 'UPDATE'
  payload := jsonb_build_object(
    'action', action,
    'id', NEW.id,
    'passenger_id', NEW.passenger_id,
    'route_id', NEW.route_id,
    'depot_id', NEW.depot_id,
    'latitude', NEW.latitude,
    'longitude', NEW.longitude,
    'destination_lat', NEW.destination_lat,
    'destination_lon', NEW.destination_lon,
    'spawned_at', to_char(NEW.spawned_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
    'status', NEW.status
  );

  PERFORM pg_notify('active_passengers', payload::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2) Trigger for INSERT and UPDATE
DROP TRIGGER IF EXISTS trg_notify_active_passengers_ins ON public.active_passengers;
DROP TRIGGER IF EXISTS trg_notify_active_passengers_upd ON public.active_passengers;

CREATE TRIGGER trg_notify_active_passengers_ins
AFTER INSERT ON public.active_passengers
FOR EACH ROW EXECUTE FUNCTION public.notify_active_passengers();

CREATE TRIGGER trg_notify_active_passengers_upd
AFTER UPDATE ON public.active_passengers
FOR EACH ROW EXECUTE FUNCTION public.notify_active_passengers();
