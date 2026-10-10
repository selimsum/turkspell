# train.py
import argparse
import os

def train(model_id="Qwen/Qwen2.5-Coder-7B-Instruct", dataset_path="train_dataset.jsonl", output_dir="./output_dir", epochs=3, batch_size=2, lr=2e-4):
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from trl import SFTTrainer
    except ImportError as e:
        print(f"Error: Missing machine learning dependencies: {e}")
        print("Install with: pip install torch transformers datasets peft trl accelerate bitsandbytes")
        return

    print("Starting SFT Trainer setup...")
    print(f"Model: {model_id} | Dataset: {dataset_path} | Output Dir: {output_dir} | Epochs: {epochs}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load dataset
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found. Please run generate_training_data.py first.")
        return
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    
    # Format dataset to have a single "text" field to be compatible across TRL versions
    def format_prompts(batch):
        formatted = []
        for inst, inp, out in zip(batch['instruction'], batch['input'], batch['output']):
            text = f"Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.\n\n### Instruction:\n{inst}\n\n### Input:\n{inp}\n\n### Response:\n{out}"
            formatted.append(text)
        return {"text": formatted}
    
    dataset = dataset.map(format_prompts, batched=True)
    
    # Check GPU VRAM
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"Detected VRAM: {vram:.2f} GB")
    else:
        vram = 0
        print("No GPU detected! Running on CPU (slow).")
    
    # Decide quantization based on VRAM
    if vram < 20:
        print("Using 4-bit QLoRA (T4 GPU settings)")
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto"
        )
    else:
        print("Using standard bfloat16 LoRA (L4 GPU settings)")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    
    # Check TRL version configuration and inspect signatures dynamically
    import inspect
    import dataclasses
    
    try:
        from trl import SFTConfig
        HAS_SFT_CONFIG = True
        # Get fields of the SFTConfig dataclass
        sft_config_fields = {f.name for f in dataclasses.fields(SFTConfig)}
    except (ImportError, TypeError):
        HAS_SFT_CONFIG = False
        sft_config_fields = set()
        
    # Get parameters accepted by SFTTrainer.__init__
    sft_trainer_params = set(inspect.signature(SFTTrainer.__init__).parameters.keys())
    
    tokenizer_key = "processing_class" if "processing_class" in sft_trainer_params else "tokenizer"
    print(f"Dynamic Inspection:")
    print(f"  HAS_SFT_CONFIG: {HAS_SFT_CONFIG}")
    print(f"  SFTConfig fields: {sorted(list(sft_config_fields)) if HAS_SFT_CONFIG else 'None'}")
    print(f"  SFTTrainer params: {sorted(list(sft_trainer_params))}")
    print(f"  Selected tokenizer keyword: '{tokenizer_key}'")
    
    if HAS_SFT_CONFIG:
        print("Using modern SFTConfig for SFTTrainer")
        # Build valid config args
        config_kwargs = {
            "output_dir": output_dir,
            "per_device_train_batch_size": batch_size,
            "gradient_accumulation_steps": 4,
            "learning_rate": lr,
            "logging_steps": 10,
            "num_train_epochs": epochs,
            "bf16": True if vram >= 20 else False,
            "fp16": False if vram >= 20 else True,
            "save_strategy": "epoch",
            "report_to": "none"
        }
        
        if "max_seq_length" in sft_config_fields:
            config_kwargs["max_seq_length"] = 512
        if "dataset_text_field" in sft_config_fields:
            config_kwargs["dataset_text_field"] = "text"
            
        training_args = SFTConfig(**config_kwargs)
        
        # Build valid trainer args
        trainer_kwargs = {
            "model": model,
            "train_dataset": dataset,
            "args": training_args,
            tokenizer_key: tokenizer
        }
        
        # Only pass max_seq_length to Trainer if it's accepted there and wasn't set in config
        if "max_seq_length" in sft_trainer_params and "max_seq_length" not in config_kwargs:
            trainer_kwargs["max_seq_length"] = 512
        if "dataset_text_field" in sft_trainer_params and "dataset_text_field" not in config_kwargs:
            trainer_kwargs["dataset_text_field"] = "text"
            
        trainer = SFTTrainer(**trainer_kwargs)
    else:
        print("Using legacy SFTTrainer direct configuration")
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=lr,
            logging_steps=10,
            num_train_epochs=epochs,
            bf16=True if vram >= 20 else False,
            fp16=False if vram >= 20 else True,
            save_strategy="epoch",
            report_to="none"
        )
        
        trainer_kwargs = {
            "model": model,
            "train_dataset": dataset,
            "args": training_args,
            tokenizer_key: tokenizer
        }
        
        if "max_seq_length" in sft_trainer_params:
            trainer_kwargs["max_seq_length"] = 512
        if "dataset_text_field" in sft_trainer_params:
            trainer_kwargs["dataset_text_field"] = "text"
            
        trainer = SFTTrainer(**trainer_kwargs)
    
    print("Starting training...")
    trainer.train()
    print(f"Training finished! Saved adapters to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Qwen on Turkspell grammar rules using QLoRA")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen2.5-Coder-7B-Instruct")
    parser.add_argument("--dataset", type=str, default="train_dataset.jsonl")
    parser.add_argument("--output-dir", type=str, default="./output_dir")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()

    train(
        model_id=args.model_id,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
