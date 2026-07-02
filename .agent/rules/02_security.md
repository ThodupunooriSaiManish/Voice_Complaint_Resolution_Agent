# Security and Guardrails Guidelines

This document outlines security practices and data handling guardrails.

## 1. PII Redaction
- Ensure that transcripts containing potential sensitive information like Credit Cards or Passwords are masked/redacted before database storage or printing to logs.
- Standard regex checking for credit cards: `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b`.

## 2. Temporary Data Management
- Audio chunks streamed over WebSockets must reside purely in memory (in-memory Float32/Int16 array buffers).
- Once speech segmentation completes and STT transcription succeeds, clear the active in-memory audio buffers.
- Save temporary WAV files to the local `data/` cache only if debugging is enabled, and delete them on server shutdown.

## 3. Prompt Injection Prevention
- Subagents parsing transcription text must treat user utterances strictly as data.
- Wrap user transcriptions in strict XML tags or JSON property boundaries within LLM prompts (e.g., `<user_transcript>...</user_transcript>`) to prevent prompt injections from overriding agent behavior.
- Validate all structured outputs from subagents against the defined schemas. If parsing fails, fall back to default neutral objects rather than failing or returning raw, unchecked text.
