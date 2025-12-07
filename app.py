"""
Tanit Fertility Assistant - PRODUCTION VERSION
Uses real AI models: Qwen2-VL-4B + Qwen2.5-4B + faster-whisper
First run: Downloads ~10GB models (10-15 minutes)
Subsequent runs: Launches in 30 seconds
"""

import gradio as gr
from datetime import datetime
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.vlm_handler import VLMHandler
from models.llm_handler import LLMHandler
from voice.stt import STTHandler
from rag.graphrag_query import GraphRAGEngine
from utils.safety import SafetyGuardrails
from utils.latency_tracker import LatencyTracker

# Initialize components
print("🚀 Initializing Tanit Fertility Assistant (Production Mode)...")
print("⏳ First run: Downloading models (~10GB, 10-15 minutes)")
print("   Subsequent runs: 30 seconds\n")

try:
    print("1/5 Loading VLM (Qwen2-VL-4B-Instruct)...")
    vlm = VLMHandler(model_name="Qwen/Qwen2-VL-2B-Instruct", quantization="4bit")  # Using 2B for faster demo
    
    print("2/5 Loading LLM (Qwen2.5-4B-Instruct)...")
    llm = LLMHandler(model_name="Qwen/Qwen2.5-3B-Instruct", quantization="4bit")  # Using 3B for faster demo
    
    print("3/5 Loading STT (faster-whisper medium)...")
    stt = STTHandler(model_size="base")  # Using base for faster demo
    
    print("4/5 Loading GraphRAG knowledge base...")
    graphrag = GraphRAGEngine(index_path="rag/graphrag_index")
    
    print("5/5 Initializing safety guardrails...")
    safety = SafetyGuardrails()
    
    print("\n✅ All models loaded successfully!\n")
    
except Exception as e:
    print(f"\n❌ Error loading models: {str(e)}")
    print("\n💡 For quick demo without downloads, run: python app_demo.py")
    sys.exit(1)

# Global conversation history
conversation_history = []

def process_multimodal_input(text_input, audio_input, image_input, pdf_input):
    """
    Main processing pipeline with real AI models:
    1. STT if audio provided
    2. VLM if image/PDF provided
    3. GraphRAG retrieval for grounding
    4. LLM synthesis with safety checks
    """
    latency = LatencyTracker()
    latency.start()
    
    try:
        # Step 1: Transcribe audio if provided
        if audio_input is not None:
            latency.checkpoint("stt_start")
            text_input = stt.transcribe(audio_input)
            latency.checkpoint("stt_end")
            print(f"📝 Transcribed: {text_input[:100]}...")
        
        if not text_input or text_input.strip() == "":
            return "⚠️ Please provide a question (text or voice) to get started."
        
        # Step 2: Process visual inputs (images/PDFs)
        visual_context = ""
        if image_input is not None:
            latency.checkpoint("vlm_start")
            visual_context = vlm.analyze_image(
                image_input,
                prompt="You are analyzing a medical document. Extract all visible information including: hormone values with units, reference ranges, dates, patient age, and any medical measurements. Be precise and complete."
            )
            latency.checkpoint("vlm_end")
            print(f"👁️ VLM extracted: {visual_context[:200]}...")
        
        if pdf_input is not None:
            latency.checkpoint("pdf_start")
            visual_context += "\n\n" + vlm.analyze_pdf(pdf_input)
            latency.checkpoint("pdf_end")
        
        # Step 3: GraphRAG retrieval for medical grounding
        latency.checkpoint("rag_start")
        query = text_input + " " + visual_context if visual_context else text_input
        rag_context = graphrag.query(query, top_k=5, include_subgraph=True)
        latency.checkpoint("rag_end")
        print(f"📚 Retrieved medical knowledge from GraphRAG")
        
        # Step 4: Build comprehensive prompt
        system_prompt = safety.get_medical_system_prompt()
        
        user_prompt = f"""Patient Query: {text_input}

{f"Visual Analysis (VLM extracted data): {visual_context}" if visual_context else ""}

Relevant Medical Knowledge (GraphRAG):
{rag_context['formatted_context']}

Instructions:
- Provide a warm, empathetic, evidence-based response
- Explain medical terms in plain language
- Reference the knowledge sources you're drawing from
- Give actionable next steps when appropriate
- Include appropriate medical disclaimers
- Be encouraging and supportive"""

        # Step 5: Generate response with LLM
        latency.checkpoint("llm_start")
        response = llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=conversation_history[-4:],  # Last 2 turns for context
            temperature=0.7,
            max_tokens=800
        )
        latency.checkpoint("llm_end")
        
        # Step 6: Safety post-processing
        response = safety.apply_disclaimers(response, query_type="fertility")
        response = safety.check_hallucination(response, rag_context)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": query[:500]})
        conversation_history.append({"role": "assistant", "content": response[:500]})
        
        # Generate latency report
        latency.stop()
        latency_report = latency.get_report()
        total_time = latency_report.get('total', 0)
        
        print(f"⚡ Total latency: {total_time:.2f}s")
        
        # Append latency to response
        response += f"\n\n---\n⚡ **Processing Time:** {total_time:.2f}s"
        if 'vlm' in latency_report:
            response += f" (VLM: {latency_report['vlm']:.2f}s"
        if 'rag' in latency_report:
            response += f" | RAG: {latency_report['rag']:.2f}s"
        if 'llm' in latency_report:
            response += f" | LLM: {latency_report['llm']:.2f}s)"
        
        return response
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return safety.get_error_message()

