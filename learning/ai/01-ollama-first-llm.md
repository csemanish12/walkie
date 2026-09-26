# Ollama and running my first local LLM

**Date started:** 2026-09-26
**Used in project:** `ai/app/llm/` (summarizing AI app events, cleaning up voice input)

## In one sentence
Ollama is a free app that downloads ready-made AI models to my Mac and runs them there,
so I can chat with them or call them from code: no internet, no API key, no cost.

---

## Part 1 — The big idea: why I don't have to train anything

### Training vs running (inference)

There are two completely separate stages in an LLM's life:

```
   TRAINING  (done once, by Alibaba / Google / Meta ...)
   ------------------------------------------------------
   trillions of words of text
          |
          v
   thousands of GPUs for weeks, costs millions of $
          |
          v
   result: a file full of numbers  ("weights")      <-- this is what I download
          |
          |
   RUNNING / INFERENCE  (what I do, on my Mac)
   ------------------------------------------------------
   my prompt  -->  math using those numbers  -->  answer
```

- **Training** = the model *learns*. Hugely expensive. I never do this.
- **Inference** = the model *is used*. Cheap enough to run on a laptop.

Analogy: training is like a chef spending 10 years learning to cook. The **weights** are the
chef's trained brain, frozen. Downloading a model = hiring the already-trained chef.
I just give orders (prompts).

### What is actually inside a "model"?

A model file is mostly **one giant list of numbers** called **weights** (or **parameters**).

- "Qwen 3.5 **4B**" = about **4 billion** numbers.
- Those numbers were tuned during training so that the math produces sensible text.
- The file doesn't contain sentences or a database of facts. Everything it knows is spread through those numbers.

### How does it produce an answer?

An LLM only does one thing: **predict the next token** (a token is roughly ¾ of a word).

```
"The sky is"          -> model predicts " blue"
"The sky is blue"     -> model predicts " today"
"The sky is blue today" -> model predicts "."
... repeat until done
```

Each prediction = one pass of math through all ~4 billion weights.
Speed is measured in **tokens per second (tok/s)**. More tok/s means the answer appears faster.

---

## Part 2 — What "download and run locally" means

| | Cloud AI (e.g. Claude, ChatGPT) | Local AI (Ollama) |
|---|---|---|
| Where the model lives | Company's servers | A file on my disk |
| Where the math happens | Their GPUs | My Mac's GPU (M1) |
| Internet needed? | Yes, every time | Only to download once |
| Cost | Subscription / per use | Free |
| Privacy | Data sent to them | Never leaves my Mac |
| Smartness | Very high (huge models) | Lower (small models), but fine for simple jobs |

"Running locally" means:
1. The model file is loaded from disk into **memory (RAM)**.
2. The Mac's **GPU** does the math for each token.
3. The answer is printed. Nothing is sent anywhere.

### Why it fits on my Mac: quantization

- Normally each weight uses 16 bits (see [02-precision-fp16-bf16.md](02-precision-fp16-bf16.md) for why 16-bit, and FP16 vs BF16). 4B weights × 2 bytes = **~8 GB**. Too heavy.
- **Quantization** stores each weight in about **4 bits** instead, so the file is **~3 GB**.
- A bit less precise, but the answers are nearly as good. Most local models are shipped this way.
- My M1 has **16 GB unified memory**, meaning the CPU and GPU share the same RAM. A 3 GB model fits easily.

---

## Part 3 — What Ollama is

Ollama does three jobs:

```
+-------------------------------------------------------------+
|                           OLLAMA                            |
|                                                             |
|  1. Model manager    ollama pull / list / rm                |
|                      (like an app store for models)         |
|                                                             |
|  2. Model runner     loads weights, does the math on GPU    |
|                      (built on llama.cpp)                   |
|                                                             |
|  3. Local server     http://localhost:11434                 |
|                      so MY code can call the model          |
+-------------------------------------------------------------+
        ^                                   ^
        |                                   |
   me in the terminal               Walkie's ai/ service
   (ollama run ...)                 (HTTP requests)
```

