from faster_whisper import WhisperModel

class STTHandler:
    def __init__(self, model_size="medium"):
        """
        faster-whisper: 4x faster than OpenAI Whisper, runs on CPU
        - "medium" model: best accuracy/speed tradeoff for medical terminology
        - <1s latency even on CPU
        """
        print(f"Loading faster-whisper '{model_size}' model...")
        self.model = WhisperModel(
            model_size,
            device="cpu",  # Runs efficiently on CPU
            compute_type="int8"  # Quantized for speed
        )
        print("STT model loaded")
    
    def transcribe(self, audio_path):
        """
        Transcribe audio file to text with medical vocabulary support
        """
        segments, info = self.model.transcribe(
            audio_path,
            language="en",  # Auto-detect if None
            beam_size=5,
            vad_filter=True  # Voice activity detection
        )
        
        # Combine all segments
        transcript = " ".join([segment.text for segment in segments])
        
        print(f"Transcribed: {transcript[:100]}...")
        return transcript.strip()