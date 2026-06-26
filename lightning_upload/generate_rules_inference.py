import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json

base_model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
peft_model_id = "./output_dir" # Path to your last checkpoint folder

# Load base model + adapters
print("Loading model and adapters...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id)
model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.bfloat16,
    device_map="cuda" # Load directly onto the GPU to avoid CPU/disk offloading bugs in PEFT
)
model = PeftModel.from_pretrained(model, peft_model_id)

# Example: Ask the model to suggest rules for a missing aspect
prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Determine the missing suffix templates and propose code edits for generate_grammar_rules.py to accept unrecognized forms of root 'yap'.

### Input:
Root stem: yap
Unrecognized inflections found in corpus: yapıverdi, yapıvermiş, yapıverir

### Response:
"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=256)
    
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
