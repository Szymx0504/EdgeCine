# Inference Latency & Accuracy Report (WSL/Docker Edition)

This report documents the performance gains achieved by moving from standard PyTorch inference to an optimized **ONNX Runtime** backend within a containerized Linux environment (WSL2).

## 1. Environment Details
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Target Backend:** ONNX Runtime v1.17+ (CPUExecutionProvider)
- **Host System:** Linux / WSL2 (Docker Container)
- **Metrics Tool:** `/scripts/benchmark.py`

## 2. Real-World Benchmarks (WSL)
*Measured over 100 samples in the Dockerized environment.*

| Backend | Mean Latency | Speedup | Parity (Accuracy) | Size On Disk |
|---------|--------------|---------|-------------------|--------------|
| **PyTorch (Baseline)** | ~21.25 ms | 1.0x | 1.0 (REF) | ~91 MB |
| **ONNX FP32** | **~6.60 ms** | **3.22x** | **1.00000012** | ~91 MB |
| **ONNX INT8 (Quantized)**| ~7.83 ms | 2.71x | 0.98264441 | **~23 MB** |

## 3. The "Quantization Overhead" Insight
During our Linux audit, we confirmed that **ONNX FP32** is the fastest variant on this hardware. While **INT8 Quantization** is 2.7x faster than PyTorch, it is slightly slower than FP32 (0.84x performance relative to FP32).

### Technical Analysis for Antmicro Interview:
- **Why FP32 wins here:** Modern CPUs are highly optimized for floating-point math. Unless a CPU has specialized instructions like **AVX-512 VNNI**, the "dynamic quantization" overhead (converting numbers between formats on-the-fly) can make INT8 slightly slower than native FP32.
- **Why we still include INT8:** 
  - **Memory Efficiency:** INT8 reduces the model size by **75%** (from 91MB down to 23MB). 
  - **Edge Portability:** On low-power ARM architecture (like a Raspberry Pi or Jetson Nano), where memory is the bottleneck, the 23MB INT8 model is often the only viable choice for deployment.
- **Conclusion:** We keep both variants available via environment variables to allow for "deployment-time" trade-offs between speed and memory footprint.

## 4. Optimization Path
1. **Static Quantization:** Future versions can use calibration datasets to move from dynamic to static quantization, removing the runtime overhead.
2. **TVM Compilation:** For truly embedded targets, compiling these ONNX graphs into C++ kernels would further reduce the binary size and latency.
