# Database Schema

## ERD (Mermaid)

```mermaid
erDiagram
    users {
        serial id PK
        varchar name "Unique"
        varchar password_hash
    }

    tags {
        serial id PK
        varchar name "Unique"
    }

    users_tags {
        int user_id PK, FK
        int tag_id PK, FK
    }

    movies {
        serial id PK
        int duration_minutes
        bool is_short_movie
    }

    series {
        serial id PK
        int seasons_count
        bool is_miniseries
    }

    films {
        serial id PK
        varchar type
        varchar title
        varchar director
        varchar country
        date date_added
        int release_year
        varchar rating
        text description
        tsvector search_vector
        vector embedding
        int movie_id FK
        int series_id FK
    }

    actors {
        serial id PK
        varchar name
        varchar surname
    }

    films_actors {
        int film_id PK, FK
        int actor_id PK, FK
    }

    films_tags {
        int film_id PK, FK
        int tag_id PK, FK
    }

    user_interactions {
        bigserial id PK
        int user_id FK
        int film_id FK
        varchar interaction_type
        timestamp interaction_timestamp
    }

    users ||--o{ users_tags : ""
    tags ||--o{ users_tags : ""
    
    films ||--o{ films_tags : ""
    tags ||--o{ films_tags : ""
    
    films ||--o{ films_actors : ""
    actors ||--o{ films_actors : ""
    
    films ||--o{ user_interactions : ""
    users ||--o{ user_interactions : ""
    
    films }o--|| movies : ""
    films }o--|| series : ""
```

## Details
- **embeddings**: `vector(384)` for semantic search (all-MiniLM-L6-v2).
- **search_vector**: `tsvector` column for PostgreSQL Full-Text Search fallback.
- **constraints**: `films` table uses a `one_type_only` check to ensure strict typing between movies and series.
