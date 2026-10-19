# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Send one prompt to a local Ollama model and show the answer plus timing stats.

Every request option is a flag, so one setting can be changed at a time and compared:

    uv run scripts/ollama_chat.py "what is the color of sky?"
    uv run scripts/ollama_chat.py --think "what is the color of sky?"
    uv run scripts/ollama_chat.py --system "answer in one short plain-text line" "what is the color of sky?"
    uv run scripts/ollama_chat.py --temperature 0 --num-predict 40 "..."
    uv run scripts/ollama_chat.py --stream --think --show-thinking "..."
    uv run scripts/ollama_chat.py --print-payload --think "..."     # see the JSON sent to Ollama

The functions (ChatRequest, chat) can also be imported by other scripts, e.g. for step 3.
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:e4b"
NS_PER_S = 1e9  # Ollama reports every duration in nanoseconds


class OllamaError(Exception):
    """Ollama answered, but with an error (unknown model, bad request, ...)."""


@dataclass
class ChatRequest:
    """One /api/chat request. None means "leave it out and use Ollama's default"."""

    prompt: str
    model: str = DEFAULT_MODEL
    system: str | None = None
    think: bool = False
    stream: bool = False
    temperature: float | None = None
    num_predict: int | None = None  # max output tokens (thinking tokens count too)
    keep_alive: str | None = None  # how long to keep the model loaded afterwards, e.g. "30m"

    def to_payload(self) -> dict[str, Any]:
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": self.prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "think": self.think,
            "stream": self.stream,
        }
        # Sampling settings go in a nested "options" object, not at the top level.
        options = {"temperature": self.temperature, "num_predict": self.num_predict}
        options = {k: v for k, v in options.items() if v is not None}
        if options:
            payload["options"] = options
        if self.keep_alive is not None:
            payload["keep_alive"] = self.keep_alive
        return payload


@dataclass
class ChatResult:
    """The answer, the hidden thinking, and the final response's timing fields."""

    content: str
    thinking: str
    stats: dict[str, Any]

    @property
    def tokens(self) -> int:
        return self.stats.get("eval_count", 0)  # includes thinking tokens

    def seconds(self, field: str) -> float:
        return self.stats.get(field, 0) / NS_PER_S

    @property
    def cut_off(self) -> bool:
        """Stopped by the num_predict limit, not because the answer was finished."""
        return self.stats.get("done_reason") == "length"

    @property
    def tokens_per_second(self) -> float:
        # Writing speed only: output tokens over the time spent writing them.
        write_s = self.seconds("eval_duration")
        return self.tokens / write_s if write_s else 0.0

    def summary(self) -> str:
        return (
            f"{self.tokens} tokens | {self.seconds('total_duration'):.2f} s total"
            f" | {self.seconds('load_duration'):.2f} s loading"
            f" | {self.seconds('prompt_eval_duration'):.2f} s reading prompt"
            f" | {self.seconds('eval_duration'):.2f} s writing"
            f" | {self.tokens_per_second:.1f} tok/s"
        )


OnChunk = Callable[[str, str], None]  # (thinking piece, content piece)


def chat(client: httpx.Client, request: ChatRequest, on_chunk: OnChunk | None = None) -> ChatResult:
    """Send one request. When streaming, on_chunk is called with each piece as it arrives."""
    payload = request.to_payload()
    if not request.stream:
        response = client.post("/api/chat", json=payload)
        _raise_for_ollama_error(response)
        data = response.json()
        message = data.get("message", {})
        return ChatResult(message.get("content", ""), message.get("thinking", ""), data)

    content: list[str] = []
    thinking: list[str] = []
    final: dict[str, Any] = {}
    with client.stream("POST", "/api/chat", json=payload) as response:
        _raise_for_ollama_error(response)
        # One JSON object per line: thinking pieces, then content pieces, then done=true with stats.
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if "error" in chunk:
                raise OllamaError(chunk["error"])
            message = chunk.get("message", {})
            think_piece = message.get("thinking", "")
            content_piece = message.get("content", "")
            thinking.append(think_piece)
            content.append(content_piece)
            if on_chunk:
                on_chunk(think_piece, content_piece)
            if chunk.get("done"):
                final = chunk
    return ChatResult("".join(content), "".join(thinking), final)


def _raise_for_ollama_error(response: httpx.Response) -> None:
    """Turn a 4xx/5xx into an OllamaError carrying Ollama's own error message."""
    if response.status_code < 400:
        return
    response.read()  # a streamed response has no body loaded yet
    try:
        detail = response.json().get("error", response.text)
    except ValueError:
        detail = response.text
    raise OllamaError(f"{response.status_code}: {detail}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prompt", help="the user message")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--system", help="system message: instructions on how to answer")
    p.add_argument(
        "--think", action=argparse.BooleanOptionalAction, default=False, help="reasoning mode (default: off)"
    )
    p.add_argument(
        "--stream", action=argparse.BooleanOptionalAction, default=False, help="print the answer as it's written"
    )
    p.add_argument("--temperature", type=float, help="0 = most predictable; Ollama's default if unset")
    p.add_argument("--num-predict", type=int, help="max output tokens, bounds the worst-case time")
    p.add_argument("--keep-alive", help='keep the model loaded this long afterwards, e.g. "30m"')
    p.add_argument("--show-thinking", action="store_true", help="also print the thinking text")
    p.add_argument("--print-payload", action="store_true", help="print the JSON sent to Ollama first")
    p.add_argument("--timeout", type=float, default=120.0, help="seconds to wait for the answer (default: 120)")
    p.add_argument("--url", default=OLLAMA_URL)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    request = ChatRequest(
        prompt=args.prompt,
        model=args.model,
        system=args.system,
        think=args.think,
        stream=args.stream,
        temperature=args.temperature,
        num_predict=args.num_predict,
        keep_alive=args.keep_alive,
    )
    if args.print_payload:
        print(json.dumps(request.to_payload(), indent=2), end="\n\n")

    def show_live(think_piece: str, content_piece: str) -> None:
        if args.show_thinking and think_piece:
            print(f"\033[2m{think_piece}\033[0m", end="", flush=True)  # dim
        print(content_piece, end="", flush=True)

    # Connecting should be instant; only the answer itself may take long.
    timeout = httpx.Timeout(args.timeout, connect=2.0)
    try:
        with httpx.Client(base_url=args.url, timeout=timeout) as client:
            result = chat(client, request, on_chunk=show_live if args.stream else None)
    except httpx.ConnectError:
        print(f"Ollama isn't running at {args.url}", file=sys.stderr)
        return 1
    except httpx.TimeoutException:
        print(f"Timed out after {args.timeout:g} s (model loading? long answer? try --num-predict)", file=sys.stderr)
        return 1
    except OllamaError as e:
        print(f"Ollama error {e}", file=sys.stderr)
        return 1

    if args.stream:
        print()
    else:
        if args.show_thinking and result.thinking:
            print(f"\033[2m{result.thinking}\033[0m\n")
        print(result.content)
    print(f"\n{result.summary()}")
    if result.cut_off:
        # Thinking tokens count toward num_predict, so thinking can use up the whole budget.
        where = "while still thinking, so there's no answer" if not result.content else "mid-answer"
        print(f"⚠ Hit the --num-predict limit {where}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
