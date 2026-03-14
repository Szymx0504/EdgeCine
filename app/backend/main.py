from fastapi import FastAPI, HTTPException, Query, Body, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from typing import List
import logging
import time

from .config import db_config
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    InteractionCreate, InteractionUpdate, InteractionResponse,
    FilmCreate, FilmResponse
)
from .config import hasher

import os
import torch
import onnxruntime as ort
from transformers import AutoTokenizer

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("edge-cine-api")

# Load Optimized ONNX Model at Startup (Edge AI Optimization)
logger.info("Initializing EdgeCine Neural Engine...")
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Model variant selection (FP32 vs INT8)
model_variant = os.getenv("ONNX_VARIANT", "FP32").upper()
# Resolve the absolute path to the 'app' directory
# Since main.py is in /app/backend, we only need to go up one directory to reach /app
base_dir = os.path.dirname(os.path.dirname(__file__))

if model_variant == "INT8":
    onnx_model_path = os.path.join(base_dir, "models", "v1-onnx-minilm", "model_int8.onnx")
else:
    onnx_model_path = os.path.join(base_dir, "models", "v1-onnx-minilm", "model.onnx")

logger.info(f"Using model variant: {model_variant} from {onnx_model_path}")

if os.path.exists(onnx_model_path):
    onnx_session = ort.InferenceSession(onnx_model_path, providers=['CPUExecutionProvider'])
    logger.info("ONNX Runtime session successfully initialized.")
else:
    logger.error(f"CRITICAL: ONNX model binary missing at {onnx_model_path}")
    onnx_session = None

def mean_pooling(token_embeddings, attention_mask):
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def generate_embedding(text: str):
    if not onnx_session:
        return None
    
    inputs = tokenizer(text, return_tensors="np", padding=True, truncation=True)
    ort_inputs = {
        'input_ids': inputs['input_ids'].astype('int64'),
        'attention_mask': inputs['attention_mask'].astype('int64'),
    }
    if 'token_type_ids' in inputs:
        ort_inputs['token_type_ids'] = inputs['token_type_ids'].astype('int64')
        
    start_time = time.time()
    ort_outs = onnx_session.run(None, ort_inputs)
    latency_ms = (time.time() - start_time) * 1000
    
    logger.info(f"ONNX Inference completed in {latency_ms:.2f}ms")
    
    last_hidden_state = torch.tensor(ort_outs[0])
    attention_mask = torch.tensor(inputs['attention_mask'])
    
    embedding_tensor = mean_pooling(last_hidden_state, attention_mask)
    embedding_tensor = torch.nn.functional.normalize(embedding_tensor, p=2, dim=1)
    return embedding_tensor[0].tolist()

def _extract_themes(text_list: list, query: str = ""):
    """Last-resort fallback theme extractor. Should rarely be used."""
    stopwords = {
        'series', 'movie', 'film', 'drama', 'based', 'young', 'world', 'life', 'story', 'charact', 
        'people', 'between', 'through', 'across', 'within', 'during', 'since', 'after', 'before',
        'against', 'along', 'about', 'above', 'below', 'around', 'executive', 'company', 'office',
        'group', 'their', 'them', 'these', 'those', 'where', 'when', 'which', 'while', 'whose',
        'entrepreneur', 'determined', 'success', 'business', 'leader', 'career', 'actually',
        'various', 'multiple', 'several', 'include', 'another', 'boozy', 'following', 'become',
        'special', 'losing', 'taking', 'getting', 'making', 'found', 'given', 'known', 'named',
        'called', 'often', 'still', 'always', 'really', 'might', 'himself', 'herself', 'themselves'
    }
    vibe_words = {
        'heart', 'warm', 'laugh', 'tension', 'adventure', 'thrill', 'dark', 'hope', 
        'friend', 'love', 'scary', 'spooky', 'unwind', 'relax', 'magic', 'mystery',
        'journey', 'brave', 'together', 'family', 'spirit', 'vibrant', 'gentle'
    }
    q_words = set(query.lower().split())
    word_scores = {}
    for text in text_list:
        words = [w.strip(".,()!?:;\"'").lower() for w in text.split() if len(w) > 4]
        for w in words:
            if any(sw == w[:len(sw)] for sw in stopwords): continue
            score = 1
            if any(v in w for v in vibe_words): score += 10
            if any(w.endswith(s) for s in ['ing', 'ive', 'ful', 'ous', 'ic', 'al']): score += 3
            if w in q_words: score -= 5
            word_scores[w] = word_scores.get(w, 0) + score
    sorted_themes = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_themes[:3]]

