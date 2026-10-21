# Prompting a small model to summarize coding-agent events

**Date started:** 2026-10-20
**Used in project:** `scripts/summarize_samples.py` (Phase 2 step 3); becomes the AI service's
`POST /summarize` prompt in step 5

## In one sentence
An LLM is stateless and only knows what's in the prompt, so most of the work in getting good
summaries was **giving it the right context** (what the event is, who did it, whether it
failed, what call a result belongs to), and the rest was **showing it the style I want**
(few-shot examples) instead of describing it.

## Why I needed it
Walkie's timeline needs a one-line summary per event. The first naive prompt produced summaries
that were wrong, answered the event instead of summarizing it, or were three times longer than
needed. Every wasted token costs ~60 ms on my M1.

## How it works

### The test set
17 real events from `backend/walkie.db` (`scripts/samples.json`, gitignored): short and long
prompts, short and very long replies, Bash/Write/browser tool calls, their results, a trivial
`ok`, and one failure (exit code 1). Every tool result is paired with its tool call.

### Baseline: what went wrong, and why
Naive prompt: system = "Summarize this event in one short line", user message = the event's raw
`text`. Each failure had a context cause:

| | What happened | Cause |
|---|---|---|
| A | `ok` → *"Please provide the event you would like me to summarize!"*; "commit it, one commit per step." → *"Please provide…"* | The event text was sent **as the user's message**, so the model replied *to* it instead of summarizing it. |
| B | An exit-code-1 failure → *"Development progress was made on the FastAPI backend…"* | The model only got `text`. It never saw `is_error`, so it summarized the bulk of the output (commit messages) and ignored "Exit code 1". |
| C | *"**The user** executed commands…"* (it was the assistant); a browser result repeated its call | No one told it who the actors were; results were summarized without their calls. |
| D | 9–42 tokens per summary, full sentences | "One short line" is vague; nothing showed what *short* means. |

### Fixes
1. **Instruction + clearly delimited data in the user message:**
   ```
   Summarize this event:
   <event> ... </event>
   ```
   The `<event>` tags label it as data to summarize, not something to answer. Also safer:
   event text could one day contain "ignore your instructions…".
2. **State the facts I have as fields, don't make it guess:** `Kind`, `Tool`, `Status: OK/FAILED`,
   and label the text by kind (`Message` / `Input` / `Output`). A raw `is_error: False` reads like
   "failed": the model wrote "attempted to…" for a call that succeeded.
3. **Group by meaning, not by row.** A tool result means nothing without its call ("ok"), so
   call + result (linked by `tool_use_id`) is **one unit, summarized once**. Prompts and replies
   stay single.
   - The model is **stateless**: every call starts from zero. But don't send the whole session
     each time: reading grows with it. Send the **smallest context that makes the summary
     correct**. (The triggering prompt could be added as a short `Context:` line if pairs are
     still ambiguous; one prompt can trigger 20+ tool calls, so it's costly to repeat.)
4. **Say who the actors are, in the text.** Two different conversations both say "user":
   ```
   The watched session (DATA):  human ──prompt──▶ coding agent ──tool calls──▶ ...
   My script → Gemma (API):     system = my rules | user = my request | assistant = Gemma's answer
   ```
   The API roles describe *my script talking to Gemma*. Who did what in the event goes **inside
   the event block** (`Actor: the user` / `Actor: the assistant (Claude Code)`). Never send the
   agent's reply under role `assistant`: Gemma would think it wrote it.
5. **System vs user message.** System = standing rules, identical every call (and first in the
   prompt, so it gets **cached**). User = this request: just "Summarize this event:" + the event.
6. **Agent-agnostic.** No agent name in the instructions; the agent comes from each event's
   `app` field (`claude-code` → "Claude Code"). One prompt for every agent, still cacheable.
   Agent quirks belong in the adapter (e.g. Claude Code stores background-task notifications as
   user messages; the adapter should map them to `kind: status`).
7. **Few-shot examples + temperature 0** (below).

### Few-shot examples
Zero-shot = *describe* the output ("one short line"). Few-shot = *show* 2–8 finished examples
(event → summary). A 4B model copies a pattern far better than it follows a description: from the
examples it picks up verb-first, no subject, under 8 words, results include the outcome
("Ran tests: 48 passed"), prompts start with "Asked…", replies with "Explained…".

- **Never use test-set events as examples**: the model partly copies them and the test lies.
- **Cover the cases that matter**, especially failures. With one failure example the model
  wrote "Failed scaffold regeneration and file operations" (no reason). A rule ("If Status is
  FAILED, say what failed and why") + a second, different failure example fixed it:
  "Failed scaffold regeneration: directory not found", which matches the real error.
- Watch for copying *content* (e.g. inventing "48 passed"). If it happens, change the examples'
  content, not their style.

### Temperature
At each step the model gives a probability for every possible next token; temperature controls
how it picks. **0 = always the most likely token** (consistent, faithful); 1 = pick in proportion
to the probabilities (varied). `gemma4:e4b` defaults to **1**
(`ollama show gemma4:e4b --parameters`), which is why step 1's sky answers changed wording each
run. For summaries: 0. It also makes prompt experiments fair: a change in output comes from my
change, not chance.

## Minimal example
Same 17 events, same model, writing time only (prompt reading was mostly cached):

| | Calls | Tokens per summary | Writing time, all events |
|---|---|---|---|
| Baseline (naive prompt, one call per row) | 17 | 9–42, avg ~21 | ~19.7 s |
| + delimited event, fields, pairs, actors | 11 | 11–41 | ~13.0 s |
| + few-shot examples, temperature 0, failure rule | 11 | **7–13, avg ~9** | **~5.4 s** |

About **3.6× less time per event** (pairing cut 17 calls to 11; few-shot cut tokens by more than half).
At ~0.5 s per summary: roughly **100+ summaries a minute** from one local model.

Final output, for example:
```
tool_call + tool_result | Listed stored sessions via REST call
tool_call + tool_result | Created types.ts with event and session interfaces
tool_call + tool_result | Failed scaffold regeneration: directory not found
prompt                  | Asked to explain commands and venv management
reply                   | Explained project environment setup for Python and JS
```

## Gotchas / mistakes I made
- `result.seconds` is a method (`seconds("eval_duration")`); printing it without calling gave
  `<bound method …>`.
- `os.getcwd()`-based paths break when run from another folder; `Path(__file__).parent` doesn't.
- My loop variable `events` overwrote the outer `events` list.
- Timings looked great partly because of **prompt caching** from earlier runs
  (`prompt_eval_cached_count` ≈ `prompt_eval_count`). Caching only works when the *start* of the
  prompt is identical, so: fixed instructions first, changing event text last.
- Thinking tokens count toward `num_predict`: with thinking on, a small limit can produce an empty answer.
- Copying few-shot examples into the prompt, the "who is who" sentence ended up after the last
  example, where it read like part of it. Rules first, then examples.

## Questions still open
- Which events skip the LLM entirely? Tool calls already carry the agent's own `description`;
  trivial results (`ok`, "File created successfully") could be summarized from the call alone.
- How much of a very long `text` to send (truncate to N characters?), measured with a cold cache.
- Does `qwen3.5:4b` summarize better than `gemma4:e4b` with the same prompt?
- Adapter: map Claude Code's background-task notifications to `kind: status`.

## Links
- Few-shot prompting: https://www.promptingguide.ai/techniques/fewshot
- Ollama model parameters (temperature, num_predict): https://docs.ollama.com/modelfile
