CREATE TABLE IF NOT EXISTS fact_delay_events_1min (
    minute_recorded TIMESTAMP NOT NULL,
    hour_recorded TIMESTAMP NOT NULL,
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    stop_sequence INT,
    delay_seconds INT NOT NULL,
    PRIMARY KEY (trip_id, stop_id, minute_recorded)
);

CREATE INDEX IF NOT EXISTS idx_delay_route_minute
ON fact_delay_events_1min (route_id, minute_recorded);

CREATE TABLE IF NOT EXISTS fact_seen_trips_1min (
    minute_recorded TIMESTAMP NOT NULL,
    hour_recorded TIMESTAMP NOT NULL,
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    is_delayed BOOL NOT NULL,
    PRIMARY KEY (minute_recorded, trip_id)
);

CREATE INDEX IF NOT EXISTS idx_seen_route_minute
ON fact_seen_trips_1min (route_id, minute_recorded);

CREATE TABLE IF NOT EXISTS dim_routes (
    route_id TEXT PRIMARY KEY,
    long_name TEXT,
    short_name TEXT
);

CREATE OR REPLACE VIEW v_seen_trips_latest AS (
    SELECT *
      FROM fact_seen_trips_1min
     WHERE minute_recorded = (
           SELECT MAX(minute_recorded)
             FROM fact_seen_trips_1min)
);

CREATE OR REPLACE VIEW v_trip_delays AS (
SELECT
    minute_recorded,
    hour_recorded,
    trip_id,
    route_id,
    MAX(delay_seconds) AS delay_seconds
  FROM fact_delay_events_1min
 GROUP BY minute_recorded, hour_recorded, trip_id, route_id
 );

CREATE OR REPLACE VIEW v_all_trips_1min AS (
SELECT minute_recorded, hour_recorded, trip_id, route_id, delay_seconds
  FROM v_trip_delays

UNION ALL

SELECT minute_recorded, hour_recorded, trip_id, route_id, 0 AS delay_seconds
  FROM fact_seen_trips_1min
 WHERE is_delayed IS FALSE
 );

CREATE OR REPLACE VIEW v_avg_delays_1min AS (
SELECT minute_recorded, hour_recorded,
       AVG(delay_seconds) AS avg_delay_per_trip,
       AVG(delay_seconds) FILTER (WHERE delay_seconds <> 0) AS avg_delay,
       COUNT(*) AS trips_count
  FROM v_all_trips_1min
 GROUP BY minute_recorded, hour_recorded
);

CREATE OR REPLACE VIEW v_avg_delays_1h AS (
SELECT hour_recorded,
       AVG(avg_delay_per_trip) AS avg_delay_per_trip,
       AVG(avg_delay) AS avg_delay,
       AVG(trips_count) AS trips_count
  FROM v_avg_delays_1min
 GROUP BY hour_recorded
);

CREATE OR REPLACE VIEW v_route_delays AS (
SELECT minute_recorded, route_id, AVG(delay_seconds) AS avg_delay
  FROM v_all_trips_1min
 GROUP BY minute_recorded, route_id
);

CREATE OR REPLACE VIEW v_route_delays_latest AS (
SELECT *
  FROM v_route_delays
 WHERE minute_recorded = (
       SELECT MAX(minute_recorded)
         FROM v_route_delays)
);

CREATE OR REPLACE VIEW v_avg_trip_delays AS (
SELECT minute_recorded, SUM(delay_seconds)::float / COUNT(*)::float AS avg_delay
  FROM v_all_trips_1min
 GROUP BY minute_recorded
);