# Glossary

Short definitions in my own words. Keep alphabetical.

| Term | Meaning | See |
|---|---|---|
| Adapter | Small plug-in that reads one AI app's activity and converts it to Walkie's common format | backend/ |
| BF16 | "Brain float 16": 16-bit format, same wide range as FP32 but less precision; the standard for training LLMs | ai/02 |
| Effective parameters | The "E" in Gemma's E2B/E4B: how many parameters actually need fast memory at once, thanks to PLE | ai/01 |
| FP16 | 16-bit float with more precision than BF16 but a much narrower range (can overflow) | ai/02 |
| FP32 | 32-bit float, the old "full precision" default; accurate but twice the memory of 16-bit | ai/02 |
| Inference | Running an already-trained model to get answers (what I do locally) | ai/01 |
| JSON Lines (.jsonl) | One JSON object per line; easy to append to and to tail | backend/01 |
| LLM | Large language model: predicts the next token of text | ai/ |
| Mantissa | The precise digits part of a float; more mantissa bits = finer precision | ai/02 |
| MCP | Model Context Protocol: open standard that lets AI apps call tools I write | backend/ |
| Offset | How many bytes of a file I've already read; where the next read starts | backend/03 |
| Ollama | App that downloads and runs local LLMs, with a server on :11434 | ai/01 |
| Parameters / weights | The billions of numbers learned during training; the model file is mostly these | ai/01 |
| Per-Layer Embeddings (PLE) | Gemma trick: keeps big embedding tables on disk/CPU RAM instead of GPU memory, loaded per layer as needed | ai/01 |
| Quantization | Storing model weights with fewer bits (e.g. 4-bit) so it fits in less memory | ai/ |
| STT | Speech-to-text | ai/ |
| Token | Chunk of text a model reads/writes (~¾ of a word) | ai/ |
| Tokens/sec (tok/s) | How fast a model writes; Ollama shows it as "eval rate" | ai/01 |
| Training | Teaching a model by tuning its weights on huge data; done by the model maker, not me | ai/01 |
| TTS | Text-to-speech | ai/ |
| Tailing | Reading only what's been appended to a file since last time (like `tail -f`) | backend/03 |
| Unified memory | Apple Silicon RAM shared by CPU and GPU, so models can use most of the 16 GB | ai/01 |
| VAD | Voice activity detection: detects when someone is speaking | ai/ |
| WebSocket | Two-way connection that stays open, so the server can push updates | frontend/ |
