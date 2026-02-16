from pidproject.db.db import get_conn


def main() -> None:
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            with open(r"../../../sql/schema.sql") as schema_sql:
                cur.execute(schema_sql.read())
    conn.close()
    print("Database setup complete")


if __name__ == "__main__":
    main()
