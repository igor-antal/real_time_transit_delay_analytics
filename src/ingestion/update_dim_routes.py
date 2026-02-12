import requests
from api_key import API_KEY
from src.db.db import get_conn
from logger import logger
import json

ROUTES_URL = r"https://api.golemio.cz//v2/gtfs/routes"
headers = {"X-Access-Token": API_KEY}

try:
    response = requests.get(STOPS_URL, headers=headers)
    response.raise_for_status()
except requests.exceptions.ConnectionError as error:
    logger.exception()
    raise
except requests.exceptions.HTTPError as error:
    logger.exception()
    raise

response = response.json()

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
    logger.info("Dim routes updated")


if __name__ == "__main__":
    update_dim_routes()
