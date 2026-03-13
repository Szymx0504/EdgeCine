# System Architecture & Engineering Decisions

## 1. Core Engine: Semantic Vector Search
Traditional keyword search relies on exact string matching. This system implements a semantic search architecture utilizing a 384-dimensional latent space to discover content based on contextual meaning.

### Embedding Pipeline
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Data Ingestion:** Movie metadata (Title, Cast, Plot, Tags) is concatenated and processed into a unified vector representation.
- **Storage:** Vectors are stored in a PostgreSQL database using the `pgvector` extension.
- **Retrieval:** Queries are vectorized in real-time. The database computes the Cosine Distance (`<=>`) between the query vector and stored embeddings to mathematically identify the closest semantic matches.

## 2. Hardware Optimization & Run-Time

### ONNX Runtime Integration
To meet sub-100ms inference latency requirements without relying on GPU acceleration, the deep learning model was exported from PyTorch to an ONNX computational graph.
- This decoupling from the heavy PyTorch ecosystem reduces the Docker container footprint and accelerates CPU inference by executing an optimized, static mathematical graph.

### Dynamic INT8 Quantization
The system is designed to support both FP32 and INT8 model variants for edge deployment flexibility.
- **FP32:** Provides maximum numerical parity and the lowest absolute latency on standard x86 CPUs.
- **INT8:** Reduces the model's memory footprint by ~75% (from ~91MB to ~23MB) via dynamic quantization. While this introduces a minor CPU overhead for calculating activation scaling factors at runtime, it is a critical optimization for deploying the engine on memory-constrained edge hardware.

## 3. Hybrid Search & Reliability
To prevent search "blindspots" when dealing with highly specific noun queries (e.g., exact actor names or obscure titles that fall outside the semantic latent space), the system uses a tiered architecture:
1. **Primary Layer (Semantic):** pgvector Cosine Distance matching.
2. **Fallback Layer (Lexical):** PostgreSQL Full-Text Search (`tsvector` and `tsquery`) acting as a deterministic safety net.

## 4. Algorithmic Ranking & Variance
- **Ranking Engine:** Raw semantic distance is normalized and blended with historical popularity metrics (likes and average user ratings) using a log-weighted formula to prioritize highly-rated, relevant films.
- **Insight Generation:** A stateful `used_templates` tracker forces variance in natural language generation during a single transaction, preventing repetitive phrasing across a batch of recommendations.

## 5. Deployment Architecture
- **Environment:** Containerized via Docker Compose for strict parity across development (Windows/WSL) and target production (Linux) targets.
- **State Management:** Database initialization and vector schema setup are handled via automated SQL entrypoint execution.
