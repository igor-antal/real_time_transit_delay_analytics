import requests
from api_key import API_KEY
from src.db.db import get_conn
from datetime import datetime

STOPS_URL = r"https://api.golemio.cz//v2/gtfs/routes"
headers = {"X-Access-Token": API_KEY}
response = requests.get(STOPS_URL, headers=headers).json()

INSERT_SQL = """
INSERT INTO dim_routes (
    route_id,
    long_name,
    short_name
)
VALUES (%s, %s, %s);
"""


def main():
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE dim_routes;")

            for route in response:
                route_id = route["route_id"]
                long_name = route["route_long_name"]
                short_name = route["route_short_name"]

                cur.execute(
                    INSERT_SQL, (
                        route_id,
                        long_name,
                        short_name
                    )
                )
    conn.close()
    print(f"Routes updated: {datetime.now()}")


if __name__ == "__main__":
    main()
