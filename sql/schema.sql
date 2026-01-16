CREATE TABLE IF NOT EXISTS fact_trip_delay_1min (
    minute_recorded TIMESTAMP NOT NULL,
    hour_recorded TIMESTAMP NOT NULL,
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    delay_seconds INT NOT NULL,
    is_delayed BOOL NOT NULL,
    PRIMARY KEY (trip_id, minute_recorded)
);

CREATE INDEX IF NOT EXISTS idx_delay_route_minute
ON fact_trip_delay_1min (route_id, minute_recorded);

CREATE TABLE IF NOT EXISTS dim_routes (
    route_id TEXT PRIMARY KEY,
    long_name TEXT,
    short_name TEXT
);

CREATE OR REPLACE VIEW v_trips_latest AS (
    SELECT *
      FROM fact_trip_delay_1min
     WHERE minute_recorded = (
           SELECT MAX(minute_recorded)
             FROM fact_trip_delay_1min)
);

CREATE OR REPLACE VIEW v_delays_per_minute AS (
    SELECT minute_recorded,
           hour_recorded,
           COUNT(trip_id) AS trip_count,
           AVG(delay_seconds) AS avg_delay_per_trip,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) AS median_delay_per_trip,
           AVG(delay_seconds) FILTER(WHERE delay_seconds <> 0) AS avg_delay,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) FILTER(WHERE delay_seconds <> 0) AS median_delay
      FROM fact_trip_delay_1min
     GROUP BY minute_recorded, hour_recorded
);

CREATE OR REPLACE VIEW v_delays_per_hour AS (
WITH hourly_avg_trip_count AS (
    SELECT hour_recorded,
           AVG(trip_count) AS avg_trip_count
      FROM v_delays_per_minute
     GROUP BY hour_recorded
    )

    SELECT td.hour_recorded,
           hatc.avg_trip_count,
           AVG(td.delay_seconds) AS avg_delay_per_trip,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY td.delay_seconds) AS median_delay_per_trip,
           AVG(td.delay_seconds) FILTER(WHERE td.delay_seconds <> 0) AS avg_delay,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY td.delay_seconds) FILTER(WHERE td.delay_seconds <> 0) AS median_delay
      FROM fact_trip_delay_1min td
      JOIN hourly_avg_trip_count hatc
        ON hatc.hour_recorded = td.hour_recorded
     GROUP BY td.hour_recorded, hatc.avg_trip_count
);

CREATE OR REPLACE VIEW v_avg_delay_per_route_latest_top15 AS(
WITH route_delays AS(
    SELECT route_id,
           AVG(delay_seconds) AS avg_delay
      FROM fact_trip_delay_1min
     WHERE minute_recorded = (SELECT MAX(minute_recorded)
                                FROM fact_trip_delay_1min)
     GROUP BY route_id
     ORDER BY avg_delay DESC
     LIMIT 15
    )

    SELECT dr.long_name, rd.avg_delay
      FROM route_delays rd
      JOIN dim_routes dr
        ON rd.route_id = dr.route_id
);

CREATE OR REPLACE VIEW v_pct_delayed_trips AS(
    SELECT COUNT(*) FILTER(WHERE is_delayed = TRUE)::numeric / COUNT(*) AS pct_delayed
      FROM fact_trip_delay_1min
);

CREATE OR REPLACE VIEW v_ongoing_trips_count AS(
    SELECT COUNT(*)
      FROM fact_trip_delay_1min
);