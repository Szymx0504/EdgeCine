# 🎬 EdgeCine: Semantic Discovery Engine

[![Tech Stack: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vector DB: pgvector](https://img.shields.io/badge/Vector_DB-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Inference: ONNX Runtime](https://img.shields.io/badge/Inference-ONNX_Runtime-00599C?style=flat-square&logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Deployment: Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

EdgeCine is a search engine built to explore edge-optimized semantic vectorization. Instead of basic keyword matching, it maps metadata (plots, tags, directors) into a 384-dimensional latent space.

The goal was to achieve high-performance, local AI inference on standard CPU hardware. By avoiding external APIs, I kept the end-to-end search latency well under 100ms.

---

## Technical Overview

### 1. ONNX Runtime & Edge Optimization
- **Local Inference:** Vector embeddings are generated entirely locally within the FastAPI backend.
- **PyTorch to ONNX:** The `sentence-transformers/all-MiniLM-L6-v2` model was converted from PyTorch to an ONNX graph, resulting in a ~3x speedup in query-to-vector time.
- **Quantization (FP32 vs INT8):** The project supports hot-swapping between standard FP32 weights and an INT8 quantized model. Dynamic INT8 quantization reduces the model footprint from ~91MB to ~23MB. This makes it suitable for memory-constrained edge devices (e.g. Raspberry Pi) at the cost of slight CPU overhead for scaling calculations.

### 2. Hybrid Search in PostgreSQL
- **Semantic Search:** Uses the `pgvector` extension to calculate the Cosine Distance (`<=>`) between the user's query vector and the pre-computed movie vectors.
- **Fallback Search:** Implements standard PostgreSQL Full-Text Search (FTS) using English stemming as a reliable fallback for highly specific name or keyword queries.
- **Ranking System:** Final results are sorted by a custom algorithm that combines semantic distance with log-weighted popularity metrics (likes and ratings).

### 3. Monitoring & Tooling
- **Search CLI:** A professional terminal-based search utility (`scripts/search_cli.py`) for engineers to test the neural engine directly from the command line.
- **Agentic Insights:** A narrative reason engine that generates randomized, context-aware justifications for every recommendation, simulating real-time AI reasoning.
- **Dockerized Architecture:** The entire stack (Database, Backend, Frontend) is containerized for consistent deployment across Linux/WSL environments. The Docker build process is heavily optimized, utilizing CPU-only PyTorch wheels to drastically reduce image bloat and build times.

---

## Installation & Setup

You will need **Docker** and **Docker Compose**. If you are on Windows, ensure the Docker WSL2 backend is enabled.

```bash
# 1. Clone the repository
git clone https://github.com/Szymx0504/EdgeCine.git
cd EdgeCine
```

### Running the Application

This project supports two execution modes via Docker Compose:

*   **Development Mode (Default)**: Includes Hot-Reloading for fast development. Any code changes in the `app/` directory will be reflected instantly.
    ```bash
    docker compose up -d --build
    ```
*   **Production Context**: Runs the application with frozen code and optimized workers.
    ```bash
    docker compose -f docker-compose.yml up -d --build
    ```

### Running Tests
To verify the system integrity (Neural Engine, API, RRF logic):
```bash
docker compose exec backend pytest tests/
```

The web interface will be available at [http://localhost:8080](http://localhost:8080).

### 🛠️ Data Bootstrapping
On a fresh installation, the database is seeded with raw metadata. You MUST generate the vector embeddings to enable semantic search:
```bash
# Generate 384-d embeddings for all 8,800 films (Local Inference)
docker compose exec backend python3 /app/backend/generate_embeddings.py
```
*Note: This process takes 3-5 minutes on a standard CPU as it performs local transformer inference.*

### 🛠️ CLI Search Tool
A dedicated utility for engineering-level verification of the inference engine:
```bash
# Run a neural search from the terminal
python scripts/search_cli.py "love" --limit 3
```

To benchmark the quantized model, you can switch the inference engine by modifying the `.env` file or `docker-compose.yml`:
```yaml
environment:
  - ONNX_VARIANT=INT8
```

---

## Documentation & Benchmarks

- **[Inference Latency & Quantization Report](docs/latency_report.md)**: A breakdown of PyTorch vs. ONNX performance and the trade-offs of dynamic INT8 quantization.
- **[System Architecture](docs/architecture.md)**: Technical details on vector mathematics, hybrid search layering, and deployment architecture.
