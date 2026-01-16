from src.db.db import get_conn

TIME_INSERT_SQL = """
INSERT INTO dim_time
SELECT ts, DATE_TRUNC('hour', ts)

  FROM GENERATE_SERIES(
       DATE_TRUNC('day', CURRENT_DATE - 1),
       DATE_TRUNC('day', CURRENT_DATE + 2) - interval '1 minute',
       interval '1 minute'
) ts;
"""

conn = get_conn()
with conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_time;")
        cur.execute(TIME_INSERT_SQL)
        print("DIM TIME updated.")

