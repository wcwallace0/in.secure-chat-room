import psycopg2
import psycopg2.pool
from contextlib import contextmanager
from dotenv import dotenv_values

config = dotenv_values(".env")

dbpool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=1,
                            maxconn=50,
                            host=config["HOSTNAME"],
                            dbname=config["DATABASE"],
                            user=config["USER"],
                            password=config["PASSWORD"],
                            port=config["PORT"]
                            )

@contextmanager
def db_cursor():
    conn = dbpool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        dbpool.putconn(conn)