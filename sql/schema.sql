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

CREATE OR REPLACE VIEW v_delays_per_trip_1min AS (
WITH delayed_trips AS (
    SELECT
        minute_recorded,
        hour_recorded,
        trip_id,
        route_id,
        MAX(delay_seconds) AS delay_seconds
      FROM fact_delay_events_1min
     GROUP BY minute_recorded, hour_recorded, trip_id, route_id
    ),

trips_without_delay AS (
    SELECT minute_recorded,
           hour_recorded,
           trip_id,
           route_id,
           0 AS delay_seconds
     FROM fact_seen_trips_1min
    WHERE is_delayed IS FALSE)

    SELECT *
      FROM delayed_trips

    UNION ALL

    SELECT *
      FROM trips_without_delay
);

CREATE OR REPLACE VIEW v_delays_per_minute AS (
    SELECT minute_recorded,
           hour_recorded,
           COUNT(trip_id) AS trip_count,
           AVG(delay_seconds) AS avg_delay_per_trip,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) AS median_delay_per_trip,
           AVG(delay_seconds) FILTER(WHERE delay_seconds <> 0) AS avg_delay,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) FILTER(WHERE delay_seconds <> 0) AS median_delay
      FROM v_delays_per_trip_1min
     GROUP BY minute_recorded, hour_recorded
);

CREATE OR REPLACE VIEW v_delays_per_hour AS (
WITH hourly_avg_trip_count AS (
    SELECT hour_recorded,
           AVG(trip_count) AS avg_trip_count
      FROM v_delays_per_minute
     GROUP BY hour_recorded
    )

    SELECT dpt.hour_recorded,
           hatc.avg_trip_count,
           AVG(dpt.delay_seconds) AS avg_delay_per_trip,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY dpt.delay_seconds) AS median_delay_per_trip,
           AVG(delay_seconds) FILTER(WHERE dpt.delay_seconds <> 0) AS avg_delay,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY dpt.delay_seconds) FILTER(WHERE dpt.delay_seconds <> 0) AS median_delay
      FROM v_delays_per_trip_1min dpt
      JOIN hourly_avg_trip_count hatc
        ON hatc.hour_recorded = dpt.hour_recorded
     GROUP BY dpt.hour_recorded, hatc.avg_trip_count
);

CREATE OR REPLACE VIEW v_avg_delay_per_route_latest_top15 AS(
    SELECT route_id,
           AVG(delay_seconds) AS avg_delay
      FROM v_delays_per_trip_1min
     WHERE minute_recorded = (SELECT MAX(minute_recorded)
                                FROM v_delays_per_trip_1min)
     GROUP BY route_id
     ORDER BY avg_delay DESC
     LIMIT 15
);