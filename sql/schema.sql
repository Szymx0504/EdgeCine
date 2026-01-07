
-- Drop tables in reverse order of dependency to avoid errors
drop table if exists users_tags;
drop table if exists films_actors;
drop table if exists films_tags;
drop table if exists user_interactions cascade;

drop table if exists users cascade;
-- cascade should handle dependent foreign keys, but explicit drops above are safer
drop table if exists tags cascade;
drop table if exists films cascade;
drop table if exists movies cascade;
drop table if exists series cascade;
drop table if exists actors cascade;

create table users(
	id serial primary key,
	name varchar(64) not null unique,
	password_hash varchar(255) not null
);

create table tags(
	id serial primary key,
	name varchar(255) not null unique
);

create table users_tags(
	user_id int not null,
	tag_id int not null,

	primary key (user_id, tag_id),
	foreign key(user_id) references users(id) on delete cascade,
	foreign key(tag_id) references tags(id) on delete cascade
);

create table movies(
	id serial primary key,
	duration_minutes int,
	is_short_movie bool
);

create table series(
	id serial primary key,
	seasons_count int,
	is_miniseries bool
);

create table films(
	id serial primary key,
	type varchar(16) not null,
	title varchar(255) not null,
	director varchar(255),
	country varchar(255),
	date_added date,
	release_year int,
	rating varchar(32),
	description text,
	search_vector tsvector,

	movie_id int references movies(id) on delete cascade,
	series_id int references series(id) on delete cascade,

	constraint one_type_only
		check (
			(type = 'movie' and movie_id is not null and series_id is null) or
			(type = 'series' and series_id is not null and movie_id is null)
		)
);

-- Trigger to automatically update the search_vector whenever a film is inserted or updated
CREATE OR REPLACE FUNCTION films_search_vector_update() RETURNS trigger AS $$
BEGIN
  -- We concatenate title (A-weight: most important) and description (B-weight)
  NEW.search_vector :=
    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER films_search_vector_trigger
BEFORE INSERT OR UPDATE ON films
FOR EACH ROW EXECUTE FUNCTION films_search_vector_update();

create table actors(
	id serial primary key,
	name varchar(255) not null,
	surname varchar(255) not null
);

create table films_actors(
	film_id int not null,
	actor_id int not null,

	primary key (film_id, actor_id),
	foreign key(film_id) references films(id) on delete cascade,
	foreign key(actor_id) references actors(id) on delete cascade
);

create table films_tags(
	film_id int not null,
	tag_id int not null,

	primary key (film_id, tag_id),
	foreign key(film_id) references films(id) on delete cascade,
	foreign key(tag_id) references tags(id) on delete cascade
);

create table user_interactions(
	id bigserial primary key,
	user_id int not null,
	film_id int not null,
	interaction_type varchar(16) not null, -- like, rate_1, rate_2, rate_3, rate_4, rate_5
	interaction_timestamp timestamp with time zone default current_timestamp,

	foreign key(user_id) references users(id) on delete cascade,
	foreign key(film_id) references films(id) on delete cascade
);
