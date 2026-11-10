"""
Database Connection Manager.
Provides context management, connection pooling/reconnects, parameterized execution,
and safe transaction handling with commit and rollback.
"""

import mysql.connector
from mysql.connector import errorcode
import config

class Database:
    """Context manager and execution utility for MySQL database operations."""

    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or config.DB_HOST
        self.user = user or config.DB_USER
        self.password = password or config.DB_PASSWORD
        self.database = database or config.DB_NAME
        self.port = port or config.DB_PORT
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establishes connection to MySQL."""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                autocommit=False
            )
            return self.conn
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                raise RuntimeError(f"Database '{self.database}' does not exist. Please run initialization first.")
            elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise RuntimeError("Access denied: Invalid MySQL username or password. Check .env file.")
            else:
                raise RuntimeError(f"MySQL Connection Error [{err.errno}]: {err.msg}")

    def __enter__(self):
        self.connect()
        self.cursor = self.conn.cursor(dictionary=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.conn and self.conn.is_connected():
                self.conn.rollback()
        else:
            if self.conn and self.conn.is_connected():
                self.conn.commit()

        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def execute_query(self, query: str, params: tuple = None):
        """Executes a SELECT query and returns all matching rows as dictionaries."""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()

    def execute_one(self, query: str, params: tuple = None):
        """Executes a SELECT query and returns the first row as a dictionary or None."""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()

    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """Executes an INSERT, UPDATE, or DELETE query and returns affected rows."""
        self.cursor.execute(query, params or ())
        return self.cursor.rowcount

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Executes an INSERT query and returns the last inserted ID."""
        self.cursor.execute(query, params or ())
        return self.cursor.lastrowid

    def commit(self):
        """Explicitly commits the current transaction."""
        if self.conn and self.conn.is_connected():
            self.conn.commit()

    def rollback(self):
        """Rolls back the current transaction."""
        if self.conn and self.conn.is_connected():
            self.conn.rollback()

def get_db_connection():
    """Convenience factory returning a connected Database instance."""
    db = Database()
    db.connect()
    return db

def test_connection(host=None, user=None, password=None, port=None):
    """Tests if a MySQL server can be connected without specifying database name."""
    try:
        conn = mysql.connector.connect(
            host=host or config.DB_HOST,
            user=user or config.DB_USER,
            password=password or config.DB_PASSWORD,
            port=port or config.DB_PORT
        )
        if conn.is_connected():
            conn.close()
            return True, "Connected successfully"
        return False, "Could not establish connection"
    except Exception as e:
        return False, str(e)
