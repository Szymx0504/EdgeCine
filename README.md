# 🎬 EdgeCine: Edge-Optimized Semantic Discovery Engine

[![Tech Stack: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vector DB: pgvector](https://img.shields.io/badge/Vector_DB-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Inference: ONNX Runtime](https://img.shields.io/badge/Inference-ONNX_Runtime-00599C?style=flat-square&logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Edge AI: Linux & Docker](https://img.shields.io/badge/Deployment-Linux_|_Docker-2496ED?style=flat-square&logo=linux&logoColor=white)](https://www.docker.com/)

EdgeCine is a high-performance semantic search platform engineered for **Edge AI and constrained environments**. Moving beyond simple keyword matching, this project maps over 8,000 films into a 384-dimensional latent space.

Designed with **model runtime optimization** and **deployment scalability** in mind, EdgeCine achieves **sub-10ms inference latency** on standard CPU hardware using ONNX execution providers, with built-in support for **INT8 Quantization**.

---

## 🚀 Key Engineering Features

### 1. Deep Learning Model Runtime Optimization (ONNX)
- **PyTorch to ONNX Pipeline:** The core `sentence-transformers/all-MiniLM-L6-v2` model was exported from PyTorch to an ONNX computational graph, achieving a **3.22x speedup** in query-to-vector transformation over the baseline PyTorch implementation.
- **Edge AI Portability (INT8 Quantization):** Features built-in support for switching between **FP32** (High Precision) and **INT8** (Memory Optimized) model variants. 
  - Dynamic INT8 quantization reduces the model footprint by **75%** (from ~91MB to ~23MB), making it viable for memory-constrained edge edge devices (e.g., Raspberry Pi, specialized SoCs).
- **In-process Inference:** Vectorization happens entirely locally within the FastAPI process, eliminating dependencies on high-latency, proprietary Cloud API endpoints.

👉 **Deep Dive:** See the [docs/latency_report.md](docs/latency_report.md) for a detailed benchmark breakdown of FP32 vs. INT8 execution times and quantization overhead.

### 2. Hybrid Search Architecture with pgvector
Utilizes a multi-layered discovery strategy implemented natively in PostgreSQL, minimizing I/O bottlenecks:
- **Primary:** Semantic Vector Similarity using `pgvector` and **Cosine Distance (`<=>`)** operators for true conceptual matching.
- **Secondary:** PostgreSQL Full-Text Search (FTS) with English-stemming acting as a deterministic fallback.
- **Scoring Engine:** A custom ranking algorithm blending semantic cosine similarity with exponential popularity weights (likes and ratings).

### 3. Linux-First Deployment & Telemetry
- **Deterministic Builds:** Fully containerized using Docker, enabling consistent deployment across Linux desktops and edge nodes. The `Dockerfile` is highly optimized, stripping away heavy CUDA dependencies for a pure CPU build path.
- **Neural Monitor:** The UI features a real-time **Neural Monitor** that exposes low-level runtime metrics directly to the user viewport:
  - **Inference Latency:** Direct visibility into the ONNX session execution time.
  - **Engine Trace:** Verification of the execution provider and model precision level (FP32/INT8).

---

## 🛠 Open Source Tech Stack

- **Deep Learning / ML:** PyTorch (conversion), ONNX Runtime, HuggingFace Transformers.
- **Backend:** Python (FastAPI), SQLAlchemy (Psycopg2).
- **Vector Intelligence:** PostgreSQL + `pgvector`.
- **Operating System / Deployment:** Linux (WSL2), Docker Compose.
- **Frontend:** React + Vite, Tailwind CSS.

---

## 🔧 Installation & "Neural" Setup

Clone the repository and ensure you have **Docker Compose** installed on your Linux host (or WSL2).

```bash
# 1. Clone and sync
git clone https://github.com/your-username/ EdgeCine.git
cd EdgeCine

# 2. Build and launch (Optimized CPU Path)
docker-compose up -d --build
```

Access the **Neural Discovery Engine** at [http://localhost](http://localhost).
To test edge footprint optimizations, switch the backend variant in `docker-compose.yml`:
```yaml
environment:
  - ONNX_VARIANT=INT8
```

---

## 🔬 System Documentation & Case Studies
- 👉 **[Architecture Walkthrough & Interview Guide](./docs/walkthrough.md)**: A detailed look at the vector mathematics, mean-pooling logic, and a case study on resolving WSL/Windows filesystem "Split-Brain" deployment bugs.
- 👉 **[Inference Latency Report](./docs/latency_report.md)**: PyTorch vs. ONNX benchmarks and quantization trade-off analysis.

---
*Developed by Szymon — Optimized for the Antmicro AI Internship 2026. Aligned with passions for Open Source, Runtime Optimization, and Edge AI.*
