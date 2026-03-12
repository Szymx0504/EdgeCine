# NetRecommender

A movie recommender web application built with FastAPI (Python) and React.

## Features

- **Browse Top Movies** - See the most liked films in the community
- **Search Films** - Find movies and series by title or description
- **AI Recommendations** - Get personalized suggestions using natural language queries
- **Edge-Ready Vector Search** - Local ONNX inference optimized for low-latency Discovery
- **Hybrid Search Architecture** - Tiered system combining Semantic Vectors with Full-Text FTS
- **Benchmarked Performance** - Verified latency gains and parity checks (see `/docs/latency_report.md`)
- **Like Films** - Save your favorite movies and build interaction history
- **User Profiles** - Manage your account and view your activity history

## Tech Stack

- **Backend**: Python FastAPI + PostgreSQL
- **AI/ML**: ONNX Runtime, Hugging Face Transformers, PyTorch
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
API_KEY=your_api_key
```

### 2. Database Setup

Run the SQL scripts in order (make sure the database exists first):

**Linux/macOS (Bash):**
```bash
# Load .env variables
export $(grep -v '^#' .env | xargs)

# Create the database
createdb -h $DB_HOST -U $DB_USER $DB_NAME

# Then run the scripts
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/schema.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/indexes.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/views.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/seed.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/add_vector_column.sql
```

**Windows (PowerShell):**
```powershell
# Load .env variables
Get-Content .env | Foreach-Object {
    $var = $_.Split('=', 2)
    Set-Item -Path "env:$($var[0])" -Value $var[1]
}

# Create the database
createdb -h $env:DB_HOST -U $env:DB_USER $env:DB_NAME

# Then run the scripts
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f sql/schema.sql
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f sql/indexes.sql
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f sql/views.sql
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f sql/seed.sql
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f sql/add_vector_column.sql
```

### 3. Backend Setup & Embeddings Generation

Make sure you have generated the ONNX optimization model first by running `optimization/embedder.py`.
Then, create a Python environment, install dependencies, and generate embeddings for your database.

**Linux/macOS:**
```bash
# 1. Create and activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate backfill vectors for existing films
python app/backend/generate_embeddings.py

# 4. Start the frontend API
uvicorn app.backend.main:app --reload
```

**Windows PowerShell:**
```powershell
# 1. Create and activate a Virtual Environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate backfill vectors for existing films
python app/backend/generate_embeddings.py

# 4. Start the frontend API
uvicorn app.backend.main:app --reload
```

### 4. Frontend

```bash
cd app/frontend
npm install
npm run dev
```

## Edge AI & Inference Optimization

To prepare the recommender for Edge environments and reduce latency, the embedding model was optimized for hardware acceleration:
- **Vector Embeddings**: Migrated from external APIs to a local `all-MiniLM-L6-v2` model.
- **ONNX Export**: Exported the PyTorch model to ONNX format (`model.onnx`) for cross-platform compatibility and efficient execution.
- **Inference Optimization**: Benchmarks show approximately **~1.9x speedup** when using ONNX Runtime (CPUExecutionProvider) over standard PyTorch inference, making the system responsive and resource-efficient for Edge devices.
See the `optimization/` directory for embedding generation and benchmark scripts.

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
│   ├── backend/             # FastAPI Engine & Vector Logic
│   └── frontend/            # React Discovery Interface
├── models/
│   └── v1-onnx-minilm/      # Versioned ML artifacts (ONNX/Data)
├── scripts/
│   ├── benchmark.py         # Performance & Parity Testing
│   └── embedder.py          # Data Vectorization Utility
├── sql/
│   ├── schema.sql           # Database schema
│   └── indexes.sql          # Performance (GIN/B-Tree)
└── docs/
    └── latency_report.md    # Optimization benchmarks
```

## Optimization & Performance
This project prioritizes local inference over external API calls to minimize latency and ensure privacy. By leveraging ONNX Runtime, the backend achieves significant speedups while maintaining 0.999+ numerical parity with the original transformer models. See [latency_report.md](file:///docs/latency_report.md) for full metrics.

## Database Design

- **Views**: v_model_training_triplets for ML training data
