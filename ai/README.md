# AI service

Python service. Runs on http://localhost:8100. Only the backend calls it.

## Folders
```
app/
  vad/   Silero VAD: detect speech
  stt/   Moonshine: speech -> text
  tts/   Kokoro: text -> speech
  llm/   Ollama client (Qwen 3.5 4B): summarize, clean up
```

## Endpoints (draft)
- `POST /stt`: audio in, text out
- `POST /tts`: text in, audio out
- `POST /summarize`: event in, one-line summary out
- `POST /clean`: raw spoken text in, clear instruction out

## Setup (not done yet)
```bash
brew install ollama        # or download from ollama.com
ollama pull qwen3.5:4b
uv init
```
