import os
import sys
import subprocess

def check_dependencies():
    """
    Checks if core dependencies are installed, otherwise prompts the user.
    """
    try:
        import streamlit
        import numpy
        import gtts
        import speech_recognition
        import httpx
        import pandas
    except ImportError as e:
        missing = e.name
        print(f"[*] Missing core python package: '{missing}'")
        print("[*] Installing required dependencies from requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("[+] Successfully installed dependencies.")
        except Exception as err:
            print(f"[-] Installation failed: {err}")
            sys.exit(1)

def generate_samples():
    """
    Generates sample audio files using the TTS service so the user has files
    ready to upload and test right away.
    """
    examples_dir = os.path.join("data", "examples")
    os.makedirs(examples_dir, exist_ok=True)
    
    # Import service after dependencies are confirmed
    from app.services.tts import tts_service
    
    samples = {
        "refrigerator_complaint.wav": (
            "Hi, my name is John Doe. I am calling because my new refrigerator that I bought last week "
            "is making a loud buzzing noise and the freezer is not freezing anything. All my ice cream melted. "
            "My order number is 98765, and my phone is 555-0123. This is urgent, please help."
        ),
        "kettle_spark_complaint.wav": (
            "Hello, this is Sarah Connor. I want to report a safety hazard. The electric kettle model K300 "
            "I purchased yesterday sparks whenever I turn it on. It almost set my kitchen counter on fire. "
            "I want a refund immediately. Please call me back at 555-9090."
        )
    }
    
    print("[*] Checking sample audio files in data/examples/...")
    for filename, text in samples.items():
        filepath = os.path.join(examples_dir, filename)
        if not os.path.exists(filepath):
            try:
                audio_bytes = tts_service.synthesize(text)
                with open(filepath, "wb") as f:
                    f.write(audio_bytes)
                print(f"[+] Generated sample audio: {filepath}")
            except Exception as e:
                print(f"[-] Failed to generate sample {filename}: {e}")

def main():
    print("=" * 60)
    print("      STREAMLIT VOICE COMPLAINT AGENT STARTUP")
    print("=" * 60)
    
    # 1. Check requirements
    check_dependencies()

    # 2. Ensure data directory exists and generate samples
    os.makedirs("data", exist_ok=True)
    generate_samples()
    
    # 3. Print helpful user guidelines
    print("\n[System Configuration Checklist]:")
    print(" - Ollama: Make sure Ollama is running and Llama 3 model is pulled:")
    print("           Command: ollama run llama3")
    print("           (If Ollama is down, a rule-based mock agent will act as fallback)")
    print(" - MongoDB: Ensure MongoDB is running at localhost:27017")
    print("           (If MongoDB is down, files will save to local 'data/db_fallback.json')")
    print(" - Speech-to-Text: Dual-mode active (Faster-Whisper on CPU or Google Cloud Speech API)")
    print(" - Text-to-Speech: Dual-mode active (gTTS or OS Native SAPI5 via pyttsx3)")
    print("\nStarting Streamlit UI dashboard server...\n")
    
    # 4. Run Streamlit
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "app/main.py"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nExiting server...")

if __name__ == "__main__":
    main()
