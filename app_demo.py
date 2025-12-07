"""
Tanit Fertility Assistant - DEMO VERSION
No model downloads required - uses mock responses for demonstration
Run this for instant demo, then switch to full app.py for production
"""

import gradio as gr
from datetime import datetime
import time
import json
import os

# Mock handlers for demo
class MockVLM:
    def analyze_image(self, image_path, prompt):
        time.sleep(0.8)  # Simulate processing
        return """
Extracted from hormone panel:
- AMH: 1.1 ng/mL (slightly below average for age 34)
- FSH: 8.2 mIU/mL (day 3) - normal range
- LH: 5.1 mIU/mL - normal
- Estradiol: 45 pg/mL - normal follicular phase
- TSH: 2.1 mIU/L - optimal for fertility
Test date: 2024-12-01
"""

class MockLLM:
    def generate(self, system_prompt, user_prompt, **kwargs):
        time.sleep(1.2)  # Simulate generation
        
        # Simple response based on keywords
        if "amh" in user_prompt.lower() and "1.1" in user_prompt:
            return """Thank you for sharing your information. Let me help you understand what this means:

**Understanding Your AMH Level:**
At 34 years old with an AMH of 1.1 ng/mL, your ovarian reserve is slightly below the average range (typically 1.5-4.0 ng/mL for your age), but this is still within a range where natural conception is possible for many women.

**PCOS Context:**
Having PCOS actually changes how we interpret AMH. Women with PCOS typically have higher AMH levels due to the accumulation of small follicles. Your level of 1.1 might actually represent better ovarian function than the same number would in someone without PCOS.

**What This Means:**
- Your ovarian reserve shows moderate activity
- With PCOS, ovulation regularity is often the key factor, not reserve
- Many women with similar profiles conceive successfully, especially with cycle monitoring
- Time is on your side at 34 - you have options to explore

**Recommended Next Steps:**
1. Track your ovulation patterns (BBT, LH tests, or ultrasound monitoring)
2. Discuss cycle regulation options with your RE if cycles are irregular
3. Consider a full fertility workup including HSG and partner analysis
4. Lifestyle optimization: PCOS responds well to nutrition and exercise

**Evidence Base:** This interpretation aligns with ASRM 2023 guidelines on ovarian reserve testing and ESHRE PCOS management recommendations."""
        
        return "Based on the medical knowledge available, I can help explain fertility concepts, hormone levels, and treatment options. Please share specific questions or upload test results for detailed interpretation."

class MockSTT:
    def transcribe(self, audio_path):
        time.sleep(0.5)
        return "I'm 34 years old, my AMH is 1.1 ng/mL and I have PCOS. Should I be worried?"

class MockGraphRAG:
    def __init__(self):
        kb_file = "rag/graphrag_index/knowledge_base.json"
        if os.path.exists(kb_file):
            with open(kb_file, 'r') as f:
                self.kb = json.load(f)
        else:
            self.kb = {}
    
    def query(self, query, **kwargs):
        time.sleep(0.5)
        
        formatted = """## Relevant Medical Knowledge from GraphRAG:

### AMH Levels
Anti-Müllerian Hormone (AMH) indicates ovarian reserve

**Age-Specific Reference Ranges:**
- Age 31-35: 1.5-5.5 ng/mL
- Age 36-40: 1.0-3.5 ng/mL

**Clinical Interpretation:**
- Normal: 1.5-4.0 indicates adequate reserve for age
- Low: <1.0 may indicate diminished ovarian reserve

### Medical Sources:
- ASRM 2023 Guidelines
- Fertility & Sterility Journal
"""
        
        return {
            "nodes": [],
            "relationships": [],
            "formatted_context": formatted
        }

# Initialize mock components
print("🚀 Loading Tanit Fertility Assistant (Demo Mode)...")
vlm = MockVLM()
llm = MockLLM()
stt = MockSTT()
graphrag = MockGraphRAG()

conversation_history = []

