import os
from onnxruntime.quantization import quantize_dynamic, QuantType

def run_quantization():
    """
    Antmicro-grade ML Optimization: 
    Converts FP32 ONNX model to INT8 Dynamic Quantization.
    Significantly reduces model size and improves CPU inference speed.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    model_dir = os.path.join(base_dir, "models", "v1-onnx-minilm")
    
    input_model_path = os.path.join(model_dir, "model.onnx")
    output_model_path = os.path.join(model_dir, "model_int8.onnx")

    if not os.path.exists(input_model_path):
        print(f"[ERROR] Source model not found: {input_model_path}")
        return

    print("="*60)
    print(" MODEL QUANTIZATION (FP32 -> INT8) ")
    print("="*60)
    
    print(f"[*] Starting Dynamic Quantization...")
    print(f"    Source: {input_model_path}")
    print(f"    Target: {output_model_path}")

    # Dynamic quantization is ideal for BERT-based models on CPU
    quantize_dynamic(
        model_input=input_model_path,
        model_output=output_model_path,
        weight_type=QuantType.QUInt8
    )

    # Size comparison
    size_orig = os.path.getsize(input_model_path) / (1024 * 1024)
    size_quant = os.path.getsize(output_model_path) / (1024 * 1024)

    print("\n" + "-"*30)
    print(" RESULTS ")
    print("-"*30)
    print(f"Original Size:    {size_orig:.2f} MB")
    print(f"Quantized Size:   {size_quant:.2f} MB")
    print(f"Reduction:        {((size_orig - size_quant) / size_orig) * 100:.1f}% smaller")
    
    print("\n[STATUS] INT8 Model generated successfully.")
    print("[*] Next Step: Run 'python scripts/benchmark.py' to verify speedup vs accuracy drift.")
    print("="*60)

if __name__ == "__main__":
    try:
        run_quantization()
    except Exception as e:
        print(f"Error during quantization: {e}")
        print("\nNote: You may need to install 'onnxruntime' if not present.")
