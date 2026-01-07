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
            SELECT 
                f.id, 
                f.title, 
                COUNT(CASE WHEN ui.interaction_type = 'like' THEN 1 END) as likes,
                ROUND(AVG(
                    CASE 
                        WHEN ui.interaction_type LIKE 'rate_%' 
                        THEN CAST(SPLIT_PART(ui.interaction_type, '_', 2) AS INTEGER) 
                        ELSE NULL 
                    END
                ), 1) as avg_rating
            FROM films f
            LEFT JOIN user_interactions ui ON f.id = ui.film_id
            GROUP BY f.id
            ORDER BY likes DESC, avg_rating DESC
            LIMIT 20;
        """

        cur.execute(query)
        movies = cur.fetchall()

        cur.close()
        conn.close()
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/films/recommend")
def recommend_films(q: str = Query(..., min_length=1), skip: int = 0, limit: int = Query(20, le=100)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # First try: websearch_to_tsquery (AND logic by default)
        query = """
            SELECT 
                f.id, f.title, f.release_year, f.type, f.description,
                ts_rank(f.search_vector, websearch_to_tsquery('english', %s)) as rank,
                (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                (SELECT ROUND(AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER)), 1) 
                 FROM user_interactions ui 
                 WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating
            FROM films f
            WHERE f.search_vector @@ websearch_to_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s OFFSET %s;
        """

        cur.execute(query, (q, q, limit, skip))
        rows = cur.fetchall()
        
        # Fallback: if no results, try OR logic with plainto_tsquery on each word
        if not rows:
            words = [w.strip() for w in q.split() if len(w.strip()) >= 2]
            if words:
                # Build OR query: word1 | word2 | word3
                or_query = " | ".join(words)
                fallback_query = """
                    SELECT 
                        f.id, f.title, f.release_year, f.type, f.description,
                        ts_rank(f.search_vector, to_tsquery('english', %s)) as rank,
                        (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                        (SELECT ROUND(AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER)), 1) 
                         FROM user_interactions ui 
                         WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating
                    FROM films f
                    WHERE f.search_vector @@ to_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s OFFSET %s;
                """
                cur.execute(fallback_query, (or_query, or_query, limit, skip))
                rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "year": r[2],
                "type": r[3],
                "description": r[4],
                "rank": r[5],
                "likes": r[6],
                "avg_rating": r[7]
            })
        
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database error during recommendation")

@app.get("/films/search")
def search_films(query: str = Query(None, min_length=1), skip: int = 0, limit: int = Query(20, le=100)):
    """
    Search films by title or description.
    Handles multi-word queries with fallback:
    1. Try full-text search with AND (all words must match)
    2. If no results, fallback to OR (any word matches)
    """
    if not query:
        return []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Split query into words and filter out very short ones
        words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
        
        if not words:
            return []

        # Build the full-text search query using PostgreSQL tsquery
        # First try: AND all words together
        ts_query_and = " & ".join(words)
        
        query_fts = """
            SELECT 
                f.id, f.title, f.release_year, f.type, f.description,
                (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                (SELECT ROUND(AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER)), 1) 
                 FROM user_interactions ui 
                 WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating,
                ts_rank(f.search_vector, plainto_tsquery('english', %s)) as rank
            FROM films f
            WHERE f.search_vector @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC, f.release_year DESC
            LIMIT %s OFFSET %s;
        """
        
        cur.execute(query_fts, (query, query, limit, skip))
        rows = cur.fetchall()
        
        # Fallback: if no FTS results, try ILIKE with OR logic on each word
        if not rows:
            conditions = []
            params = []
            for word in words:
                conditions.append("(f.title ILIKE %s OR f.description ILIKE %s)")
                params.extend([f"%{word}%", f"%{word}%"])
            
            where_clause = " OR ".join(conditions)
            
            query_fallback = f"""
                SELECT 
                    f.id, f.title, f.release_year, f.type, f.description,
                    (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                    (SELECT ROUND(AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER)), 1) 
                     FROM user_interactions ui 
                     WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating,
                    0 as rank
                FROM films f
                WHERE {where_clause}
                ORDER BY f.release_year DESC
                LIMIT %s OFFSET %s;
            """
            params.extend([limit, skip])
            cur.execute(query_fallback, tuple(params))
            rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "title": r[1],
                "year": r[2],
                "type": r[3],
                "description": r[4],
                "likes": r[5],
                "avg_rating": r[6]
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
        
        # Get like count and average rating
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN interaction_type = 'like' THEN 1 END) as likes,
                ROUND(AVG(
                    CASE 
                        WHEN interaction_type LIKE 'rate_%%' 
                        THEN CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER) 
                        ELSE NULL 
                    END
                ), 1) as avg_rating
            FROM user_interactions 
            WHERE film_id = %s
        """, (film_id,))
        stats = cur.fetchone()
        likes = stats['likes']
        avg_rating = stats['avg_rating']
        
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
            "likes": likes,
            "avg_rating": avg_rating
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Username already exists")
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
            SELECT ui.id, ui.film_id, ui.interaction_type, 
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
            INSERT INTO user_interactions (user_id, film_id, interaction_type) 
            VALUES (%s, %s, %s) 
            RETURNING id, user_id, film_id, interaction_type, interaction_timestamp
        """
        cur.execute(query, (
            interaction.user_id, 
            interaction.film_id, 
            interaction.interaction_type
        ))
        new_interaction = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        return new_interaction
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        if not update_fields:
             raise HTTPException(status_code=400, detail="No fields to update")
             
        params.append(interaction_id)
        query = f"UPDATE user_interactions SET {', '.join(update_fields)} WHERE id = %s RETURNING id, user_id, film_id, interaction_type, interaction_timestamp"
        
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