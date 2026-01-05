from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List

from .config import db_config
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    InteractionCreate, InteractionUpdate, InteractionResponse
)
from .config import hasher

app = FastAPI(title="Netflix Data API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(**db_config.get_connection_params())

@app.get("/")
def read_root():
    return {"message": "Welcome to the Netflix API! DB is working in the background."}

@app.get("/movies/top")
def get_top_movies():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT f.id, f.title, COUNT(ui.id) as likes
            FROM films f
            JOIN user_interactions ui ON f.id = ui.film_id
            WHERE ui.interaction_type = 'like'
            GROUP BY f.id
            ORDER BY likes DESC
            LIMIT 10;
        """

        cur.execute(query)
        movies = cur.fetchall()

        cur.close()
        conn.close()
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/films/recommend")
def recommend_films(q: str = Query(..., min_length=1)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Websearch to tsquery parses "natural" queries like "action movies with brad pitt"
        # ts_rank sorts by relevance
        query = """
            SELECT 
                id, title, release_year, type, description,
                ts_rank(search_vector, websearch_to_tsquery('english', %s)) as rank
            FROM films 
            WHERE search_vector @@ websearch_to_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT 20;
        """

        cur.execute(query, (q, q))
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "year": r[2],
                "type": r[3],
                "description": r[4],
                "rank": r[5]
            })
        
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database error during recommendation")

@app.get("/films/search")
def search_films(q: str = Query(None, min_length=1)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT id, title, release_year, type, description 
            FROM films 
            WHERE title ILIKE %s OR description ILIKE %s
            ORDER BY release_year DESC
            LIMIT 20;
        """

        search_param = f"%{q}%"
        cur.execute(query, (search_param, search_param))
        
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "year": r[2],
                "type": r[3],
                "description": r[4]
            })
        
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Błąd bazy: {e}")
        raise HTTPException(status_code=500, detail="Błąd połączenia z bazą danych")

@app.get("/films/{film_id}")
def get_film_details(film_id: int):
    """Get full details of a single film including actors and tags."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get film basic info
        cur.execute("""
            SELECT f.id, f.title, f.type, f.director, f.country, f.date_added, 
                   f.release_year, f.rating, f.description,
                   m.duration_minutes, m.is_short_movie,
                   s.seasons_count, s.is_miniseries
            FROM films f
            LEFT JOIN movies m ON f.movie_id = m.id
            LEFT JOIN series s ON f.series_id = s.id
            WHERE f.id = %s
        """, (film_id,))
        
        film = cur.fetchone()
        if not film:
            raise HTTPException(status_code=404, detail="Film not found")
        
        # Get actors
        cur.execute("""
            SELECT a.name 
            FROM actors a
            JOIN films_actors fa ON a.id = fa.actor_id
            WHERE fa.film_id = %s
        """, (film_id,))
        actors = [row['name'] for row in cur.fetchall()]
        
        # Get tags
        cur.execute("""
            SELECT t.name 
            FROM tags t
            JOIN films_tags ft ON t.id = ft.tag_id
            WHERE ft.film_id = %s
        """, (film_id,))
        tags = [row['name'] for row in cur.fetchall()]
        
        # Get like count
        cur.execute("""
            SELECT COUNT(*) as likes FROM user_interactions 
            WHERE film_id = %s AND interaction_type = 'like'
        """, (film_id,))
        likes = cur.fetchone()['likes']
        
        cur.close()
        conn.close()
        
        return {
            "id": film['id'],
            "title": film['title'],
            "type": film['type'],
            "director": film['director'],
            "country": film['country'],
            "date_added": str(film['date_added']) if film['date_added'] else None,
            "release_year": film['release_year'],
            "rating": film['rating'],
            "description": film['description'],
            "duration_minutes": film['duration_minutes'],
            "is_short_movie": film['is_short_movie'],
            "seasons_count": film['seasons_count'],
            "is_miniseries": film['is_miniseries'],
            "actors": actors,
            "tags": tags,
            "likes": likes
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Users CRUD ---

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Hash the password
        password_hash = hasher.hash_password(user.password)
        
        cur.execute("INSERT INTO users (name, password_hash) VALUES (%s, %s) RETURNING id, name", (user.name, password_hash))
        new_user = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", response_model=UserResponse)
def login(user_login: UserLogin):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM users WHERE name = %s", (user_login.name,))
        user = cur.fetchone()
        
        cur.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        if not hasher.verify_password(user_login.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        return {"id": user["id"], "name": user["name"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("UPDATE users SET name = %s WHERE id = %s RETURNING id, name", (user.name, user_id))
        updated_user = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        deleted_id = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        if not deleted_id:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "User deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- User Interactions ---

@app.get("/users/{user_id}/interactions")
def get_user_interactions(user_id: int):
    """Get all interactions for a user with film details."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT ui.id, ui.film_id, ui.interaction_type, ui.duration_watched_sec, 
                   ui.interaction_timestamp, f.title, f.type as film_type
            FROM user_interactions ui
            JOIN films f ON ui.film_id = f.id
            WHERE ui.user_id = %s
            ORDER BY ui.interaction_timestamp DESC
        """
        cur.execute(query, (user_id,))
        interactions = cur.fetchall()
        
        cur.close()
        conn.close()
        return interactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Interactions CRUD ---

@app.post("/interactions", response_model=InteractionResponse)
def create_interaction(interaction: InteractionCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            INSERT INTO user_interactions (user_id, film_id, interaction_type, duration_watched_sec) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id, user_id, film_id, interaction_type, duration_watched_sec, interaction_timestamp
        """
        cur.execute(query, (
            interaction.user_id, 
            interaction.film_id, 
            interaction.interaction_type, 
            interaction.duration_watched_sec
        ))
        new_interaction = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        return new_interaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/interactions/{interaction_id}", response_model=InteractionResponse)
def update_interaction(interaction_id: int, interaction: InteractionUpdate):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic query based on provided fields
        update_fields = []
        params = []
        if interaction.interaction_type is not None:
            update_fields.append("interaction_type = %s")
            params.append(interaction.interaction_type)
        if interaction.duration_watched_sec is not None:
            update_fields.append("duration_watched_sec = %s")
            params.append(interaction.duration_watched_sec)
            
        if not update_fields:
             raise HTTPException(status_code=400, detail="No fields to update")
             
        params.append(interaction_id)
        query = f"UPDATE user_interactions SET {', '.join(update_fields)} WHERE id = %s RETURNING id, user_id, film_id, interaction_type, duration_watched_sec, interaction_timestamp"
        
        cur.execute(query, tuple(params))
        updated_row = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        if not updated_row:
             raise HTTPException(status_code=404, detail="Interaction not found")
             
        return updated_row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/interactions/{interaction_id}")
def delete_interaction(interaction_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM user_interactions WHERE id = %s RETURNING id", (interaction_id,))
        deleted_id = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        if not deleted_id:
             raise HTTPException(status_code=404, detail="Interaction not found")
        
        return {"message": "Interaction deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Analytics View ---

@app.get("/analytics/training-data")
def get_training_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM v_model_training_triplets")
        data = cur.fetchall()
        
        cur.close()
        conn.close()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))