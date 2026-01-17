import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Get a connection to NeonDB PostgreSQL."""
    connection_string = os.environ.get("DATABASE_URL")
    if not connection_string:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(connection_string)
        return conn
    except psycopg2.Error as e:
        raise RuntimeError(f"Failed to connect to database: {e}")


def query(sql, params=None, fetch_one=False):
    """Execute a SELECT query and return results."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            if fetch_one:
                return cur.fetchone()
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    """Execute an INSERT/UPDATE/DELETE query."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        raise RuntimeError(f"Database error: {e}")
    finally:
        conn.close()
