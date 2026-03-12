# Performance & Optimization Notes

## 1. Indexing Strategy

We implemented three purposeful indexes to address specific query patterns in the application:

### a) Full-Text Search Index (`idx_films_search_vector`)
- **Type**: GIN (Generalized Inverted Index)
- **Target**: `films(search_vector)`
- **Purpose**: Powering the search bar functionality.
- **Why**: Standard B-Tree indexes are poor for partial text matching. A GIN index on a `tsvector` column allows for extremely fast full-text search queries (e.g., finding "Space" in title or description), crucial for our `GET /films/search` endpoint.

### b) Title Lookup Index (`idx_films_title`)
- **Type**: B-Tree (Standard)
- **Target**: `films(title)`
- **Purpose**: Exact title lookups and sorting.
- **Why**: We frequently sort by title or look up specific movies. Indexing this column avoids full table scans during alphabetical sorting.

### c) Foreign Key Index (`idx_user_interactions_user_id`)
- **Type**: B-Tree
- **Target**: `user_interactions(user_id)`
- **Purpose**: Optimizing the "User Profile" view.
- **Why**: The Profile page (`GET /users/{id}/interactions`) filters the massive `user_interactions` table by `user_id`. Without this index, every profile load would require scanning the entire interactions history table, which grows rapidly.

## 2. Views for Analytics
`v_model_training_triplets`
- Aggregates user interaction data.
- **Benefit**: Encapsulates complex logic (weighting different interaction types) into a clean view, ensuring consistency for any downstream ML models or reporting tools.
