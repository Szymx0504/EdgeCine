# Inference Latency & Accuracy Report

This report documents the performance gains achieved by moving from standard PyTorch inference to an optimized **ONNX Runtime** backend. These optimizations are critical for deploying AI models to Edge environments with limited resources.

## 1. Environment Details
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Target Backend:** ONNX Runtime v1.17+ (CPUExecutionProvider)
- **Host System:** Windows 10/11 (Local Backend)

## 2. Latency Comparison
Metrics were generated using `/scripts/benchmark.py` over 100 diverse text samples.

| Backend | Mean Latency | Parity (Accuracy) | Size On Disk |
|---------|--------------|-------------------|--------------|
| **PyTorch (Standard)** | ~21.40 ms | 1.0 (REF) | ~91 MB |
| **ONNX FP32** | **~6.40 ms** | **1.00000006** | ~91 MB |
| **ONNX INT8 (Quantized)**| ~11.11 ms | 0.98264442 | **~23 MB** |

## 3. The "INT8 Paradox" & Hardware Trade-offs
During testing, we observed that while **INT8 Quantization** reduced the model size by **3.8x**, it was actually slower than FP32 on this specific CPU.

**Technical Analysis for Interview:**
- **Why it's slower:** Dynamic quantization introduces overhead for converting weights on-the-fly. If the host CPU lacks specialized INT8 instructions (like AVX-512 VNNI), the "cost" of quantization outweighs the speed of integer math.
- **Why we still keep it:** For **Edge Devices** (like an ARM-based Jetson or Raspberry Pi), memory is more scarce than compute. A 23MB model is significantly better for these environments than a 91MB model, even if latency is slightly higher.
- **Accuracy (Parity):** The drop to `0.98` similarity is negligible for movie recommendation but is a key metric to monitor in production.

## 4. Optimization Roadmap
Based on current benchmarks:
1. **Static Quantization:** Calibration with a dataset to remove the dynamic quantization overhead.
2. **TVM Compilation:** Compiling specifically for INT8 using TVM to bypass generic runtime kernels.

## 4. Optimization Roadmap
Based on current benchmarks, the following "System-Level" optimizations are planned:
1. **INT8 Quantization:** Moving from FP32 to INT8 weights to reduce memory footprint by 75% and further boost CPU throughput.
2. **TVM Compilation:** Utilizing the Apache TVM stack to compile specific model ops into optimized C++ kernels for deployment on specialized ARM or RISC-V hardware.
