# M1 — Problem Definition & Business Rules

## 1. Domain & Problem
**Domain:** Entertainment / Media Streaming  
**Problem:** Users are overwhelmed by the vast number of movies and series available. They need a system that not only allows them to browse and search but also provides recommendations based on their interests and past interactions.

## 2. User Stories
1. **As a User**, I want to register and log in so that I can save my history.
2. **As a User**, I want to browse "Top Movies" so I can see what is popular.
3. **As a User**, I want to search for films by title or description.
4. **As a User**, I want to ask for recommendations in natural language (e.g., "movies about space travel").
5. **As a User**, I want to "Like" or "Rate" a film (1-5 stars) to keep track of what I enjoyed.
6. **As a User**, I want to view my profile to see my interaction history.
7. **As a User**, I want to update my username or delete my account if I choose to leave.

## 3. Business Rules
1. **Users**: A user is identified by a unique ID. A user must have a username and password.
2. **Films**: A film can be either a Movie or a Series.
   - It must have a title and type.
   - It can optionally have a director, country, release year, rating, description, and duration.
3. **Interactions**:
   - A user can have many interactions with films.
   - A film can have many interactions from users.
   - An interaction is of a specific type ('view', 'like', 'add_to_list', 'skip', 'rate_1'...'rate_5').
   - A user cannot have multiple interactions of the same type for the same film (e.g., cannot "like" twice).
4. **Tags**: Films can be associated with multiple tags (M:N).
5. **Actors**: Films can be associated with multiple actors (M:N).
