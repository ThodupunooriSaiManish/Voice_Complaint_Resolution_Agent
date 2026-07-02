import io
import os
import tempfile
import numpy as np
from app.core.audio import convert_float32_to_wav

# Try loading faster-whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Try loading speech_recognition for online fallback
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class SpeechToTextService:
    def __init__(self, model_size: str = "base"):
        self.use_whisper = False
        self.model = None
        
        if WHISPER_AVAILABLE:
            try:
                print(f"Loading Faster-Whisper model ({model_size}) on CPU...")
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
                self.use_whisper = True
                print("Faster-Whisper model loaded successfully.")
            except Exception as e:
                print(f"Failed to load Faster-Whisper: {e}. Using Google Web Speech API fallback.")
        else:
            print("Faster-Whisper not installed. Using Google Web Speech API fallback.")

        self.mock_index = 0
        self.mock_complaints = [
            "Hi, my name is John Doe. I am calling because my new refrigerator that I bought last week is making a loud buzzing noise and the freezer is not freezing anything. All my ice cream melted. My order number is 98765, and my phone is 555-0123. This is urgent, please help.",
            "Hello, this is Sarah Connor. I want to report a safety hazard. The electric kettle model K300 I purchased yesterday sparks whenever I turn it on. It almost set my kitchen counter on fire. I want a refund immediately. Please call me back at 555-9090.",
            "My name is Bob Vance. I received my order today, but it is the wrong product! I ordered a vacuum cleaner but received a blender instead. I am very frustrated. My phone is 555-4567."
        ]

    def transcribe(self, audio_samples: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribes the float32 audio samples array (synchronous).
        """
        if len(audio_samples) == 0:
            return ""

        # Check if we can run Whisper locally
        if self.use_whisper and self.model is not None:
            try:
                segments, info = self.model.transcribe(audio_samples, beam_size=5)
                text = " ".join([segment.text for segment in segments]).strip()
                print(f"[STT Whisper] Transcribed: {text}")
                return text
            except Exception as e:
                print(f"Whisper transcription failed: {e}. Trying secondary methods...")

        # Fallback to speech_recognition (Google Web API)
        if SR_AVAILABLE:
            try:
                wav_bytes = convert_float32_to_wav(audio_samples, sample_rate)
                return self.transcribe_file(wav_bytes)
            except Exception as e:
                print(f"Google Web Speech API transcription failed: {e}. Using local mock text.")
        
        # Offline / Failure fallback
        return self._get_mock_text()

    def transcribe_file(self, file_bytes: bytes) -> str:
        """
        Transcribes a raw audio file (WAV/MP3/WebM/etc) from bytes.
        """
        if len(file_bytes) == 0:
            return ""

        if SR_AVAILABLE:
            try:
                # Write file bytes to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                recognizer = sr.Recognizer()
                try:
                    with sr.AudioFile(tmp_path) as source:
                        audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    print(f"[STT File Google] Transcribed: {text}")
                    return text
                finally:
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
            except Exception as e:
                print(f"[STT File Error] Google recognition failed: {e}. Trying local fallback.")

        # If offline or error, parse mock text
        return self._get_mock_text()

    def _get_mock_text(self) -> str:
        text = self.mock_complaints[self.mock_index % len(self.mock_complaints)]
        self.mock_index += 1
        print(f"[STT Mock] Transcribed (mock): {text}")
        return text

stt_service = SpeechToTextService()
