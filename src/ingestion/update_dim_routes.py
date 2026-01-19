import requests
from api_key import API_KEY
from src.db.db import get_conn
from datetime import datetime
import json

STOPS_URL = r"https://api.golemio.cz//v2/gtfs/routes"
headers = {"X-Access-Token": API_KEY}
response = requests.get(STOPS_URL, headers=headers).json()

INSERT_SQL = """
INSERT INTO dim_routes (
    route_id,
    long_name,
    short_name,
    route_type
)
VALUES (%s, %s, %s, %s);
"""


def update_dim_routes() -> None:
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE dim_routes;")

            with open("route_types.json", "r") as f:
                route_types = json.loads(f.read())

                for route in response:
                    route_id = route["route_id"]
                    long_name = route["route_long_name"]
                    short_name = route["route_short_name"]
                    route_type = route_types[str(route["route_type"])]

                    cur.execute(
                        INSERT_SQL, (
                            route_id,
                            long_name,
                            short_name,
                            route_type
                        )
                    )
    conn.close()
    print(f"Routes updated: {datetime.now()}")


if __name__ == "__main__":
    update_dim_routes()
