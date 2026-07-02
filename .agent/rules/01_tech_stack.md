# Technical Stack Guidelines

This document specifies the technical design standards for the Voice Complaint Resolution Agent.

## 1. Backend Design (FastAPI & WebSockets)
- Use standard asynchronous endpoints (`async def`) for I/O bound operations (FastAPI, Motor DB, Ollama HTTP queries).
- WebSocket connection endpoint at `/ws/stream` to receive audio chunks and stream transcription/agent state updates.
- Keep the main event loop clean. Perform computationally heavy task operations (like signal processing or heavy text synthesis fallbacks) using custom thread executors if necessary.

## 2. LLM Engine (Ollama Local Llama 3)
- Connect using `http://localhost:11434/v1` (OpenAI compatibility layer) or direct `http://localhost:11434/api/chat` POST endpoints.
- Subagents MUST request structured JSON outputs. Use clear system instructions and structured prompting.
- Standard JSON mode or structured outputs (`format="json"`) should be used if supported, otherwise require the model to wrap the output in a markdown block ````json ... ````.

## 3. Robust Dual-Mode Fallbacks
- **VAD (Voice Activity Detection):**
  - Primary: `silero-vad` model loaded via ONNX.
  - Fallback: Root-Mean-Square (RMS) energy-based sliding window VAD.
- **STT (Speech-To-Text):**
  - Primary: `faster-whisper` (Whisper-base/small model).
  - Fallback: `speech_recognition` module connecting to Google Web Speech API, or rule-based mock matching text keywords if internet connection is down.
- **TTS (Text-To-Speech):**
  - Primary: `XTTS-v2` / `coqui-tts`.
  - Fallback: Google TTS (`gtts` package) generating MP3, or standard OS TTS (`pyttsx3`), or static base64 pre-rendered greeting/confirmation audio.
- **Database:**
  - Primary: `motor.motor_asyncio.AsyncIOMotorClient` connecting to local MongoDB `mongodb://localhost:27017`.
  - Fallback: Asynchronous JSON file repository (`data/db_fallback.json`).
