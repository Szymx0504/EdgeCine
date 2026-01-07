import pandas as pd

from app.backend.config import hasher
import random
import string

df = pd.read_csv("netflix_titles.csv", sep=",")
df = df.dropna(subset=["listed_in", "title", "type"])
df["date_added"] = pd.to_datetime(df["date_added"], format="%B %d, %Y", errors="coerce")

actor_ids_map = {}
actor_inserts = []
all_actors = sorted(list(set([actor.strip() for row in df["cast"].dropna() for actor in row.split(",")])))
for i, actor in enumerate(all_actors):
    actor_id = i + 1
    actor_ids_map[actor] = actor_id # to make use of it in other tables
    split = actor.split(" ", 1)
    # Truncate to 255 chars to fit schema
    name = split[0].replace("'", "''")[:255]
    surname = (split[1].replace("'", "''") if len(split) > 1 else "N/A")[:255]
    query = f"INSERT INTO actors (id, name, surname) VALUES ({actor_id}, '{name}', '{surname}');"
    actor_inserts.append(query)

# movie_ids_map = {}
movie_inserts = []
movies = df[df["type"] == "Movie"].copy()[["rating", "duration"]]
movies["duration"] = movies["duration"].str.split(" ").str[0].astype(int)
movies["is_short_movie"] = movies["duration"] < 45
for i, movie in movies.iterrows():
    movie_id = i + 1
    # movie_ids_map[movie] = movie_id
    duration_minutes = movie["duration"]
    is_short_movie = "TRUE" if movie["is_short_movie"] else "FALSE"
    query = f"INSERT INTO movies (id, duration_minutes, is_short_movie) VALUES ({movie_id}, {duration_minutes}, {is_short_movie});"
    movie_inserts.append(query)

# series_ids_map = {}
series_inserts = []
series = df[df["type"] == "TV Show"].copy()[["rating", "duration"]]
series["duration"] = series["duration"].str.split(" ").str[0].astype(int)
series["is_miniseries"] = series["duration"] == 1
for i, serie in series.iterrows():
    serie_id = i + 1
    # series_ids_map[serie] = serie_id
    seasons_count = serie["duration"]
    is_miniseries = "TRUE" if serie["is_miniseries"] else "FALSE"
    query = f"INSERT INTO series (id, seasons_count, is_miniseries) VALUES ({serie_id}, {seasons_count}, {is_miniseries});"
    series_inserts.append(query)

all_tags = sorted(list(set([tag.strip() for row in df["listed_in"].dropna() for tag in row.split(",")])))
tags_ids_map = {}
tags_inserts = []
for i, tag in enumerate(all_tags):
    tag_id = i + 1
    tags_ids_map[tag] = tag_id
    tag_clean = tag.replace("'", "''")[:255]
    query = f"INSERT INTO tags (id, name) VALUES ({tag_id}, '{tag_clean}');"
    tags_inserts.append(query)

films_inserts = []
films_actors_inserts = []
films_tags_inserts = []
for index, row in df.iterrows():
    film_id = index + 1
    type = f"'{"movie" if row["type"] == "Movie" else "series"}'"
    title = f"'{row["title"].replace("'", "''")}'"
    director = f"'{row["director"].replace("'", "''")}'" if pd.notna(row["director"]) else "NULL"
    country = f"'{row["country"].replace("'", "''")}'" if pd.notna(row["country"]) else "NULL"
    date_added = f"'{row["date_added"].date()}'" if pd.notna(row["date_added"]) else "NULL"
    release_year = row["release_year"] if pd.notna(row["release_year"]) else "NULL"
    rating = f"'{row["rating"].replace("'", "''")}'" if pd.notna(row["rating"]) else "NULL"
    description = f"'{row["description"].replace("'", "''")}'" if pd.notna(row["description"]) else "NULL"
    # sql = f"INSERT INTO films (type, title, director, country, date_added, release_year) VALUES ({type}, {title}, {director}, {country}, {date_added}, {release_year});"
    # commands.append(sql)
    columns_inserted = ["id", "type", "title", "director", "country", "date_added", "release_year", "rating", "description"]
    values_inserted = [film_id, type, title, director, country, date_added, release_year, rating, description]

    if row["type"] == "Movie":
        columns_inserted.append("movie_id")
        values_inserted.append(index+1)
    else:
        columns_inserted.append("series_id")
        values_inserted.append(index+1)
    
    sql = f"INSERT INTO films ({", ".join(columns_inserted)}) VALUES ({", ".join([str(item) for item in values_inserted])});"
    films_inserts.append(sql)

    if pd.notna(row["cast"]):
        #stripa trzeba dac przed set
        unique_actors_in_film = set([a.strip() for a in row["cast"].split(",")])
        for actor in unique_actors_in_film:
            actor_id = actor_ids_map[actor]
            query = f"INSERT INTO films_actors (film_id, actor_id) VALUES ({film_id}, {actor_id});"
            films_actors_inserts.append(query)
    
    if pd.notna(row["listed_in"]):
        unique_tags = set([t.strip() for t in row["listed_in"].split(",")])
        for tag in unique_tags:
            tag_id = tags_ids_map[tag]
            query = f"INSERT INTO films_tags (film_id, tag_id) VALUES ({film_id}, {tag_id});"
            films_tags_inserts.append(query)



