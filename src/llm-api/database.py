import os
import psycopg

# Get database connection details from environment variables
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Construct the connection string
CONN_STRING = f"host='{DB_HOST}' dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}'"


def get_db_connection():
    """Establish connection to Postgres DB."""
    try:
        conn = psycopg.connect(CONN_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def Initialize_db():
    """Initialize the database."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                api_key TEXT PRIMARY KEY,
                credits INTEGER NOT NULL,
                is_active BOOLEAN NOT NULL
                )
            """)

            cur.execute("SELECT * FROM users WHERE api_key = %s", ('test-key-123',))
            if cur.fetchone() is None:
                print("Adding sample user to PostgreSQL...")
                cur.execute(
                    "INSERT INTO users (api_key, credits, is_active) VALUES (%s, %s, %s)",
                    ('test-key-123', 50, True)
                )

            conn.commit()
            print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing the database: {e}")
    finally:
        conn.close()


def get_user(api_key: str):
    conn = get_db_connection()
    if conn is None: return None

    user_data = None
    with conn.cursor() as cur:
        cur.execute("SELECT api_key, credits, is_active FROM users WHERE api_key = %s", (api_key,))
        user = cur.fetchone() 
        if user:
            user_data = {"api_key": user[0], "credits": user[1], "is_active": user[2]}
    
    conn.close()
    return user_data

def consume_credit(api_key: str):
    conn = get_db_connection()
    if conn is None: return

    with conn.cursor() as cur:
        cur.execute("UPDATE users SET credits = credits - 1 WHERE api_key = %s", (api_key,))
    
    conn.commit() 
    conn.close()