from src.db.db import get_conn

TIME_INSERT_SQL_MINUTE = """
INSERT INTO dim_time_minute
SELECT ts
              
  FROM GENERATE_SERIES(
       DATE_TRUNC('day', CURRENT_DATE - 1),
       DATE_TRUNC('day', CURRENT_DATE + 2) - interval '1 minute',
       interval '1 minute'
) ts;
"""

TIME_INSERT_SQL_HOUR = """
INSERT INTO dim_time_hour
SELECT ts
              
  FROM GENERATE_SERIES(
       DATE_TRUNC('day', CURRENT_DATE - 1),
       DATE_TRUNC('day', CURRENT_DATE + 2) - interval '1 hour',
       interval '1 hour'
) ts;
"""


def update_dim_time() -> None:
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE dim_time_minute;")
            cur.execute("TRUNCATE dim_time_hour;")
            cur.execute(TIME_INSERT_SQL_MINUTE)
            cur.execute(TIME_INSERT_SQL_HOUR)
            print("DIM TIME updated.")


if __name__ == "__main__":
    update_dim_time()
