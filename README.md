# NetRecommender

A movie recommender web application built with FastAPI (Python) and React.

## Features

- 🎬 **Browse Top Movies** - See the most liked films in the community
- 🔍 **Search Films** - Find movies and series by title or description
- 🤖 **AI Recommendations** - Get personalized suggestions using natural language queries
- ❤️ **Like Films** - Save your favorite movies and build interaction history
- 👤 **User Profiles** - Manage your account and view your activity history

## Tech Stack

- **Backend**: Python FastAPI + PostgreSQL
- **Frontend**: React + Vite
- **Database**: PostgreSQL with Full-Text Search

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

## Setup

### 1. Clone and Configure

Create a `.env` file in the root folder:

```
DB_HOST=localhost
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432
```

### 2. Database Setup

Run the SQL scripts in order:

```bash
psql -h localhost -U postgres -d your_database_name -f sql/schema.sql
psql -h localhost -U postgres -d your_database_name -f sql/indexes.sql
psql -h localhost -U postgres -d your_database_name -f sql/views.sql
psql -h localhost -U postgres -d your_database_name -f sql/seed.sql
```

### 3. Backend

```bash
pip install fastapi uvicorn psycopg2-binary passlib
uvicorn app.backend.main:app --reload
```

### 4. Frontend

```bash
cd app/frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/movies/top` | Top 10 most liked films |
| GET | `/films/recommend?q=` | AI-powered recommendations |
| GET | `/films/search?q=` | Search by title/description |
| GET | `/films/{id}` | Film details with actors/tags |
| POST | `/users` | Register new user |
| POST | `/login` | User login |
| PUT | `/users/{id}` | Update user name |
| DELETE | `/users/{id}` | Delete user account |
| GET | `/users/{id}/interactions` | User's interaction history |
| POST | `/interactions` | Create interaction (like/view) |
| DELETE | `/interactions/{id}` | Remove interaction |
| GET | `/analytics/training-data` | ML training triplets view |

## Project Structure

```
movieRecommender/
├── app/
│   ├── backend/
│   │   ├── main.py          # FastAPI endpoints
│   │   ├── config.py        # Database configuration
│   │   └── schemas.py       # Pydantic models
│   └── frontend/
│       └── src/
│           ├── pages/       # Route components
│           ├── components/  # Reusable UI components
│           └── context/     # Auth context
├── schema.sql               # Database schema
├── indexes.sql              # Performance indexes
├── views.sql                # Reporting views
└── seed.sql                 # Sample data
```

## Database Design

- **Views**: v_model_training_triplets for ML training data

## M2 Conceptual Design
*(See `docs/M2_NOTES.md` and `diagrams/` folder)*

## Reflections
Building this application highlighted the challenge of bridging a normalized relational schema with a modern object-oriented frontend. Managing M:N relationships (like Tags) required careful API design. The use of Database Views proved excellent for decoupling the complex "interaction scoring" logic from the application code, allowing the backend to remain lean.