# print("Movies distinct ratings:", set(df[df["type"] == "Movie"].loc[:, "rating"]))
# print("Series distinct ratings:", set(df[df["type"] == "TV Show"].loc[:, "rating"]))

import random
from datetime import datetime, timedelta

user_inserts = []
user_tags_inserts = []
user_interactions_inserts = []
names = ["Adam", "Ewa", "Marek", "Kasia", "Piotr", "Zuzia", "Jan", "Anna", "Robert", "Magda"]
surnames = ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński"]

popular_films_ids = list(range(1, 101)) 
# all_films_ids = list(range(1, len(df) + 1))
tag_to_films = {}
for tag_name, t_id in tags_ids_map.items():
    tag_to_films[t_id] = df[df['listed_in'].str.contains(tag_name, na=False)].index + 1

for u_id in range(1, 201):
    # Append ID to ensure unique usernames
    full_name = f"{random.choice(names)} {random.choice(surnames)} {u_id}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    password_hash = hasher.hash_password(password)
    user_inserts.append(f"INSERT INTO users (id, name, password_hash) VALUES ({u_id}, '{full_name}', '{password_hash}');")

    all_tag_ids = list(tags_ids_map.values())
    fav_tags = random.sample(all_tag_ids, k=random.randint(1, 3))
    for t_id in fav_tags:
        user_tags_inserts.append(f"INSERT INTO users_tags (user_id, tag_id) VALUES ({u_id}, {t_id});")

    personal_pool = []
    for t_id in fav_tags:
        personal_pool.extend(tag_to_films.get(t_id, []))
    potential_hits = random.sample(popular_films_ids, k=min(len(popular_films_ids), 10))
    potential_personal = random.sample(personal_pool, k=min(len(personal_pool), 10)) if personal_pool else []
    target_films = list(set(potential_hits + potential_personal))
    final_selection = random.sample(target_films, k=min(len(target_films), random.randint(5, 8)))

    # hits_to_watch = random.sample(popular_films_ids, k=random.randint(3, 5))
    # others_to_watch = random.sample(all_films_ids, k=random.randint(1, 3))
    # target_films = list(set(hits_to_watch + others_to_watch))

    for f_id in final_selection:
        # 30% chance of like, 70% chance of rating
        if random.random() < 0.3:
            act_type = 'like'
        else:
            rating = random.randint(1, 5)
            act_type = f'rate_{rating}'

        base_time = datetime.now() - timedelta(days=random.randint(1, 30))
        # Add some random variation to timestamp
        timestamp = (base_time + timedelta(minutes=random.randint(0, 1000))).strftime('%Y-%m-%d %H:%M:%S')
        
        query = f"INSERT INTO user_interactions (user_id, film_id, interaction_type, interaction_timestamp) " \
                f"VALUES ({u_id}, {f_id}, '{act_type}', '{timestamp}');"
        user_interactions_inserts.append(query)


with open("sql/seed.sql", "w", encoding="utf-8") as output:
    output.write("\\encoding UTF8\n\n")
    output.write("BEGIN;\n\n")
    output.write("\n".join(actor_inserts) + "\n")
    output.write("\n".join(movie_inserts) + "\n")
    output.write("\n".join(series_inserts) + "\n")
    output.write("\n".join(tags_inserts) + "\n")
    output.write("\n".join(films_inserts) + "\n")
    output.write("\n".join(films_actors_inserts) + "\n")
    output.write("\n".join(films_tags_inserts) + "\n")
    output.write("\n".join(user_inserts) + "\n")
    output.write("\n".join(user_tags_inserts) + "\n")
    output.write("\n".join(user_interactions_inserts) + "\n\n")
    output.write("-- Reset sequence to avoid duplicate key errors on new inserts\n")
    output.write("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));\n\n")
    output.write("COMMIT;\n")