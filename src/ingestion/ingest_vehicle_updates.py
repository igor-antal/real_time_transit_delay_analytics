from src.db.db import get_conn
from .get_gtfs import fetch_gtfs_feed
from .logger import logger

VEHICLES_URL = r"https://api.golemio.cz//v2/vehiclepositions/gtfsrt/vehicle_positions.pb"
INSERT_SQL = """
INSERT INTO fact_vehicles_pos (
    trip_id,
    route_id,
    latitude,
    longitude,
    bearing
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (trip_id)
DO UPDATE SET 
   route_id = EXCLUDED.route_id,
   latitude = EXCLUDED.latitude,
   longitude = EXCLUDED.longitude,
   bearing = EXCLUDED.bearing
;
"""


def get_vehicle_updates() -> None:

    feed = fetch_gtfs_feed(VEHICLES_URL)
    with get_conn() as conn:
        with conn.cursor() as cur:

            cur.execute("TRUNCATE fact_vehicles_pos;")

            for entity in feed.entity:
                trip_id = entity.vehicle.trip.trip_id
                route_id = entity.vehicle.trip.route_id
                latitude = entity.vehicle.position.latitude
                longitude = entity.vehicle.position.longitude
                bearing = entity.vehicle.position.bearing

                cur.execute(
                    INSERT_SQL,
                    (
                        trip_id,
                        route_id,
                        latitude,
                        longitude,
                        bearing
                    )
                )
    logger.info("Vehicles updated")


if __name__ == "__main__":
    get_vehicle_updates()
