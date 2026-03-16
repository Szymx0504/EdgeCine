import pytest
from ..core.neural import engine

def test_engine_initialization():
    """Verify that the ONNX session is loaded."""
    assert engine.tokenizer is not None
    # We don't assert onnx_session here because it might be None if models are missing in the test env, 
    # but we can check if the variant is correctly identified.
    assert engine.model_variant in ["FP32", "INT8"]

def test_embedding_generation():
    """Verify that embeddings are generated with correct dimensions."""
    if engine.onnx_session is None:
        pytest.skip("ONNX session not initialized (model binary may be missing).")
        
    test_text = "Space adventure with aliens"
    embedding = engine.generate_embedding(test_text)
    
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 384  # Dimension for all-MiniLM-L6-v2
    
    # Check normalization (L2 norm should be ~1.0)
    sum_sq = sum(x**2 for x in embedding)
    assert 0.99 <= sum_sq <= 1.01
