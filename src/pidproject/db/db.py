import psycopg2
from pidproject.db.config import DB_CONFIG


def get_conn():
    return psycopg2.connect(**DB_CONFIG)
