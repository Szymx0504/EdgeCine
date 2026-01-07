# M2 — Conceptual Modeling Notes

## Design Decisions

### 1. Inheritance for Films (Movies vs. Series)
We handle the distinction between Movies and Series using a "Table per Hierarchy" approach in the physical design, but conceptually they are subtypes of a `Film` entity.
- **Film** (Supertype): Title, Director, Country, Release Year, Rating, Description.
- **Movie** (Subtype): Duration (minutes), Is Short.
- **Series** (Subtype): Seasons Count, Is Miniseries.

### 2. M:N Relationships
Several Many-to-Many relationships were identified and resolved:
- **Films ↔ Actors**: A film has many actors; an actor plays in many films. Resolved via `films_actors`.
- **Films ↔ Tags**: A film has many tags (genres, keywords); a tag applies to many films. Resolved via `films_tags`.
- **Users ↔ Tags**: Users can have preferred tags. Resolved via `users_tags`.

### 3. User Interactions
Instead of separate tables for "Likes", "Ratings", and "Views", we consolidated these into a single `User_Interactions` entity.
- **Attributes**: `Interaction_Type` (Enum: like, view, rate_X), `Timestamp`, `Duration_Watched`.
- **Rationale**: This simplifies the schema and makes it easier to query a user's entire timeline or feed. It also allows for extensibility (e.g., adding a 'share' type later without new tables).

### 4. Search Vector
To support performance for text search, we decided to include a physical attribute `search_vector` on the `Film` entity, which is populated via a database trigger.
