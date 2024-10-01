import psycopg2
import os


def test_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
        )
        print("Connection successful")
    except Exception as e:
        print(
            f"Connection failed to {os.environ['DB_NAME']} at {os.environ['DB_HOST']}: {e}"
        )


if __name__ == "__main__":
    test_connection()
