from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch
from PIL import Image
import fitz  # PyMuPDF for PDF processing

class VLMHandler:
    def __init__(self, model_name="Qwen/Qwen2-VL-4B-Instruct", quantization="4bit"):
        """
        Qwen2-VL-4B: SOTA open-source VLM for medical document understanding
        - Perfect for hormone panels, ultrasounds, lab reports
        - 4-bit quantization for Kaggle GPU compatibility
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Loading VLM: {model_name} with {quantization} quantization...")
        
        if quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto"
            )
        else:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        
        self.processor = AutoProcessor.from_pretrained(model_name)
        print("✅ VLM loaded successfully")
    
    def analyze_image(self, image_path, prompt="Describe this medical image in detail."):
        """
        Extract information from medical images:
        - Hormone lab panels
        - Ultrasound scans
        - Cycle tracking charts
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # Process inputs
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
        
        return output_text[0]
    
    def analyze_pdf(self, pdf_path):
        """
        Extract images and tables from PDF medical reports
        """
        doc = fitz.open(pdf_path)
        full_analysis = ""
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract images from page
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n < 5:  # GRAY or RGB
                    img_path = f"/tmp/page{page_num}_img{img_index}.png"
                    pix.save(img_path)
                    
                    # Analyze extracted image
                    analysis = self.analyze_image(
                        img_path,
                        prompt="Extract all visible medical data: hormone values, dates, reference ranges, measurements."
                    )
                    full_analysis += f"\n[Page {page_num+1}, Image {img_index+1}]: {analysis}"
        
        doc.close()
        return full_analysis