-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add a vector column to the films table.
-- all-MiniLM-L6-v2 outputs embeddings with 384 dimensions.
ALTER TABLE films ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Create a HNSW (Hierarchical Navigable Small World) index for fast cosine distance (<->) searches.
-- Note: You need to have some data in the table for the index to be fully effective, but it can be created upfront.
CREATE INDEX IF NOT EXISTS films_embedding_idx ON films USING hnsw (embedding vector_cosine_ops);
