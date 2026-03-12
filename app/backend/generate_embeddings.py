import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from config import db_config

def mean_pooling(token_embeddings, attention_mask):
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def generate_embeddings_for_db(batch_size=32):
    print("Loading Transformers Model (PyTorch)...")
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    
    # Use multiple threads for faster CPU inference
    torch.set_num_threads(os.cpu_count() or 4)

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
        
        # Tokenize batch
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True)
        
        # Run PyTorch inference
        with torch.no_grad():
            outputs = model(**inputs)
            last_hidden_state = outputs.last_hidden_state
            
            # Pool and normalize the whole batch
            embeddings = mean_pooling(last_hidden_state, inputs['attention_mask'])
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        # Prepare data for bulk update
        update_data = []
        for j, film in enumerate(batch):
            emb_list = embeddings[j].tolist()
            update_data.append((emb_list, film['id']))

        # Bulk Update in Postgres
        with conn.cursor() as update_cur:
            execute_values(
                update_cur,
                "UPDATE films SET embedding = data.emb::vector FROM (VALUES %s) AS data(emb, id) WHERE films.id = data.id",
                update_data
            )
        
        if (i + len(batch)) % (batch_size * 5) == 0 or (i + len(batch)) == total:
            print(f"Processed {i + len(batch)}/{total} films...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    print("Done! All films have vector embeddings.")

if __name__ == "__main__":
    generate_embeddings_for_db(batch_size=64)
