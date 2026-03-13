import os
import torch
from transformers import AutoTokenizer, AutoModel
import onnx
import onnxruntime as ort

def export_to_onnx():
    """
    Utility script to export and optimize the MiniLM model to ONNX format.
    Used for local inference and hardware acceleration.
    """
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    base_dir = os.path.dirname(os.path.dirname(__file__))
    out_dir = os.path.join(base_dir, "models", "v1-onnx-minilm")
    os.makedirs(out_dir, exist_ok=True)
    
    onnx_path = os.path.join(out_dir, "model.onnx")
    
    print(f"[*] Exporting {model_name} to ONNX...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    dummy_input = tokenizer("This is a test sentence for ONNX export.", return_tensors="pt")
    
    torch.onnx.export(
        model,
        (dummy_input['input_ids'], dummy_input['attention_mask'], dummy_input['token_type_ids']),
        onnx_path,
        input_names=['input_ids', 'attention_mask', 'token_type_ids'],
        output_names=['last_hidden_state'],
        dynamic_axes={
            'input_ids': {0: 'batch_size', 1: 'sequence_length'},
            'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
            'token_type_ids': {0: 'batch_size', 1: 'sequence_length'},
            'last_hidden_state': {0: 'batch_size', 1: 'sequence_length'}
        },
        opset_version=14,
        do_constant_folding=True
    )
    
    print(f"[V] Export complete: {onnx_path}")
    print("[*] To further optimize for Antmicro's stack, consider INT8 quantization or TVM compilation.")

if __name__ == "__main__":
    export_to_onnx()