def process_multimodal_input(text_input, audio_input, image_input, pdf_input):
    """Mock processing pipeline"""
    start_time = time.time()
    
    try:
        # Step 1: Mock STT
        if audio_input is not None:
            text_input = stt.transcribe(audio_input)
            print(f"📝 Transcribed: {text_input}")
        
        # Step 2: Mock VLM
        visual_context = ""
        if image_input is not None:
            visual_context = vlm.analyze_image(image_input, "Extract medical data")
            print(f"👁️ VLM extracted data")
        
        # Step 3: Mock GraphRAG
        query = text_input + " " + visual_context if visual_context else text_input
        rag_context = graphrag.query(query)
        
        # Step 4: Mock LLM
        system_prompt = "You are Tanit, a warm fertility AI assistant."
        user_prompt = f"""Patient Query: {text_input}

{f"Visual Analysis: {visual_context}" if visual_context else ""}

Medical Knowledge:
{rag_context['formatted_context']}

Provide warm, evidence-based response."""
        
        response = llm.generate(system_prompt, user_prompt)
        
        # Add disclaimer
        response += "\n\n---\n💡 **Important Note:** This information is for educational purposes. Your individual situation requires personalized evaluation by a reproductive endocrinologist."
        
        # Add latency
        total_time = time.time() - start_time
        response += f"\n\n🔬 **Demo Processing Time:** {total_time:.2f}s (VLM: 0.8s | RAG: 0.5s | LLM: 1.2s)"
        response += "\n\n*🎭 Running in DEMO MODE - using mock models. Run full app.py for real AI models.*"
        
        return response
    
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nPlease ensure you've run: python rag/graphrag_builder.py"

# Gradio Interface (same as full version)
with gr.Blocks(title="Tanit Fertility Companion") as demo:
    gr.Markdown("""
    # 🌸 Tanit Fertility Companion (Demo Mode)
    ### Multimodal AI Assistant - Quick Demo Version
    *Experience the interface without downloading 10GB of models*
    """)
    
    gr.Markdown("""
    ### ⚡ Demo Mode Active
    - Using mock responses to show functionality
    - For real AI: run `python app.py` (requires model downloads)
    - GraphRAG knowledge base: ✅ Active
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="💬 Your Question",
                placeholder="Ask about hormone levels, cycle tracking, treatments...",
                lines=3
            )
            
            with gr.Row():
                audio_input = gr.Audio(
                    label="🎤 Voice Input (optional)",
                    sources=["microphone"],
                    type="filepath"
                )
                
                image_input = gr.Image(
                    label="📸 Upload Lab Results (optional)",
                    type="filepath"
                )
            
            pdf_input = gr.File(
                label="📄 Upload Medical PDF (optional)",
                file_types=[".pdf"]
            )
            
            submit_btn = gr.Button("Send Message", variant="primary", size="lg")
        
        with gr.Column(scale=2):
            gr.Markdown("""
            ### 💡 Try These:
            **Text:** "I'm 34, my AMH is 1.1, should I be worried?"
            
            **Image:** Upload any test result image (demo will show mock extraction)
            
            **Voice:** Record the same question
            """)
    
    output = gr.Markdown(label="Tanit's Response")
    
    gr.Examples(
        examples=[
            ["What does an AMH of 1.1 ng/mL mean for a 34 year old with PCOS?", None, None, None],
            ["I have irregular cycles with PCOS. How do I track ovulation?", None, None, None],
            ["Explain FSH testing and what the results mean", None, None, None],
        ],
        inputs=[text_input, audio_input, image_input, pdf_input]
    )
    
    gr.Markdown("""
    ---
    ⚠️ **Medical Disclaimer:** This AI provides educational information based on clinical guidelines. 
    It cannot diagnose conditions or replace consultation with your reproductive endocrinologist.
    """)
    
    submit_btn.click(
        fn=process_multimodal_input,
        inputs=[text_input, audio_input, image_input, pdf_input],
        outputs=output
    )

if __name__ == "__main__":
    print("✅ Demo ready!")
    demo.launch(share=True, server_name="0.0.0.0")