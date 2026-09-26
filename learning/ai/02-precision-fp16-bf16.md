# Why 16-bit? And what's the difference between FP16 and BF16?

**Date started:** 2026-09-26
**Used in project:** background for `01-ollama-first-llm.md` (quantization: 16-bit weights -> 4-bit)

## In one sentence
A weight is stored as a **floating point number** (sign + exponent + mantissa, like binary
scientific notation); 16 bits is the standard for **training** because it's the cheapest format
that's still precise enough for learning to work, and BF16 vs FP16 is two different ways of
splitting those 16 bits between "how big a number can be" and "how precise it is."

---

## Floating point, in plain words

A float is basically: **sign x (a base number) x 2^(exponent)** — same idea as `6.02 x 10^23`
in scientific notation, just in binary.

- **Sign** (1 bit): positive or negative.
- **Exponent bits**: how big or small the number can get (the "zoom level").
- **Mantissa bits**: how many precise digits it keeps once zoomed in.

More exponent bits = wider **range** (very huge and very tiny numbers, without overflowing to
infinity or underflowing to zero).
More mantissa bits = finer **precision** (more exact digits, smaller gaps between representable numbers).
16 bits total has to split between these two, and that split is exactly what makes FP16 and BF16 different.

---

## FP16 vs BF16

Both use 16 bits total. They split them differently:

```
FP16   (IEEE half precision)
  [S] [ 5 exponent bits ] [   10 mantissa bits   ]
       narrower range         more precision

BF16   ("brain float", from Google Brain)
  [S] [   8 exponent bits   ] [ 7 mantissa bits ]
       same range as FP32          less precision
```

| | FP16 | BF16 | FP32 (for comparison) |
|---|---|---|---|
| Exponent bits | 5 | 8 | 8 |
| Mantissa bits | 10 | 7 | 23 |
| Range | narrow — overflows around ±65,504 | same huge range as FP32 (~1e-38 to ~3e38) | huge |
| Precision | higher (more exact digits) | lower (coarser steps) | highest |

### Why this matters for training an LLM

- During training, some numbers in the network (activations, gradients) can get **very large or
  very small** at different points.
- **FP16** has a narrow range. If a number in training grows past ~65,504, it **overflows** and
  becomes infinity/garbage. Training with FP16 needs a workaround called "loss scaling" to avoid this.
- **BF16** keeps FP32's wide range (same 8 exponent bits), so it basically never overflows,
  at the cost of coarser precision (fewer mantissa bits). Training tolerates that fine — it's
  already a bit noisy from other sources (random batch order, dropout, etc.) — see `01-ollama-first-llm.md`.
- That's why **BF16 is the default for training and storing modern LLMs** (Qwen, Llama, Gemma, ...),
  and FP16 is less common today outside of some inference-only setups.
- Converting BF16 <-> FP32 is also cheap: just truncate/pad the mantissa, since the exponent
  layout already matches. That made it easy for hardware and software to adopt.

---

## Why 16 bits at all, and not 32 or 8?

Training repeatedly nudges every weight by a tiny amount (the gradient), e.g. 0.0001.

- **Too few bits (8-bit)**: the nudge is too small to represent, rounds to zero, the model
  doesn't learn.
- **32-bit**: precise enough, and was the old default, but doubles memory and compute cost
  for accuracy that training doesn't actually need.
- **16-bit (BF16)**: the sweet spot — precise enough for the tiny updates to register, half
  the memory of 32-bit, and modern GPUs have hardware built specifically to do 16-bit math fast.

Once training is finished, the weights are **frozen** — no more tiny accumulating updates,
just repeated multiplication with fixed numbers. That's a much easier job, which is why it
tolerates being rounded down further (**quantization**) to 8-bit or 4-bit for local/inference
use, without the model "forgetting" much. See `01-ollama-first-llm.md` for how that gets me
from an ~8 GB file down to the ~3 GB one I'm running.

## Gotchas / mistakes I made
-

## Questions still open
- How exactly does 4-bit quantization work if a float needs an exponent + mantissa — does
  4-bit still use floating point, or something else (e.g. integers + a scale factor)?

## Links
- https://en.wikipedia.org/wiki/Bfloat16_floating-point_format
- https://en.wikipedia.org/wiki/Half-precision_floating-point_format
