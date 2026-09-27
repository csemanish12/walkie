# AI notes

## Topics I've written up

| Topic | File | Date |
|---|---|---|
| Ollama + running my first local LLM | [01-ollama-first-llm.md](01-ollama-first-llm.md) | 2026-09-26 |
| Why 16-bit? FP16 vs BF16 | [02-precision-fp16-bf16.md](02-precision-fp16-bf16.md) | 2026-09-26 |

## Things to learn (roughly in build order)

Tick a box once I've written the note.

**Local LLMs**
- [ ] How an LLM runs on my Mac: memory, unified memory, tokens/sec
- [x] Quantization: what 4-bit / Q4_K_M means (partly — [see note](01-ollama-first-llm.md))
- [x] Precision: FP32 vs FP16 vs BF16 ([note](02-precision-fp16-bf16.md))
- [ ] Ollama: pull, run, the HTTP API
- [ ] Prompting a small model: system prompts, keeping output short
- [ ] "Thinking" vs non-thinking mode (Qwen 3.5)
- [ ] Structured output (getting JSON back reliably)
- [x] Comparing models: Qwen 3.5 4B vs Gemma 4 E4B ([results](01-ollama-first-llm.md))

**Voice**
- [ ] Audio basics: sample rate, PCM, mono, 16 kHz
- [ ] VAD: how Silero decides "someone is talking"
- [ ] STT: Moonshine vs Whisper, streaming vs batch
- [ ] TTS: how Kokoro works, voices, latency
- [ ] ONNX: what it is and why models ship in it

**Putting it together**
- [ ] Latency budget: mic → text → LLM → speech, and where the time goes
- [ ] Running several models in 16 GB without swapping
