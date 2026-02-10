from datetime import datetime, timedelta
from .get_gtfs import fetch_gtfs_feed
from src.db.db import get_conn


TRIP_UPDATES_URL = r"https://api.golemio.cz/v2/vehiclepositions/gtfsrt/trip_updates.pb"

# delay shorter than this value won't be recorded:
MIN_DELAY_IN_SECONDS = 60

# delays above this value will be counted as 0
MAX_VALID_DELAY_SECONDS = 10000

UPSERT_DELAYS_SQL = """
INSERT INTO fact_trip_delay_1min (
    minute_recorded,
    hour_recorded,
    trip_id,
    route_id,
    delay_seconds,
    is_delayed
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (trip_id, minute_recorded)
DO UPDATE SET
    delay_seconds = GREATEST(
    fact_trip_delay_1min.delay_seconds,
    EXCLUDED.delay_seconds
);
"""


DELETE_OLD_RECORDS_SQL = """
    DELETE FROM fact_trip_delay_1min
    WHERE minute_recorded < %s;
    """


# stu = stop time update, between the arrival/departure delay returns the larger one
def extract_delay(stu) -> int | None:
    delays = []
    if stu.HasField("arrival") and stu.arrival.HasField("delay"):
        delays.append(stu.arrival.delay)
    if stu.HasField("departure") and stu.departure.HasField("delay"):
        delays.append(stu.departure.delay)
    return max(delays) if delays else None


def get_trip_updates() -> None:
    feed = fetch_gtfs_feed(TRIP_UPDATES_URL)

    conn = get_conn()

    with conn:
        with conn.cursor() as cur:
            now = datetime.now()
            day_ago = now - timedelta(hours=24)
            minute_recorded = now.replace(second=0, microsecond=0)
            hour_recorded = minute_recorded.replace(minute=0)

            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue
                trip_update = entity.trip_update

                trip_id = trip_update.trip.trip_id
                route_id = trip_update.trip.route_id

                max_delay = 0

                for stu in trip_update.stop_time_update:
                    delay = extract_delay(stu)
                    if delay is None or delay < MIN_DELAY_IN_SECONDS:
                        continue
                    max_delay = max(max_delay, delay) if max(max_delay, delay) < MAX_VALID_DELAY_SECONDS else 0

                is_delayed = max_delay > 0

                cur.execute(
                    UPSERT_DELAYS_SQL,
                    (
                        minute_recorded,
                        hour_recorded,
                        trip_id,
                        route_id,
                        max_delay,
                        is_delayed
                        )
                    )

            cur.execute(
                DELETE_OLD_RECORDS_SQL,
                (day_ago,))

    print(f"Trips / Delays updated: {now}")


if __name__ == "__main__":
    get_trip_updates()