def generate_neural_insight(query: str, top_results: list):
    """Generates a mood-empathetic general insight. No theme extraction."""
    import random
    if not top_results:
        return "I've searched through the collection, but nothing quite matches that specific vibe yet."
    
    q_lower = query.lower()
    avg_score = sum(r.get('rank', 0.5) for r in top_results) / len(top_results)
    confidence = "strong" if avg_score > 0.7 else "moderate"
    count = len(top_results)
    
    # Mood detection
    is_laugh = any(w in q_lower for w in ['laugh', 'funny', 'comedy', 'joke', 'humor'])
    is_sad = any(w in q_lower for w in ['sad', 'lonely', 'blue', 'depress', 'down'])
    is_action = any(w in q_lower for w in ['excit', 'action', 'thrill', 'engag', 'fast'])
    is_chill = any(w in q_lower for w in ['relax', 'chill', 'calm', 'unwind', 'stress', 'tire'])
    is_scary = any(w in q_lower for w in ['scar', 'horror', 'creep', 'spook', 'dark'])
    
    # Empathetic greeting
    if is_sad and is_laugh:
        greet = random.choice([
            "I hear you — sometimes the best medicine is a good laugh.",
            "I'm sorry you're feeling down. Let's fix that with something uplifting.",
            "A mix of emotions calls for a mix of great comedy.",
            "I've got just the thing to brighten your day and bring on the laughs."
        ])
    elif is_sad:
        greet = random.choice([
            "I hope these can offer a little comfort.",
            "Here are some titles that might help brighten your evening.",
            "I picked these with warmth in mind.",
            "Take a deep breath. These stories might be exactly what you need.",
            "I've curated a gentle list for you right now.",
            "Sometimes watching a good story is the best way to process things."
        ])
    elif is_laugh:
        greet = random.choice([
            "Ready for a laugh? Here's what I found.",
            "These should put a smile on your face.",
            "I've prioritized high-rated comedies to keep things light.",
            "Searching for hilarity... here are the top matches.",
            "If you need a good chuckle, these are guaranteed to deliver.",
            "I've cleared the clutter. These are the funniest matches."
        ])
    elif is_action:
        greet = random.choice([
            "Buckle up — these are high-energy picks.",
            "I've tracked down some adrenaline-fueled matches.",
            "If you want edge-of-your-seat entertainment, look no further.",
            "These picks are fast-paced and highly engaging.",
            "I've isolated the most thrilling narratives in the database.",
            "Prepare for impact. These results scored massive synergy with action."
        ])
    elif is_chill:
        greet = random.choice([
            "Here are some easy-going picks to help you unwind.",
            "These should take the edge off — no stress required.",
            "Perfect background watching or a slow, immersive evening.",
            "I've tuned the algorithm to find atmospheric, relaxing content.",
            "Kick your feet up. These are the top chill matches.",
            "Escapism at its best. Here is a low-stakes lineup."
        ])
    elif is_scary:
        greet = random.choice([
            "Lights off? Here are your best bets for a thrill.",
            "I found some titles that should keep you on edge.",
            "Don't look behind you. These are the top horror alignments.",
            "I've tapped into the darker side of the catalog for these.",
            "These suggestions scored exceptionally high for suspense and fear.",
            "Get ready to jump. Here are the most unsettling matches."
        ])
    else:
        # Dynamic keyword insertion for generic queries
        q_words = [w.strip(".,()!?:;") for w in query.split() if len(w) > 3 and w.lower() not in ['this', 'that', 'with', 'about', 'some', 'find', 'show', 'movie', 'series']]
        if q_words and random.random() > 0.4:
            kw = random.choice(q_words).lower()
            greet = random.choice([
                f"I found some fascinating matches focusing on '{kw}'.",
                f"Here's what the embeddings pulled up regarding '{kw}'.",
                f"Analyzing your request for '{kw}' yielded these top results.",
                f"I've scanned the active vector space for the best '{kw}' content.",
                f"The neural model found a strong semantic link to '{kw}'.",
                f"I've optimized the search parameters around '{kw}'."
            ])
        else:
            greet = random.choice([
                "Here's what the neural engine found for you.",
                "I've analyzed your query and pulled up these matches.",
                "The semantic search algorithm has finalized these recommendations.",
                "I've cross-referenced your prompt with thousands of plot vectors.",
                "Here is your personalized lineup, freshly calculated.",
                "I bypassed standard keyword search and matched your actual intent.",
                "These titles possess the strongest mathematical correlation to your prompt."
            ])
    
    # Confidence suffix
    suffix = random.choice([
        f"Found {count} results with {confidence} semantic alignment.",
        f"{count} titles matched with {confidence} confidence.",
        f"Showing {count} results, ranked by vector proximity.",
        f"I've isolated {count} standout options for you.",
        f"Here are {count} films that hit the mark perfectly.",
        f"Reviewing the top {count} nearest neighbors in the latent space."
    ])
    
    header = random.choice([
        "Neural Insight",
        "AI Analysis",
        "Semantic Match Results",
        "Vector Search Findings",
        "Neural Network Report",
        "Deep Learning Highlights"
    ])
    if q_words and random.random() > 0.6:
        header = f"Analysis for '{random.choice(q_words).title()}'"
        
    return {
        "header": header,
        "text": f"{greet} {suffix}"
    }