Similar idea to Docker: `docker pull` / `docker run`, but for AI models.

Models are stored in `~/.ollama/models`.

---

## Part 4 — Step by step

> Tick each step as I go. Write what I saw in the **My notes** lines.

### Step 1 — Install Ollama
Pick one:

**A. Desktop app (easiest).** Download from https://ollama.com/download and drag it to Applications.
It adds a llama icon to the menu bar, and the server runs automatically.

**B. Homebrew (terminal).**
```bash
brew install ollama
```
With Homebrew I start the server myself (Step 3).

- [x] Done. My notes: ollama is installed

### Step 2 — Check it's installed
```bash
ollama --version
```
- [x] Done. Version I got: client version -> 0.34.4

### Step 3 — Make sure the server is running
If I used the desktop app, it's already running. With Homebrew, in a **separate terminal tab**:
```bash
ollama serve
```
Leave that tab open. Test it:
```bash
curl http://localhost:11434
```
Expected reply: `Ollama is running`

- [x] Done. My notes: got Ollama is running

### Step 4 — Download my first model
```bash
ollama pull qwen3.5:4b
```
- Downloads ~3 GB, once.
- `qwen3.5` = model family, `4b` = 4 billion parameters (the "tag").

Check it's there:
```bash
ollama list
```
- [x] Done. Size shown: 3.4GB . Make sure to keep ollama running otherwise pull will not work.

### Step 5 — Chat with it
```bash
ollama run qwen3.5:4b
```
Type a message and press Enter. Try:
- `Explain what a WebSocket is in 2 sentences.`
- `Summarize in 8 words: The agent read src/auth.ts, edited it, then ran npm test.`

Useful commands inside the chat:
- `/?` show help
- `/set nothink` turn off "thinking" mode (faster; Qwen 3.5 thinks out loud by default)
- `/bye` exit

- [x] Done. What surprised me: The thinking mode took way too much time compared to nothink mode.

### Step 6 — Measure speed
```bash
ollama run qwen3.5:4b --verbose
```
After each answer it prints stats. The important line is **eval rate** (tokens/sec).

- [x] Done. My eval rate: 18.53 tok/s

### Step 7 — See memory use
While a model is loaded (in another terminal tab):
```bash
ollama ps
```
Shows which model is loaded, how much memory it uses, and whether it's on the GPU.
Ollama unloads a model after ~5 minutes idle.

- [x] Done. Memory used: 3.2GB and 100% on GPU

### Step 8 — Call it from code (this is how Walkie will use it)
Instead of chatting in the terminal, send an HTTP request:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3.5:4b",
  "prompt": "Summarize in 8 words: The agent read src/auth.ts, edited it, then ran npm test.",
  "stream": false,
  "think": false
}'
```
The reply is JSON; the answer is in the `"response"` field.
This is exactly what `ai/app/llm/` will do later, just from Python instead of curl.

- [x] Done. My notes:

### Cleanup commands (for later)
```bash
ollama list              # what's downloaded
ollama rm qwen3.5:4b     # delete a model to free disk
ollama stop qwen3.5:4b   # unload from memory now
```

---

## My results

| Model | Size on disk | Memory (ollama ps) | Speed (tok/s) | Quality notes |
|---|---|---|---|---|
| qwen3.5:4b | 3.4 GB | 3.2GB | 18.53 | |
| gemma4:e4b (later) | | | | |

## Gotchas / mistakes I made
-

## Questions still open
- What does "thinking" mode actually do, and when is it worth the wait?
- What's the difference between `/api/generate` and `/api/chat`?
- How does the "context window" (256K for Qwen 3.5) affect memory?

## Links
- https://ollama.com (download, model library)
- https://ollama.com/library/qwen3.5 (the model I use)
- https://github.com/ollama/ollama/blob/main/docs/api.md (HTTP API reference)
