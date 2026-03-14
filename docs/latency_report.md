# Inference Latency & Performance Analysis

This report evaluates the performance gains and trade-offs of using an optimized **ONNX Runtime** backend for semantic vectorization compared to a standard PyTorch baseline.

## 1. Environment & Methodology
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Execution Provider:** ONNX Runtime v1.17+ (`CPUExecutionProvider`)
- **Host Architecture:** Linux / x86_64 (Containerized environment)
- **Metric Collection:** Mean latency measured over 100 sequential query-to-vector operations.

## 2. Benchmarks

| Backend | Mean Latency | Speedup | Numerical Parity | Footprint |
|---------|--------------|---------|-------------------|-----------|
| **PyTorch (Baseline)** | 21.25 ms | 1.0x | 1.000 (REF) | ~91 MB |
| **ONNX FP32** | **6.60 ms** | **3.22x** | **1.000** | ~91 MB |
| **ONNX INT8 (Quantized)**| 7.83 ms | 2.71x | 0.983 | **23 MB** |

## 3. Analysis of Results

### FP32 vs. INT8 Performance
Observations indicate that **ONNX FP32** provides the highest throughput on the target hardware. While INT8 quantization is significantly faster than the PyTorch baseline, it exhibits a slight latency increase compared to FP32.

**Hardware Reasoning:**
- **Floating-Point Optimization:** Modern CPUs are highly optimized for FP32 arithmetic. Without hardware-level acceleration for 8-bit integer operations (e.g., AVX-512 VNNI), the overhead of dynamic quantization—specifically calculating scaling factors for activations on-the-fly—can exceed the raw compute savings of integer math.
- **Accuracy Trade-off:** The INT8 model achieves a 0.983 numerical parity (1.7% drift), which is acceptable for semantic search where cosine similarity ranking is robust to minor precision loss.

### Edge Readiness & Portability
Despite the slight latency overhead on x86, the **INT8 variant** remains a core deployment option for the following reasons:
1. **Memory Footprint:** A 75% reduction in binary size (from 91MB to 23MB) is critical for memory-constrained edge nodes.
2. **ARM Performance:** On low-power ARM architectures (e.g., Raspberry Pi 4), memory bandwidth often becomes the bottleneck, making the smaller INT8 weights faster than FP32.

## 4. Future Optimizations
- **Static Quantization:** Implementing static quantization with a calibration dataset (HuggingFace Optimum) to pre-compute scaling factors, removing the dynamic quantization runtime overhead.
- **TVM / Graph Compilation:** Compiling the ONNX graph into specialized kernels to further reduce latency on specific embedded targets.
