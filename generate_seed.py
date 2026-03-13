import random
import string
import pandas as pd
from datetime import datetime, timedelta
import bcrypt

def to_batch_insert(table, columns, items, batch_size=100):
    """Generates batch INSERT statements for PostgreSQL."""
    if not items:
        return ""
    
    statements = []
    cols_str = ", ".join(columns)
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        values_str = ",\n    ".join(batch)
        statements.append(f"INSERT INTO {table} ({cols_str}) VALUES\n    {values_str};")
    
    return "\n\n".join(statements)

def format_val(val):
    """Formats a value for SQL insertion."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    # String handling
    s = str(val).replace("'", "''")
    return f"'{s}'"

df = pd.read_csv("netflix_titles.csv", sep=",")
df = df.dropna(subset=["listed_in", "title", "type"])
df["date_added"] = pd.to_datetime(df["date_added"], format="%B %d, %Y", errors="coerce")

# --- ACTORS ---
actor_items = []
actor_ids_map = {}
all_actors = sorted(list(set([actor.strip() for row in df["cast"].dropna() for actor in row.split(",")])))
for i, actor in enumerate(all_actors):
    actor_id = i + 1
    actor_ids_map[actor] = actor_id
    split = actor.split(" ", 1)
    name = split[0][:255]
    surname = (split[1] if len(split) > 1 else "N/A")[:255]
    actor_items.append(f"({actor_id}, {format_val(name)}, {format_val(surname)})")

# --- MOVIES ---
movie_items = []
movies = df[df["type"] == "Movie"].copy()
movies["duration_num"] = movies["duration"].str.split(" ").str[0].fillna(0).astype(int)
for i, movie in movies.iterrows():
    movie_id = i + 1
    movie_items.append(f"({movie_id}, {movie['duration_num']}, {format_val(movie['duration_num'] < 45)})")

# --- SERIES ---
series_items = []
series_df = df[df["type"] == "TV Show"].copy()
series_df["seasons"] = series_df["duration"].str.split(" ").str[0].fillna(0).astype(int)
for i, serie in series_df.iterrows():
    serie_id = i + 1
    series_items.append(f"({serie_id}, {serie['seasons']}, {format_val(serie['seasons'] == 1)})")

# --- TAGS ---
all_tags = sorted(list(set([tag.strip() for row in df["listed_in"].dropna() for tag in row.split(",")])))
tags_ids_map = {}
tags_items = []
for i, tag in enumerate(all_tags):
    tag_id = i + 1
    tags_ids_map[tag] = tag_id
    tags_items.append(f"({tag_id}, {format_val(tag[:255])})")

# --- FILMS & RELATIONS ---
film_items = []
films_actors_items = []
films_tags_items = []
for index, row in df.iterrows():
    film_id = index + 1
    is_movie = row["type"] == "Movie"
    
    movie_id = film_id if is_movie else None
    series_id = film_id if not is_movie else None
    
    vals = [
        film_id, 
        'movie' if is_movie else 'series',
        row["title"],
        row["director"],
        row["country"],
        row["date_added"].date() if pd.notna(row["date_added"]) else None,
        row["release_year"],
        row["rating"],
        row["description"],
        movie_id,
        series_id
    ]
    film_items.append(f"({', '.join([format_val(v) for v in vals])})")

    if pd.notna(row["cast"]):
        for actor in set([a.strip() for a in row["cast"].split(",")]) - {""}: # Added - {""} to handle empty strings from split
            if actor in actor_ids_map: # Ensure actor exists in map
                films_actors_items.append(f"({film_id}, {actor_ids_map[actor]})")
    
    if pd.notna(row["listed_in"]):
        for tag in set([t.strip() for t in row["listed_in"].split(",")]) - {""}: # Added - {""}
            if tag in tags_ids_map: # Ensure tag exists in map
                films_tags_items.append(f"({film_id}, {tags_ids_map[tag]})")

# --- USERS & INTERACTIONS ---
user_items = []
user_tags_items = []
user_interactions_items = []
names = ["Adam", "Ewa", "Marek", "Kasia", "Piotr", "Zuzia", "Jan", "Anna", "Robert", "Magda"]
surnames = ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński"]

popular_films_ids = list(range(1, min(101, len(df) + 1))) # Adjusted to be safe
tag_to_films = {}
for tag_name, t_id in tags_ids_map.items():
    tag_to_films[t_id] = (df[df['listed_in'].str.contains(tag_name, na=False, regex=False)].index + 1).tolist()

for u_id in range(1, 501):
    full_name = f"{random.choice(names)} {random.choice(surnames)} {u_id}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    # Direct bcrypt calls to avoid passlib bugs on Windows
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_items.append(f"({u_id}, {format_val(full_name)}, {format_val(password_hash)})")

    all_tag_ids = list(tags_ids_map.values())
    fav_tags = random.sample(all_tag_ids, k=random.randint(1, 3))
    for t_id in fav_tags:
        user_tags_items.append(f"({u_id}, {t_id})")

    personal_pool = []
    for t_id in fav_tags:
        personal_pool.extend(tag_to_films.get(t_id, []))
    
    potential_hits = random.sample(popular_films_ids, k=min(len(popular_films_ids), 20))
    potential_personal = random.sample(personal_pool, k=min(len(personal_pool), 20)) if personal_pool else []
    target_films = list(set(potential_hits + potential_personal))
    
    final_selection = random.sample(target_films, k=min(len(target_films), random.randint(5, 15)))

    for f_id in final_selection:
        act_type = 'like' if random.random() < 0.3 else f'rate_{random.randint(1, 5)}'
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))
        ts = (base_time + timedelta(minutes=random.randint(0, 1440))).strftime('%Y-%m-%d %H:%M:%S')
        user_interactions_items.append(f"({u_id}, {f_id}, '{act_type}', '{ts}')")


with open("sql/seed.sql", "w", encoding="utf-8") as out:
    out.write("\\encoding UTF8\n\n")
    out.write("BEGIN;\n\n")
    
    out.write("-- Actors\n")
    out.write(to_batch_insert("actors", ["id", "name", "surname"], actor_items) + "\n\n")
    
    out.write("-- Base Types\n")
    out.write(to_batch_insert("movies", ["id", "duration_minutes", "is_short_movie"], movie_items) + "\n\n")
    out.write(to_batch_insert("series", ["id", "seasons_count", "is_miniseries"], series_items) + "\n\n")
    
    out.write("-- Tags\n")
    out.write(to_batch_insert("tags", ["id", "name"], tags_items) + "\n\n")
    
    out.write("-- Films\n")
    out.write(to_batch_insert("films", ["id", "type", "title", "director", "country", "date_added", "release_year", "rating", "description", "movie_id", "series_id"], film_items) + "\n\n")
    
    out.write("-- Film Relations\n")
    out.write(to_batch_insert("films_actors", ["film_id", "actor_id"], films_actors_items, batch_size=200) + "\n\n")
    out.write(to_batch_insert("films_tags", ["film_id", "tag_id"], films_tags_items, batch_size=200) + "\n\n")
    
    out.write("-- Users\n")
    out.write(to_batch_insert("users", ["id", "name", "password_hash"], user_items) + "\n\n")
    out.write(to_batch_insert("users_tags", ["user_id", "tag_id"], user_tags_items, batch_size=200) + "\n\n")
    
    out.write("-- Interactions\n")
    out.write(to_batch_insert("user_interactions", ["user_id", "film_id", "interaction_type", "interaction_timestamp"], user_interactions_items, batch_size=200) + "\n\n")
    
    out.write("-- Reset identity sequences\n")
    out.write("SELECT setval('actors_id_seq', (SELECT MAX(id) FROM actors));\n")
    out.write("SELECT setval('movies_id_seq', (SELECT MAX(id) FROM movies));\n")
    out.write("SELECT setval('series_id_seq', (SELECT MAX(id) FROM series));\n")
    out.write("SELECT setval('tags_id_seq', (SELECT MAX(id) FROM tags));\n")
    out.write("SELECT setval('films_id_seq', (SELECT MAX(id) FROM films));\n")
    out.write("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));\n")
    out.write("SELECT setval('user_interactions_id_seq', (SELECT MAX(id) FROM user_interactions));\n\n")
    
    out.write("COMMIT;\n")