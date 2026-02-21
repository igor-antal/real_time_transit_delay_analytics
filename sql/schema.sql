CREATE TABLE IF NOT EXISTS fact_trip_delay_1min (
    minute_recorded TIMESTAMP NOT NULL,
    trip_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    delay_seconds INT NOT NULL,
    is_delayed BOOL NOT NULL,
    PRIMARY KEY (trip_id, minute_recorded)
);

CREATE INDEX IF NOT EXISTS idx_delay_route_minute
ON fact_trip_delay_1min (route_id, minute_recorded);

CREATE INDEX IF NOT EXISTS idx_minute_desc
ON fact_trip_delay_1min (minute_recorded DESC);

CREATE TABLE IF NOT EXISTS fact_vehicles_pos (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL,
    latitude DECIMAL NOT NULL,
    longitude DECIMAL NOT NULL,
    bearing INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_routes (
    route_id TEXT PRIMARY KEY,
    long_name TEXT,
    short_name TEXT,
    route_type TEXT
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
           COUNT(trip_id) AS trip_count,
           AVG(delay_seconds) AS avg_delay_per_trip,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) AS median_delay_per_trip,
           AVG(delay_seconds) FILTER(WHERE delay_seconds <> 0) AS avg_delay,
           percentile_cont(0.5) WITHIN GROUP(ORDER BY delay_seconds) FILTER(WHERE delay_seconds <> 0) AS median_delay
      FROM fact_trip_delay_1min
     GROUP BY minute_recorded
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

    SELECT dr.long_name, rd.avg_delay, dr.route_type
      FROM route_delays rd
      JOIN dim_routes dr
        ON rd.route_id = dr.route_id
);

CREATE OR REPLACE VIEW v_delay_by_route_type_latest AS(
    SELECT dim.route_type, AVG(fact.delay_seconds)
     FROM fact_trip_delay_1min fact
     JOIN dim_routes dim
       ON dim.route_id = fact.route_id
    WHERE fact.minute_recorded = (SELECT MAX(minute_recorded)
                                    FROM fact_trip_delay_1min)
    GROUP BY dim.route_type
);

CREATE OR REPLACE VIEW v_delay_per_trip_latest_top15 AS (
WITH latest_delayed_trips_top15 AS (
    SELECT trip_id,
           route_id,
           delay_seconds
      FROM fact_trip_delay_1min
     WHERE minute_recorded = (SELECT MAX(minute_recorded)
                                FROM fact_trip_delay_1min)
     AND is_delayed IS TRUE
     ORDER BY delay_seconds DESC
     LIMIT 15
)

    SELECT dt.trip_id,
           dt.route_id,
           dt.delay_seconds,
           dr.route_type,
           dr.long_name,
           dr.short_name,
           vp.latitude,
           vp.longitude,
           vp.bearing
      FROM latest_delayed_trips_top15 dt
      JOIN dim_routes dr
        ON dr.route_id = dt.route_id
      JOIN fact_vehicles_pos vp
        ON vp.trip_id = dt.trip_id
);
