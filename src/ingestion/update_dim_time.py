from src.db.db import get_conn

TIME_INSERT_SQL = """
INSERT INTO dim_time
SELECT ts, 
       DATE_TRUNC('hour', ts),
       EXTRACT(minute FROM ts),
       EXTRACT(hour FROM ts)::text || ':00',
       EXTRACT(day FROM ts)::text || '.' || ' ' || EXTRACT(month FROM ts)::text || '.'
       
  FROM GENERATE_SERIES(
       DATE_TRUNC('day', CURRENT_DATE - 1),
       DATE_TRUNC('day', CURRENT_DATE + 2) - interval '1 minute',
       interval '1 minute'
) ts;
"""


def update_dim_time() -> None:
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE dim_time;")
            cur.execute(TIME_INSERT_SQL)
            print("DIM TIME updated.")


if __name__ == "__main__":
    update_dim_time()
