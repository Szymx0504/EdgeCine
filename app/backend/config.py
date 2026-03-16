import os
from pathlib import Path
from dotenv import load_dotenv
from passlib.context import CryptContext

env_path = Path(__file__).resolve().parent.parent.parent / ".env"

load_dotenv(dotenv_path=env_path)

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.name = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")

    def get_connection_params(self):
        return {
            "host": self.host,
            "database": self.name,
            "user": self.user,
            "password": self.password,
            "port": self.port
        }

class PasswordHasher:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

db_config = DatabaseConfig()
hasher = PasswordHasher()