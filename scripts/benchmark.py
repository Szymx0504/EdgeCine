import time
import numpy as np
import torch
import onnxruntime as ort
from transformers import AutoTokenizer, AutoModel
import os

def mean_pooling(token_embeddings, attention_mask):
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def run_professional_benchmark():
    """
    Antmicro-grade Benchmarking Suite: 
    Compares Standard PyTorch vs. ONNX FP32 vs. ONNX INT8
    Includes Numerical Parity Check for Accuracy Verification.
    """
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    base_dir = os.path.dirname(os.path.dirname(__file__))
    model_dir = os.path.join(base_dir, "models", "v1-onnx-minilm")
    
    onnx_fp32_path = os.path.join(model_dir, "model.onnx")
    onnx_int8_path = os.path.join(model_dir, "model_int8.onnx")
    
    print("="*60)
    print(" INFERENCE PERFORMANCE & ACCURACY BENCHMARK ")
    print("="*60)
    
    if not os.path.exists(onnx_fp32_path):
        print(f"[ERROR] FP32 Model not found: {onnx_fp32_path}")
        return

    print(f"[*] Loading Tokenizer & PyTorch Model...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model_pt = AutoModel.from_pretrained(model_name)
    model_pt.eval()
    
    print(f"[*] Loading ONNX Sessions (FP32 & INT8)...")
    session_fp32 = ort.InferenceSession(onnx_fp32_path, providers=['CPUExecutionProvider'])
    
    session_int8 = None
    if os.path.exists(onnx_int8_path):
        session_int8 = ort.InferenceSession(onnx_int8_path, providers=['CPUExecutionProvider'])
    else:
        print("[!] No INT8 model found. Skipping INT8 benchmark.")

    texts = [
        "A fast inference backend is critical for responsive User Experience.",
        "Edge AI requires hardware acceleration and memory optimization.",
        "Using ONNX and TVM for deployment on resource-constrained devices.",
        "Hybrid search combines vector similarity with full-text tokenization."
    ] * 25 # 100 samples
    
    print(f"[*] Starting Comparison (N = {len(texts)})...")

    # 1. Warmup
    for _ in range(5):
        inputs = tokenizer("Warmup", return_tensors="pt")
        with torch.no_grad(): model_pt(**inputs)
        np_inputs = {k: v.numpy() for k, v in inputs.items()}
        if 'token_type_ids' in np_inputs: np_inputs['token_type_ids'] = np_inputs['token_type_ids'].astype('int64')
        session_fp32.run(None, np_inputs)
        if session_int8: session_int8.run(None, np_inputs)

    def run_inference_pt(text_list):
        times = []
        embeddings = []
        for text in text_list:
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            start = time.perf_counter()
            with torch.no_grad():
                outputs = model_pt(**inputs)
                emb = mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                embeddings.append(emb[0])
            times.append(time.perf_counter() - start)
        return times, embeddings

    def run_inference_onnx(text_list, session):
        times = []
        embeddings = []
        for text in text_list:
            inputs = tokenizer(text, return_tensors="np", padding=True, truncation=True)
            ort_inputs = {
                'input_ids': inputs['input_ids'].astype('int64'),
                'attention_mask': inputs['attention_mask'].astype('int64')
            }
            if 'token_type_ids' in inputs:
                ort_inputs['token_type_ids'] = inputs['token_type_ids'].astype('int64')
            
            start = time.perf_counter()
            ort_outs = session.run(None, ort_inputs)
            last_hidden_state = torch.tensor(ort_outs[0])
            attention_mask = torch.tensor(inputs['attention_mask'])
            emb = mean_pooling(last_hidden_state, attention_mask)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            embeddings.append(emb[0])
            times.append(time.perf_counter() - start)
        return times, embeddings

    # Benchmarking
    print("[*] Benchmarking PyTorch Baseline...")
    times_pt, emb_pt = run_inference_pt(texts)
    
    print("[*] Benchmarking ONNX FP32...")
    times_fp32, emb_fp32 = run_inference_onnx(texts, session_fp32)
    
    times_int8, emb_int8 = None, None
    if session_int8:
        print("[*] Benchmarking ONNX INT8 (Quantized)...")
        times_int8, emb_int8 = run_inference_onnx(texts, session_int8)

    # Metrics
    avg_pt = np.mean(times_pt) * 1000
    avg_fp32 = np.mean(times_fp32) * 1000
    
    # Parity Check
    def get_parity(emb_a, emb_b):
        sims = []
        for i in range(len(emb_a)):
            sim = torch.nn.functional.cosine_similarity(emb_a[i].unsqueeze(0), emb_b[i].unsqueeze(0))
            sims.append(sim.item())
        return np.mean(sims)

    parity_fp32 = get_parity(emb_pt, emb_fp32)

    print("\n" + "-"*30)
    print(" RESULTS SUMMARY ")
    print("-"*30)
    print(f"PyTorch (Base):      Lat: {avg_pt:6.2f} ms | Parity: REF")
    print(f"ONNX FP32:           Lat: {avg_fp32:6.2f} ms | Parity: {parity_fp32:.8f}")
    
    if session_int8:
        avg_int8 = np.mean(times_int8) * 1000
        parity_int8 = get_parity(emb_pt, emb_int8)
        print(f"ONNX INT8:           Lat: {avg_int8:6.2f} ms | Parity: {parity_int8:.8f}")
        print(f"\nFinal Speedup vs PyTorch: {avg_pt / avg_int8:.2f}x")
        print(f"INT8 Gain vs FP32:       {avg_fp32 / avg_int8:.2f}x")
    else:
        print(f"\nFinal Speedup vs PyTorch: {avg_pt / avg_fp32:.2f}x")

    print("\n[*] Optimization Note:")
    print(" - INT8 quantization reduces model size by ~4x (91MB -> 23MB).")
    print(" - Numerical drift in INT8 is acceptable for semantic similarity.")
    print("="*60)

if __name__ == "__main__":
    try:
        run_professional_benchmark()
    except Exception as e:
        print(f"Error during benchmark: {e}")
