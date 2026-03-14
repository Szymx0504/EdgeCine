import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
try:
    from .config import db_config
    from .core.neural import engine
except (ImportError, ValueError):
    from config import db_config
    from core.neural import engine


def generate_embeddings_for_db(batch_size=64):
    print(f"Loading Neural Engine (Variant: {engine.model_variant})...")
    
    print("Connecting to database...")
    conn = psycopg2.connect(**db_config.get_connection_params())
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT 
            f.id, f.title, f.type, f.description, f.director, f.country,
            STRING_AGG(DISTINCT t.name, ', ') AS tags,
            STRING_AGG(DISTINCT a.name || ' ' || a.surname, ', ') AS actors
        FROM films f
        LEFT JOIN films_tags ft ON f.id = ft.film_id
        LEFT JOIN tags t ON ft.tag_id = t.id
        LEFT JOIN films_actors fa ON f.id = fa.film_id
        LEFT JOIN actors a ON fa.actor_id = a.id
        WHERE f.embedding IS NULL
        GROUP BY f.id
        ORDER BY f.id
    """)
    all_films = cur.fetchall()
    total = len(all_films)
    print(f"Found {total} films without embeddings.")

    if not all_films:
        print("Database is already fully embedded!")
        cur.close()
        conn.close()
        return

    print(f"Inference started using ONNX Runtime (Batch Size: 1 for Edge compatibility)...")
    for i in range(0, total, batch_size):
        batch = all_films[i:i + batch_size]
        batch_texts = []
        for f in batch:
            text_parts = [f"Title: {f['title']} ({f['type']})."]
            if f['director']: text_parts.append(f"Director: {f['director']}.")
            if f['country']: text_parts.append(f"Country: {f['country']}.")
            if f['tags']: text_parts.append(f"Tags: {f['tags']}.")
            if f['actors']: text_parts.append(f"Cast: {f['actors']}.")
            if f['description']: text_parts.append(f"Plot: {f['description']}")
            batch_texts.append(" ".join(text_parts))
        
        # We use a batch of 1 here because our Edge-optimized ONNX model 
        # is exported with a fixed batch size to minimize memory footprint.
        # We still batch the database UPDATE operations for speed.
        embeddings = []
        for text in batch_texts:
            embeddings.append(engine.generate_embedding(text))
        
        # Prepare data for bulk update
        update_data = []
        for j, film in enumerate(batch):
            update_data.append((embeddings[j], film['id']))

        # Bulk Update in Postgres
        with conn.cursor() as update_cur:
            execute_values(
                update_cur,
                "UPDATE films SET embedding = data.emb::vector FROM (VALUES %s) AS data(emb, id) WHERE films.id = data.id",
                update_data
            )
        
        if (i + len(batch)) % 100 == 0 or (i + len(batch)) == total:
            print(f"Processed {i + len(batch)}/{total} films...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    print("Done! All films have vector embeddings.")

if __name__ == "__main__":
    generate_embeddings_for_db(batch_size=50) # Batching DB updates, not AI inference