# Gradio Interface
with gr.Blocks(title="Tanit Fertility Companion") as demo:
    gr.Markdown("""
    # 🌸 Tanit Fertility Companion
    ### Multimodal AI Assistant powered by Qwen2-VL + GraphRAG
    *Your warm, evidence-based guide through fertility care*
    """)
    
    gr.Markdown("""
    ### ✅ Production Mode Active
    - Real AI models: Qwen2-VL-2B + Qwen2.5-3B + faster-whisper
    - GraphRAG medical knowledge grounding
    - Voice, image, and text inputs supported
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            # Input modalities
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
                    label="📸 Upload Lab Results / Ultrasound (optional)",
                    type="filepath"
                )
            
            pdf_input = gr.File(
                label="📄 Upload Medical PDF (optional)",
                file_types=[".pdf"]
            )
            
            submit_btn = gr.Button("Send Message", variant="primary", size="lg")
        
        with gr.Column(scale=2):
            gr.Markdown("""
            ### 💡 Try These Examples:
            **Voice:** "I'm 34, my AMH is 1.1, should I be worried?"
            
            **Image:** Upload hormone panel screenshot
            
            **Text:** "Explain my FSH results"
            
            **Note:** First query may take 30-60s as models warm up
            """)
    
    # Output
    output = gr.Markdown(label="Tanit's Response")
    
    # Example queries
    gr.Examples(
        examples=[
            ["What does an AMH of 1.5 ng/mL mean at age 32?", None, None, None],
            ["I have PCOS and irregular cycles. How do I track ovulation?", None, None, None],
            ["Explain FSH testing and what the results mean for fertility", None, None, None],
        ],
        inputs=[text_input, audio_input, image_input, pdf_input]
    )
    
    # Medical disclaimer
    gr.Markdown("""
    ---
    ⚠️ **Medical Disclaimer:** This AI provides educational information based on clinical guidelines. 
    It cannot diagnose conditions or replace consultation with your reproductive endocrinologist.
    Always seek professional medical advice for your specific situation.
    """)
    
    # Event handler
    submit_btn.click(
        fn=process_multimodal_input,
        inputs=[text_input, audio_input, image_input, pdf_input],
        outputs=output
    )

if __name__ == "__main__":
    print("✅ Production app ready!")
    print("🌐 Launching Gradio interface...")
    demo.launch(share=True, server_name="0.0.0.0")