def generate_movie_specific_insight(query: str, title: str, description: str, tags: list = None, used_templates: set = None):
    """Generates a per-movie reason using real tags + mood matching, ensuring variety."""
    import random
    if used_templates is None:
        used_templates = set()

    q_lower = query.lower()
    d_lower = description.lower()
    # Clean tags from awkward plural suffixes
    def clean_tag(t):
        t = t.lower()
        for suffix in [' tv shows', ' movies', ' features', ' series']:
            if t.endswith(suffix):
                t = t[:-len(suffix)]
        return t.strip()

    tag_names = [clean_tag(t) for t in (tags or [])]
    
    # --- Vibe Extraction Logic ---
    vibe_keywords = {
        "dark": ["dark", "murder", "twisted", "death", "grim", "noir", "shadow"],
        "heartwarming": ["heart", "touching", "feel-good", "inspiring", "warm", "hope"],
        "suspenseful": ["suspense", "tension", "thriller", "mystery", "edge", "clue"],
        "epic": ["epic", "journey", "vast", "war", "battle", "legend", "historic"],
        "whimsical": ["magic", "whimsical", "fantasy", "dream", "wonder", "odd"],
        "intense": ["intense", "brutal", "grit", "fighting", "explosive"],
        "thought-provoking": ["think", "mind", "psychological", "deep", "philosophy", "existential"]
    }
    
    found_vibes = [v for v, kws in vibe_keywords.items() if any(k in d_lower for k in kws)]
    vibe_prefix = random.choice(found_vibes).capitalize() + " " if found_vibes else ""
    # -----------------------------

    # 1. Tag-Based Reasoning (highest quality)
    if tag_names:
        # Match tags to mood
        is_laugh = any(w in q_lower for w in ['laugh', 'funny', 'comedy', 'joke', 'humor'])
        is_sad = any(w in q_lower for w in ['sad', 'lonely', 'blue', 'depress', 'down'])
        is_chill = any(w in q_lower for w in ['relax', 'chill', 'calm', 'unwind'])
        is_romance = any(w in q_lower for w in ['romance', 'love', 'kiss', 'date'])
        
        # Find relevant tags to highlight
        mood_tag_map = {
            'comed': is_laugh, 'stand-up': is_laugh,
            'drama': is_sad, 'emotion': is_sad,
            'romant': is_romance, 'feel-good': is_laugh or is_romance,
            'chill': is_chill, 'documentary': is_chill
        }
        
        highlighted = [t for t in tag_names if any(k in t for k, v in mood_tag_map.items() if v)]
        
        # Filter out overly generic overarching tags for display
        boring_tags = ['international', 'tv show', 'movie', 'feature']
        meaningful_tags = [t for t in tag_names if not any(b in t for b in boring_tags)]
        
        if highlighted:
            display_tags = highlighted[:2]
        elif meaningful_tags:
            display_tags = meaningful_tags[:2]
        else:
            display_tags = tag_names[:2]
            
        tag_str = " & ".join([t.title() for t in display_tags])
        
        
        options = [
            (1, f"A {vibe_prefix}{tag_str} story — a strong match for your request."),
            (2, f"This falls right into the {tag_str} category, with a {vibe_prefix.lower().strip() or 'unique'} tone."),
            (3, f"Fits your vibe: a classic {tag_str} with {vibe_prefix.lower().strip() or 'compelling'} elements."),
            (4, f"A prime example of {tag_str} storytelling that feels {vibe_prefix.lower().strip() or 'highly relevant'}."),
            (5, f"Leaning into the {vibe_prefix.lower().strip() or 'strong'} {tag_str} tropes that you'll appreciate."),
            (6, f"Selected for its {vibe_prefix.lower().strip() or 'masterful'} execution of the {tag_str} genre."),
            (7, f"The neural map flagged this as a {vibe_prefix.lower().strip() or 'relevant'} {tag_str} piece."),
            (8, f"This is widely recognized as a {vibe_prefix.lower().strip() or 'top-tier'} {tag_str}."),
            (9, f"If you're looking for {vibe_prefix.lower().strip() or 'quality'} {tag_str}, this is a great choice."),
            (10, f"Categorized as {tag_str}, it explores {vibe_prefix.lower().strip() or 'intriguing'} themes.")
        ]
        
        filtered_options = [o for o in options if o[0] not in used_templates]
        
        if not filtered_options:
            return f"A fantastic {vibe_prefix.lower()}{tag_str}."
            
        choice = random.choice(filtered_options)
        used_templates.add(choice[0])
        return choice[1]
    
    # 2. Direct word overlap
    d_clean = [w.strip(".,()!?:;").lower() for w in description.split() if len(w) > 4]
    q_words = [w.strip(".,()!?:;").lower() for w in query.split() if len(w) > 3]
    overlap = [w for w in d_clean if w in q_words]
    
    if overlap:
        word = overlap[0]
        return random.choice([
            f"Direct match on '{word}' from your search.",
            f"This one explores '{word}', which you mentioned."
        ])
    
    # 3. Mood matching from description
    is_lonely = any(m in q_lower for m in ['lonely', 'sad', 'blue', 'alone'])
    if is_lonely and any(kw in d_lower for kw in ['heart', 'touching', 'friend', 'hope', 'together', 'love', 'warm']):
        return random.choice([
            "A heartwarming story — good company for a quiet evening.",
            "This one's uplifting and gentle, perfect for right now."
        ])
        
    # 4. Generic confidence fallback
    return random.choice([
        "Ranked highly by the neural engine for semantic similarity.",
        "Strong vector match to the meaning behind your request.",
        "The AI found a deep connection between your query and this plot."
    ])

