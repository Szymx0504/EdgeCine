import os
import time
import logging
from typing import Optional
import psycopg2
from psycopg2 import pool
from pathlib import Path
from dotenv import load_dotenv
from passlib.context import CryptContext

# Set up logging for the core module
logger = logging.getLogger("edge-cine-core")

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Database:
    """Thread-safe Database Connection Pool for PostgreSQL."""
    _pool: Optional[pool.ThreadedConnectionPool] = None

    @classmethod
    def initialize(cls):
        """Initializes the connection pool using environment variables with retries."""
        if cls._pool is not None:
            return

        max_retries = 5
        for i in range(max_retries):
            try:
                cls._pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=os.getenv("DB_HOST", "db"),
                    database=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    port=os.getenv("DB_PORT", "5432")
                )
                logger.info("Database Connection Pool initialized (1-10 connections).")
                return
            except Exception as e:
                if i < max_retries - 1:
                    logger.warning(f"DB connection attempt {i+1} failed, retrying in 2s... ({e})")
                    time.sleep(2)
                else:
                    logger.error(f"Failed to initialize Database Pool after {max_retries} attempts: {e}")
                    raise

    @classmethod
    def get_connection(cls):
        """Acquires a connection from the pool."""
        if cls._pool is None:
            cls.initialize()
        return cls._pool.getconn()

    @classmethod
    def return_connection(cls, conn):
        """Returns a connection back to the pool."""
        if cls._pool:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Closes all connections in the pool."""
        if cls._pool:
            cls._pool.closeall()
            logger.info("Database Connection Pool closed.")

class PasswordHasher:
    """Utility for secure password hashing and verification."""
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

# Global instances
db = Database
hasher = PasswordHasher()
