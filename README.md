# 🎬 MovieRecommender: High-Performance Semantic Discovery Engine

[![Tech Stack: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vector DB: pgvector](https://img.shields.io/badge/Vector_DB-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Inference: ONNX Runtime](https://img.shields.io/badge/Inference-ONNX_Runtime-00599C?style=flat-square&logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Edge AI: Quantized INT8](https://img.shields.io/badge/Edge_AI-Quantized_INT8-4CC61E?style=flat-square)](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)

A high-performance semantic search platform designed for edge-ready AI inference. This project moves beyond simple keyword matching by mapping over 8,000 films into a **384-dimensional latent space**, enabling conceptual discovery with sub-100ms latency on standard CPU hardware.

---

## 🚀 Key Engineering Features

### 1. Hardware-Aware AI Inference (ONNX)
- **Compiling vs. Interpreting:** Instead of standard PyTorch, we use **ONNX Runtime** to "compile" the model graph, achieving a **2x speedup** in query-to-vector transformation.
- **In-process Inference:** Vectorization happens directly in the FastAPI process, eliminating the need for expensive external LLM API calls.
- **Quantization Support:** Features built-in support for **FP32** (High Precision) and **INT8** (Memory Optimized) model variants, demonstrating readiness for constrained edge hardware.

### 2. Hybrid Search Architecture
Utilizes a multi-layered discovery strategy implemented in PostgreSQL:
- **Primary:** Semantic Vector Similarity using `pgvector` and **Cosine Distance (`<=>`)**.
- **Secondary:** PostgreSQL Full-Text Search (FTS) with English-stemming for exact keyword reliability.
- **Scoring Engine:** A custom ranking algorithm that blends semantic relevance with popularity (likes) and average user ratings using log-weighted normalization.

### 3. Neural Monitor & Telemetry
The UI features a real-time **Neural Monitor** that exposes low-level performance metrics:
- **Inference Latency:** Direct visibility into the model execution time.
- **Engine Trace:** Verification of the vector engine and model precision (FP32/INT8).

---

## 🛠 Tech Stack

- **Backend:** Python (FastAPI), SQLAlchemy (Psycopg2), transformers.
- **Vector Intelligence:** PostgreSQL + `pgvector`.
- **Optimization:** ONNX Runtime, NumPy, Torch (CPU-only build).
- **Frontend:** React + Vite, Tailwind CSS, Lucide icons.
- **Infrastructure:** Docker Compose (Automated WSL/Linux deployment).

---

## 🔧 Installation & "Neural" Setup

Clone the repository and ensure you have **Docker Desktop** (with WSL2 backend if on Windows).

```bash
# 1. Clone and launch (Optimized CPU Path)
git clone https://github.com/your-repo/movieRecommender.git
cd movieRecommender
docker-compose up -d --build
```

Access the **Neural Discovery Engine** at [http://localhost](http://localhost).

---

## 🔬 System Deep-Dive
*For detailed information on the vector mathematics, mean-pooling logic, and the "Ghost Code" debugging case study, please refer to the internal documentation:*
👉 **[Architecture Walkthrough & Interview Guide](./docs/walkthrough.md)**

---
*Created for the Antmicro Internship Application 2026.*
