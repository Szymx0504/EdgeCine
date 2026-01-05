-- Index for standard lookups by title
create index idx_films_title on films(title);

-- Index for user interactions (FK side, usually queried by user)
create index idx_user_interactions_user_id on user_interactions(user_id);

-- GIN Index for Full Text Search (Recommendation System)
create index idx_films_search_vector on films using gin(search_vector);