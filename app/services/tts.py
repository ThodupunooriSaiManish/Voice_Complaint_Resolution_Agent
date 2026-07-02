import io
import os
import tempfile

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

class TextToSpeechService:
    def __init__(self):
        self.pyttsx3_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                # Initialize pyttsx3 offline engine
                self.pyttsx3_engine = pyttsx3.init()
                # Set default voice properties
                self.pyttsx3_engine.setProperty('rate', 150)
            except Exception as e:
                print(f"Failed to initialize pyttsx3: {e}")

    def synthesize(self, text: str) -> bytes:
        """
        Synthesizes text into audio bytes (synchronous).
        """
        if not text:
            return b""
            
        print(f"[TTS] Synthesizing text: {text[:60]}...")

        # 1. Try Google Text-To-Speech (gTTS) - Online, high-quality, lightweight
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_bytes = fp.read()
                print("[TTS gTTS] Synthesized successfully.")
                return audio_bytes
            except Exception as e:
                print(f"gTTS synthesis failed: {e}. Trying offline fallbacks...")

        # 2. Try pyttsx3 - Offline, Windows Native SAPI5
        if PYTTSX3_AVAILABLE and self.pyttsx3_engine is not None:
            try:
                # pyttsx3 works by saving to file since direct in-memory stream is platform-dependent
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_name = tmp.name
                
                # Run synthesis to file
                self.pyttsx3_engine.save_to_file(text, tmp_name)
                self.pyttsx3_engine.runAndWait()
                
                with open(tmp_name, "rb") as f:
                    audio_bytes = f.read()
                
                # Cleanup
                try:
                    os.unlink(tmp_name)
                except Exception:
                    pass
                    
                print("[TTS pyttsx3] Synthesized offline WAV successfully.")
                return audio_bytes
            except Exception as e:
                print(f"pyttsx3 synthesis failed: {e}. Returning mock silent audio.")

        # 3. Fallback: Return a silent or basic audio file (WAV structure) to prevent crashes
        # A tiny 1-second silent mono 16kHz WAV file
        print("[TTS Mock] Returning mock silent audio bytes.")
        import wave
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # Write 8000 samples of silence (0.5s)
            wav_file.writeframes(b'\x00' * 16000)
        return wav_io.getvalue()

tts_service = TextToSpeechService()
