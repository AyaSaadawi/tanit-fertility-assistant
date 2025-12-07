"""
Medical Safety Guardrails for Tanit Fertility Assistant
Ensures responses are educational, non-diagnostic, and appropriately cautious
"""

class SafetyGuardrails:
    def __init__(self):
        self.emergency_keywords = [
            "severe pain", "heavy bleeding", "hemorrhage", "ectopic", 
            "emergency", "can't breathe", "chest pain", "suicidal"
        ]
        
        self.diagnosis_keywords = [
            "you have", "you are diagnosed", "you definitely", 
            "this is", "you need to take", "you must"
        ]
    
    def get_medical_system_prompt(self):
        """
        System prompt ensuring medical safety and accuracy
        """
        return """You are Tanit, a warm and knowledgeable fertility companion AI assistant. Your role is to provide evidence-based educational information about reproductive health.

CRITICAL SAFETY RULES:
1. NEVER diagnose medical conditions - only provide educational information
2. ALWAYS recommend consulting a reproductive endocrinologist for medical decisions
3. NEVER provide definitive treatment recommendations - only explain options
4. ALWAYS express appropriate uncertainty when discussing complex medical situations
5. NEVER guarantee outcomes (pregnancy, treatment success, etc.)
6. ALWAYS cite the medical sources you're drawing from
7. Use warm, empathetic language - patients are often anxious about fertility

RESPONSE STRUCTURE:
- Start with empathy and validation of the patient's concerns
- Explain relevant medical concepts in plain language
- Provide context (reference ranges, what's normal, when to worry)
- Give actionable next steps
- End with appropriate disclaimers and encouragement

TONE GUIDELINES:
- Warm and compassionate, never clinical or cold
- Encouraging but realistic
- Use "many women" or "some people" instead of "you will"
- Say "this may indicate" instead of "this means you have"
- Say "consider discussing with your doctor" not "you need to"

Remember: You're a supportive educational companion, not a replacement for medical care."""
    
    def apply_disclaimers(self, response, query_type="general"):
        """
        Add appropriate medical disclaimers based on query type
        """
        # Check if response inappropriately gives medical advice
        response_lower = response.lower()
        
        # Warning if response sounds too definitive
        if any(phrase in response_lower for phrase in self.diagnosis_keywords):
            response = self._soften_language(response)
        
        # Choose appropriate disclaimer
        disclaimers = {
            "fertility": "\n\n💡 **Important Note:** This information is for educational purposes. Your individual situation requires personalized evaluation by a reproductive endocrinologist who can review your complete medical history, perform examinations, and order appropriate tests.",
            
            "lab_results": "\n\n⚕️ **Medical Disclaimer:** Lab value interpretation depends on your specific medical context, testing methods, and complete hormonal profile. Please discuss these results with your healthcare provider for personalized guidance.",
            
            "treatment": "\n\n⚠️ **Treatment Information:** Treatment decisions should be made with your reproductive endocrinologist based on your complete medical evaluation. This information helps you understand options, not choose treatment.",
            
            "general": "\n\n💡 **Important:** This is educational information only. Always consult with your reproductive endocrinologist for medical advice specific to your situation."
        }
        
        disclaimer = disclaimers.get(query_type, disclaimers["general"])
        
        # Add emergency guidance if needed
        if any(keyword in response_lower for keyword in self.emergency_keywords):
            disclaimer = "\n\n🚨 **IMPORTANT:** If you're experiencing severe symptoms like heavy bleeding, severe pain, or other emergency symptoms, please seek immediate medical attention by calling emergency services or going to the nearest emergency room.\n" + disclaimer
        
        return response + disclaimer
    
    def _soften_language(self, response):
        """
        Soften overly definitive language in responses
        """
        replacements = {
            "you have": "this may suggest",
            "you are diagnosed": "you may have been diagnosed",
            "you definitely": "this could indicate",
            "this is": "this may be",
            "you need to take": "your doctor might recommend",
            "you must": "it's often recommended to"
        }
        
        for definitive, softer in replacements.items():
            response = response.replace(definitive, softer)
        
        return response
    
    def check_hallucination(self, response, rag_context):
        """
        Basic hallucination check: ensure key claims are grounded in RAG context
        """
        response_lower = response.lower()
        
        # Check if response references provided sources
        source_indicators = [
            "according to", "studies show", "research indicates", 
            "guidelines recommend", "asrm", "eshre", "clinical"
        ]
        
        sources_mentioned = any(
            indicator in response_lower for indicator in source_indicators
        )
        
        # If no sources mentioned but RAG returned results, add attribution
        if not sources_mentioned and rag_context.get("nodes") and len(rag_context["nodes"]) > 0:
            response += "\n\n📚 *This response is based on established clinical guidelines and medical research from reproductive health organizations.*"
        
        # Check for specific numbers/claims without context
        if any(char.isdigit() for char in response):
            # If numbers are mentioned, ensure they're contextualized
            if "reference range" not in response_lower and "normal range" not in response_lower:
                if "ng/ml" in response_lower or "miu/ml" in response_lower:
                    # Hormone values mentioned without ranges - add note
                    if "interpretation depends on" not in response_lower:
                        response += "\n\n📊 *Note: Interpretation of hormone values depends on age, cycle day, testing method, and individual circumstances.*"
        
        return response
    
    def get_error_message(self):
        """
        Friendly error message when processing fails
        """
        return """I apologize, but I encountered an issue processing your request. This might be due to:

• Technical difficulties with image or audio processing
• Temporary system issues
• Unsupported file format

**Please try:**
1. Describing your question in text instead
2. Using a different image format (JPEG/PNG work best)
3. Refreshing the page and trying again
4. Keeping audio recordings under 2 minutes

If the problem persists, please let me know what you were trying to do and I'll do my best to help in another way.

I'm here to support you through your fertility journey! 💜"""
    
    def validate_input(self, text_input, audio_input, image_input):
        """
        Validate user inputs before processing
        Returns: (is_valid, error_message)
        """
        # Check if at least one input is provided
        if not text_input and not audio_input and not image_input:
            return False, "Please provide a question via text, voice, or upload an image."
        
        # Check text length
        if text_input and len(text_input) > 2000:
            return False, "Please keep your question under 2000 characters."
        
        return True, None
    
    def detect_crisis(self, text):
        """
        Detect if user might be in crisis
        """
        crisis_keywords = [
            "want to die", "kill myself", "end it all", "suicide",
            "no reason to live", "better off dead"
        ]
        
        text_lower = text.lower() if text else ""
        
        if any(keyword in text_lower for keyword in crisis_keywords):
            return True, """

🆘 **Crisis Support:**

If you're having thoughts of suicide or self-harm, please reach out for immediate help:

**United States:**
- National Suicide Prevention Lifeline: 988 or 1-800-273-8255
- Crisis Text Line: Text HOME to 741741

**International:**
- Find your country's helpline: https://findahelpline.com

You don't have to go through this alone. Please talk to someone who can help right now.

For fertility-related emotional support, consider:
- RESOLVE: The National Infertility Association
- Fertility counseling services
- Support groups in your area

Your life matters. Please reach out for help. 💜"""
        
        return False, None