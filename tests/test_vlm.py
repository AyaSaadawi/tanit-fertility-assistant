"""
Test suite for VLM medical image analysis accuracy
"""

import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

class VLMTester:
    def __init__(self):
        print("Loading VLM for testing...")
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-2B-Instruct",
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(
            "Qwen/Qwen2-VL-2B-Instruct",
            trust_remote_code=True
        )
    
    def create_synthetic_hormone_panel(self, values):
        """Create synthetic hormone panel for testing"""
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fall back to default if unavailable
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Title
        draw.text((50, 30), "Hormone Panel - Lab Results", fill='black', font=font)
        draw.text((50, 60), "Patient: Test Case", fill='black')
        
        # Draw table
        y_pos = 120
        for test_name, value, unit, ref_range in values:
            draw.text((50, y_pos), test_name, fill='black', font=font)
            draw.text((300, y_pos), f"{value}", fill='black', font=font)
            draw.text((450, y_pos), unit, fill='black', font=font)
            draw.text((550, y_pos), f"Ref: {ref_range}", fill='black')
            y_pos += 50
        
        return img
    
    def analyze_image(self, image, query="Extract all hormone values"):
        """Analyze medical image"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": query}
                ]
            }
        ]
        
        text = self.processor.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        inputs = self.processor(
            text=[text],
            images=[image],
            videos=None,
            padding=True,
            return_tensors="pt"
        ).to("cuda")
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,
                do_sample=False
            )
        
        analysis = self.processor.batch_decode(
            outputs[:, inputs['input_ids'].shape[1]:],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        return analysis
    
    def extract_value(self, text, hormone_name):
        """Extract specific hormone value from analysis"""
        patterns = [
            rf"{hormone_name}[:\s]+(\d+\.?\d*)",
            rf"{hormone_name}.*?(\d+\.?\d*)\s*ng/mL",
            rf"{hormone_name}.*?(\d+\.?\d*)\s*mIU/mL",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def run_accuracy_test(self):
        """Run comprehensive accuracy test"""
        print("\n" + "="*60)
        print("VLM MEDICAL ACCURACY TEST")
        print("="*60)
        
        # Test cases: (hormone, value, unit, reference_range)
        test_cases = [
            [
                ("AMH", 1.5, "ng/mL", "1.5-4.0"),
                ("FSH", 8.2, "mIU/mL", "3.0-10.0"),
                ("LH", 5.1, "mIU/mL", "2.0-10.0"),
                ("Estradiol", 45, "pg/mL", "25-75"),
            ],
            [
                ("AMH", 0.8, "ng/mL", "1.5-4.0"),
                ("FSH", 15.3, "mIU/mL", "3.0-10.0"),
                ("LH", 6.7, "mIU/mL", "2.0-10.0"),
                ("TSH", 2.1, "mIU/L", "0.5-4.5"),
            ],
            [
                ("AMH", 3.2, "ng/mL", "1.5-4.0"),
                ("Progesterone", 18.5, "ng/mL", ">10"),
                ("Estradiol", 220, "pg/mL", "150-400"),
            ]
        ]
        
        total_tests = 0
        correct_extractions = 0
        errors = []
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i} ---")
            
            # Create synthetic image
            img = self.create_synthetic_hormone_panel(case)
            
            # Analyze
            analysis = self.analyze_image(img)
            print(f"Analysis: {analysis[:200]}...")
            
            # Check each hormone
            for hormone, expected_value, unit, ref in case:
                total_tests += 1
                extracted = self.extract_value(analysis, hormone)
                
                if extracted is not None:
                    error_margin = abs(extracted - expected_value) / expected_value
                    if error_margin < 0.05:  # 5% tolerance
                        correct_extractions += 1
                        print(f"✓ {hormone}: {extracted} (expected {expected_value})")
                    else:
                        print(f"✗ {hormone}: {extracted} (expected {expected_value})")
                        errors.append((hormone, expected_value, extracted))
                else:
                    print(f"✗ {hormone}: NOT FOUND (expected {expected_value})")
                    errors.append((hormone, expected_value, None))
        
        # Results
        accuracy = (correct_extractions / total_tests) * 100
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        print(f"Total tests: {total_tests}")
        print(f"Correct extractions: {correct_extractions}")
        print(f"Accuracy: {accuracy:.1f}%")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for hormone, expected, extracted in errors:
                print(f"  - {hormone}: expected {expected}, got {extracted}")
        
        return accuracy

def main():
    tester = VLMTester()
    accuracy = tester.run_accuracy_test()
    
    if accuracy >= 95:
        print("\n🎉 VLM PASSED: Medical accuracy >= 95%")
    else:
        print(f"\n⚠️ VLM NEEDS IMPROVEMENT: Accuracy {accuracy:.1f}% < 95%")

if __name__ == "__main__":
    main()