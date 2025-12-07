from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMHandler:
    def __init__(self, model_name="Qwen/Qwen2.5-4B-Instruct", quantization="4bit"):
        """
        Qwen2.5-4B-Instruct: Best open-source reasoning model for medical dialogue
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Loading LLM: {model_name}...")
        
        if quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto"
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✅ LLM loaded successfully")
    
    def generate(self, system_prompt, user_prompt, conversation_history=[], temperature=0.7, max_tokens=800):
        """
        Generate medically-grounded, empathetic response
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        messages.extend(conversation_history)
        
        # Add current query
        messages.append({"role": "user", "content": user_prompt})
        
        # Format with chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        
        # Generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9
            )
        
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response