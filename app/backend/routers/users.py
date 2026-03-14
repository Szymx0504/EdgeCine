from fastapi import APIRouter, HTTPException, Depends
from ..core.database import db, hasher
from ..schemas import UserCreate, UserResponse, UserLogin
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(tags=["Users & Auth"])

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    conn = db.get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        password_hash = hasher.hash_password(user.password)
        cur.execute("INSERT INTO users (name, password_hash) VALUES (%s, %s) RETURNING id, name", (user.name, password_hash))
        new_user = cur.fetchone()
        conn.commit()
        return new_user
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        db.return_connection(conn)

@router.post("/login", response_model=UserResponse)
def login(user_login: UserLogin):
    conn = db.get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE name = %s", (user_login.name,))
        user = cur.fetchone()
        if not user or not hasher.verify_password(user_login.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return {"id": user["id"], "name": user["name"]}
    finally:
        db.return_connection(conn)

@router.get("/users/{user_id}/interactions")
def get_user_interactions(user_id: int):
    conn = db.get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM user_interactions WHERE user_id = %s", (user_id,))
        return cur.fetchall()
    finally:
        db.return_connection(conn)
