# 🎬 EdgeCine: Semantic Discovery Engine

[![Tech Stack: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vector DB: pgvector](https://img.shields.io/badge/Vector_DB-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Inference: ONNX Runtime](https://img.shields.io/badge/Inference-ONNX_Runtime-00599C?style=flat-square&logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Deployment: Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

A movie recommendation engine built to test and demonstrate edge-optimized semantic search. Instead of relying on simple keyword matching, the system maps movie metadata (descriptions, tags, directors) into a 384-dimensional vector space.

The primary goal of this project was to implement high-performance, local AI inference on standard CPU hardware without relying on external, slow APIs, keeping latency well under 100ms.

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
- **Real-Time Telemetry:** The frontend includes a monitor that displays inference latency, execution provider details, and precision metrics on every search interaction.
- **Dockerized Architecture:** The entire stack (Database, Backend, Frontend) is containerized for consistent deployment across Linux/WSL environments. The Docker build process is heavily optimized, utilizing CPU-only PyTorch wheels to drastically reduce image bloat and build times.

---

## Installation & Setup

You will need **Docker** and **Docker Compose**. If you are on Windows, ensure the Docker WSL2 backend is enabled.

```bash
# 1. Clone the repository
git clone https://github.com/Szymx0504/EdgeCine.git
cd EdgeCine

# 2. Build and launch the containers
docker-compose up -d --build
```

The web interface will be available at [http://localhost](http://localhost).

To benchmark the quantized model, you can switch the inference engine by modifying the `.env` file or `docker-compose.yml`:
```yaml
environment:
  - ONNX_VARIANT=INT8
```

---

## Documentation & Benchmarks

- **[Inference Latency & Quantization Report](docs/latency_report.md)**: A breakdown of PyTorch vs. ONNX performance and the trade-offs of dynamic INT8 quantization.
- **[System Architecture](docs/architecture.md)**: Technical details on vector mathematics, hybrid search layering, and deployment architecture.
