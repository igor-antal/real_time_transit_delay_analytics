from datetime import datetime, timedelta
from src.ingestion.get_gtfs import fetch_gtfs_feed
from src.db.db import get_conn


TRIP_UPDATES_URL = r"https://api.golemio.cz/v2/vehiclepositions/gtfsrt/trip_updates.pb"

# delay shorter than this value won't be recorded:
MIN_DELAY_IN_SECONDS = 60

UPSERT_DELAYS_SQL = """
INSERT INTO fact_delay_events_1min (
    minute_recorded,
    hour_recorded,
    trip_id,
    route_id,
    stop_id,
    stop_sequence,
    delay_seconds
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (trip_id, stop_id, minute_recorded)
DO UPDATE SET
    delay_seconds = GREATEST(
    fact_delay_events_1min.delay_seconds,
    EXCLUDED.delay_seconds
);
"""

UPSERT_TRIPS_SQL = """
INSERT INTO fact_seen_trips_1min (
    minute_recorded,
    hour_recorded,
    trip_id,
    route_id,
    is_delayed
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (trip_id, minute_recorded)
DO UPDATE SET
    minute_recorded = GREATEST(
    fact_seen_trips_1min.minute_recorded,
    EXCLUDED.minute_recorded
);
"""


# deletes records older than specified datetime
def delete_old_records(table):
    return f"""
    DELETE FROM {table}
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
    now = datetime.now()
    day_ago = now - timedelta(hours=24)

    with conn:
        with conn.cursor() as cur:
            minute_recorded = now.replace(second=0, microsecond=0)
            hour_recorded = minute_recorded.replace(minute=0)

            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue

                trip_update = entity.trip_update
                trip_id = trip_update.trip.trip_id
                route_id = trip_update.trip.route_id
                seen_delay = False

                # stu = stop_time_update
                for stu in trip_update.stop_time_update:
                    delay = extract_delay(stu)
                    if delay is None or delay < MIN_DELAY_IN_SECONDS:
                        continue
                    else:
                        seen_delay = True

                    cur.execute(
                        UPSERT_DELAYS_SQL,
                        (
                            minute_recorded,
                            hour_recorded,
                            trip_id,
                            route_id,
                            stu.stop_id,
                            stu.stop_sequence,
                            delay
                        )
                    )

                cur.execute(
                    UPSERT_TRIPS_SQL,
                    (
                        minute_recorded,
                        hour_recorded,
                        trip_id,
                        route_id,
                        seen_delay
                    )
                )

            cur.execute(
                delete_old_records("fact_delay_events_1min"),
                (day_ago,)
            )
            cur.execute(
                delete_old_records("fact_seen_trips_1min"),
                (day_ago,)
            )
    conn.close()
    print(f"Trips / Delays updated: {now}")


if __name__ == "__main__":
    get_trip_updates()
