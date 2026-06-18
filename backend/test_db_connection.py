import psycopg2
import os
import sys
import time

MAX_RETRIES = 30
RETRY_INTERVAL = 2


def test_connection():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = psycopg2.connect(
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
            )
            conn.close()
            print("Connection successful")
            return
        except Exception as e:
            print(f"Attempt {attempt}/{MAX_RETRIES}: DB not ready ({e})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)

    print("Database connection failed after all retries. Exiting.")
    sys.exit(1)


if __name__ == "__main__":
    test_connection()