app = FastAPI(title="Netflix Data API")

# Setup a simple static API Key for protecting sensitive endpoints (like POST /films)
API_KEY = os.getenv("API_KEY", "super-secret-admin-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API Key"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(**db_config.get_connection_params())

@app.get("/health")
def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "onnx_model": "loaded" if onnx_session else "not_loaded",
            "database": "unknown"
        }
    }
    
    # Check Database Connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        health_status["services"]["database"] = "connected"
    except Exception as e:
        logger.error(f"Health check failed: Database unreachable. Error: {e}")
        health_status["services"]["database"] = "disconnected"
        health_status["status"] = "unhealthy"
    
    if onnx_session is None:
        logger.error("Health check failed: ONNX model session is None.")
        health_status["status"] = "unhealthy"
        
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
        
    return health_status

@app.get("/")
def read_root():
    return {
        "message": "EdgeCine Neural Search API",
        "version": "2.0.0-pro",
        "status": "active"
    }

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
def recommend_films(q: str = Query(..., min_length=1), skip: int = 0, limit: int = Query(6, le=100)):
    start_time = time.time()
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Step 1: Generate vector embedding for the search query
        query_embedding = generate_embedding(q)

        if query_embedding:
            # Vector Search Query (using Cosine Distance <=> or <->)
            # The smaller the distance, the more similar the vectors
            query = """
                WITH stats AS (
                    SELECT 
                        f.id,
                        (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                        (SELECT AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER))
                         FROM user_interactions ui 
                         WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating
                    FROM films f
                    WHERE f.embedding IS NOT NULL
                    ORDER BY f.embedding <=> %s::vector
                    LIMIT 200 -- Pre-filter top 200 closest vector matches before applying ranking
                )
                SELECT 
                    f.id, f.title, f.release_year, f.type, f.description,
                    (
                        -- Vector Similarity Score (1 - Cosine Distance)
                        (1.0 - (f.embedding <=> %s::vector)) * 2.0 + 
                        (LN(COALESCE(s.likes, 0) + 1) * 0.1) +
                        (CASE WHEN COALESCE(s.avg_rating, 0) > 3.0 THEN (s.avg_rating - 3.0) * 0.1 ELSE 0 END)
                    ) as rank,
                    COALESCE(s.likes, 0) as likes,
                    ROUND(COALESCE(s.avg_rating, 0), 1) as avg_rating
                FROM films f
                JOIN stats s ON f.id = s.id
                ORDER BY rank DESC
                LIMIT %s;
            """
            cur.execute(query, (query_embedding, query_embedding, limit))
            rows = cur.fetchall()
            
            if rows:
                results = []
                used_templates = set()
                for r in rows:
                    # Exponential/Linear mapping for MiniLM embeddings
                    # Raw rank (including bonuses) is usually around 0.6 - 1.2
                    raw_rank = r[5]
                    # This maps a 0.5 raw score -> 60% and 1.2 raw score -> 95%
                    calculated_rank = (raw_rank - 0.4) * 0.5 + 0.6
                    ui_rank = min(0.99, max(0.55, calculated_rank))
                    
                    # Fetch real tags for this film
                    cur.execute(
                        "SELECT t.name FROM films_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.film_id = %s",
                        (r[0],)
                    )
                    film_tags = [row[0] for row in cur.fetchall()]
                    
                    results.append({
                        "id": r[0],
                        "title": r[1],
                        "year": r[2],
                        "type": r[3],
                        "description": r[4],
                        "rank": ui_rank,
                        "likes": r[6],
                        "avg_rating": r[7],
                        "match_reason": generate_movie_specific_insight(q, r[1], r[4], tags=film_tags, used_templates=used_templates)
                    })
                
                insight_data = generate_neural_insight(q, results)
                
                return {
                    "results": results,
                    "neural_insight_header": insight_data["header"],
                    "neural_insight": insight_data["text"],
                    "telemetry": {
                        "inference_time_ms": round((time.time() - start_time) * 1000, 2),
                        "model_variant": model_variant,
                        "vector_engine": "PostgreSQL + pgvector (Cosine Similarity)"
                    }
                }

        # FALLBACK: Full-Text Keyword Search
        query = """
            WITH stats AS (
                SELECT 
                    f.id,
                    (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                    (SELECT AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER))
                     FROM user_interactions ui 
                     WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating
                FROM films f
                WHERE f.search_vector @@ websearch_to_tsquery('english', %s)
            )
            SELECT 
                f.id, f.title, f.release_year, f.type, f.description,
                (
                    ts_rank(f.search_vector, websearch_to_tsquery('english', %s)) +
                    (LN(COALESCE(s.likes, 0) + 1) * 0.1) +
                    (CASE WHEN COALESCE(s.avg_rating, 0) > 3.0 THEN (s.avg_rating - 3.0) * 0.1 ELSE 0 END)
                ) as rank,
                COALESCE(s.likes, 0) as likes,
                ROUND(COALESCE(s.avg_rating, 0), 1) as avg_rating
            FROM films f
            JOIN stats s ON f.id = s.id
            ORDER BY rank DESC
            LIMIT %s OFFSET %s;
        """

        cur.execute(query, (q, q, limit, skip))
        rows = cur.fetchall()
        
        if not rows:
            words = [w.strip() for w in q.split() if len(w.strip()) >= 2]
            if words:
                or_query = " | ".join(words)
                fallback_query = """
                    WITH stats AS (
                        SELECT 
                            f.id,
                            (SELECT COUNT(*) FROM user_interactions ui WHERE ui.film_id = f.id AND ui.interaction_type = 'like') as likes,
                            (SELECT AVG(CAST(SPLIT_PART(interaction_type, '_', 2) AS INTEGER))
                             FROM user_interactions ui 
                             WHERE ui.film_id = f.id AND ui.interaction_type LIKE 'rate_%%') as avg_rating
                        FROM films f
                        WHERE f.search_vector @@ to_tsquery('english', %s)
                    )
                    SELECT 
                        f.id, f.title, f.release_year, f.type, f.description,
                        (
                            ts_rank(f.search_vector, to_tsquery('english', %s)) +
                            (LN(COALESCE(s.likes, 0) + 1) * 0.1) +
                            (CASE WHEN COALESCE(s.avg_rating, 0) > 3.0 THEN (s.avg_rating - 3.0) * 0.1 ELSE 0 END)
                        ) as rank,
                        COALESCE(s.likes, 0) as likes,
                        ROUND(COALESCE(s.avg_rating, 0), 1) as avg_rating
                    FROM films f
                    JOIN stats s ON f.id = s.id
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
        return {
            "results": results,
            "neural_insight_header": "Text Search Match",
            "neural_insight": f"Keyword Search Fallback: I've found {len(results)} matches using traditional text similarity."
        }
    except Exception as e:
        logger.error(f"Recommendation Engine Error: {e}")
        raise HTTPException(status_code=500, detail="Database error during recommendation")

@app.post("/films", response_model=FilmResponse)
def create_film(film: FilmCreate, api_key: str = Depends(get_api_key)):
    """
    Creates a new film and IMMEDIATELY generates its vector embedding 'in the background' 
    using the ONNX model from the optimization step before saving to the database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Create the rich text representation for the model
        text_to_embed = f"{film.title} ({film.type}). {film.description}"
        
        # 2. Generate the embedding locally using ONNX (Real-Time Vectorization)
        embedding_list = generate_embedding(text_to_embed)

        # 3. Insert the film into the database along with its pre-calculated embedding
        # Notice we cast the list to `::vector` for pgvector
        query = """
            INSERT INTO films (
                title, type, director, country, release_year, 
                rating, duration, listed_in, description, embedding
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) 
            RETURNING id, title, type, description
        """
        
        cur.execute(query, (
            film.title, 
            film.type, 
            film.director, 
            film.country, 
            film.release_year,
            film.rating, 
            film.duration, 
            film.listed_in, 
            film.description, 
            embedding_list
        ))
        
        new_film = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        return new_film
    except Exception as e:
        logger.error(f"Create Film Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

        words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
        
        if not words:
            return []
        
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
        logger.error(f"Search API Error: {e}")
        raise HTTPException(status_code=500, detail="Błąd połączenia z bazą danych")

@app.get("/films/{film_id}")
def get_film_details(film_id: int):
    """Get full details of a single film including actors and tags."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
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
        
        cur.execute("""
            SELECT a.name 
            FROM actors a
            JOIN films_actors fa ON a.id = fa.actor_id
            WHERE fa.film_id = %s
        """, (film_id,))
        actors = [row['name'] for row in cur.fetchall()]
        
        cur.execute("""
            SELECT t.name 
            FROM tags t
            JOIN films_tags ft ON t.id = ft.tag_id
            WHERE ft.film_id = %s
        """, (film_id,))
        tags = [row['name'] for row in cur.fetchall()]
        
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

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
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