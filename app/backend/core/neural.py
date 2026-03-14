import os
import torch
import logging
import time
import onnxruntime as ort
from transformers import AutoTokenizer
from pathlib import Path

logger = logging.getLogger("edge-cine-neural")

class NeuralEngine:
    """Handles local AI inference using ONNX Runtime."""
    
    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model_variant = os.getenv("ONNX_VARIANT", "FP32").upper()
        self.onnx_session = None
        
        # Resolve path
        base_dir = Path(__file__).resolve().parent.parent.parent
        if self.model_variant == "INT8":
            filename = "model_int8.onnx"
        else:
            filename = "model.onnx"
            
        self.onnx_model_path = base_dir / "models" / "v1-onnx-minilm" / filename
        self._initialize_session()

    def _initialize_session(self):
        if self.onnx_model_path.exists():
            try:
                self.onnx_session = ort.InferenceSession(
                    str(self.onnx_model_path), 
                    providers=['CPUExecutionProvider']
                )
                logger.info(f"Neural Engine initialized with {self.model_variant} variant.")
            except Exception as e:
                logger.error(f"Failed to load ONNX session: {e}")
        else:
            logger.error(f"ONNX model missing at {self.onnx_model_path}")

    def _mean_pooling(self, token_embeddings, attention_mask):
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def generate_batch_embeddings(self, texts: list[str]):
        """Generates normalized 384-d vectors for a batch of texts."""
        if not self.onnx_session:
            return []
        
        inputs = self.tokenizer(texts, return_tensors="np", padding=True, truncation=True)
        ort_inputs = {
            'input_ids': inputs['input_ids'].astype('int64'),
            'attention_mask': inputs['attention_mask'].astype('int64'),
        }
        if 'token_type_ids' in inputs:
            ort_inputs['token_type_ids'] = inputs['token_type_ids'].astype('int64')
            
        ort_outs = self.onnx_session.run(None, ort_inputs)
        
        last_hidden_state = torch.tensor(ort_outs[0])
        attention_mask = torch.tensor(inputs['attention_mask'])
        
        embeddings = self._mean_pooling(last_hidden_state, attention_mask)
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings.tolist()

    def generate_embedding(self, text: str):
        """Generates a normalized 384-d vector for the given text."""
        res = self.generate_batch_embeddings([text])
        return res[0] if res else None

# Singleton instance
engine = NeuralEngine()
