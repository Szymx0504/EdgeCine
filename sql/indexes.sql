create index idx_films_title on films(title);
create index idx_user_interactions_user_id on user_interactions(user_id);
create index idx_films_search_vector on films using gin(search_vector);