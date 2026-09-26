# AI notes

## Topics I've written up

| Topic | File | Date |
|---|---|---|
| Ollama + running my first local LLM | [01-ollama-first-llm.md](01-ollama-first-llm.md) | 2026-09-26 |

## Things to learn (roughly in build order)

Tick a box once I've written the note.

**Local LLMs**
- [ ] How an LLM runs on my Mac: memory, unified memory, tokens/sec
- [ ] Quantization: what 4-bit / Q4_K_M means
- [ ] Ollama: pull, run, the HTTP API
- [ ] Prompting a small model: system prompts, keeping output short
- [ ] "Thinking" vs non-thinking mode (Qwen 3.5)
- [ ] Structured output (getting JSON back reliably)
- [ ] Comparing models: Qwen 3.5 4B vs Gemma 4 E4B (my own benchmark)

**Voice**
- [ ] Audio basics: sample rate, PCM, mono, 16 kHz
- [ ] VAD: how Silero decides "someone is talking"
- [ ] STT: Moonshine vs Whisper, streaming vs batch
- [ ] TTS: how Kokoro works, voices, latency
- [ ] ONNX: what it is and why models ship in it

**Putting it together**
- [ ] Latency budget: mic → text → LLM → speech, and where the time goes
- [ ] Running several models in 16 GB without swapping
