"""StepGame dataset loading and prompt formatting."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# 8 cardinal + intercardinal directions StepGame uses, longest first to avoid
# "left" matching inside "upper-left" during substring scans.
DIRECTIONS = ("upper-left", "upper-right", "lower-left", "lower-right", "left", "right", "above", "below")

SYSTEM_PROMPT = (
    "You are a spatial reasoning assistant. "
    "Given a sequence of positional relationships between objects, "
    "determine the spatial relationship between two specified objects. "
    "Think step by step, then answer with a single direction from: "
    "left, right, above, below, upper-left, upper-right, lower-left, lower-right."
)


def load_stepgame(split_path: str | Path) -> list[dict[str, Any]]:
    """Load a StepGame JSON split file."""
    with open(split_path) as f:
        data = json.load(f)
    return data


def format_prompt(story: str, question: str) -> str:
    """Format a StepGame example as a chat prompt."""
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{story}\n\n{question}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def format_for_training(example: dict[str, Any]) -> dict[str, str]:
    """Convert a raw StepGame example to prompt/completion pair."""
    story = example["story"]
    question = example["question"]
    answer = example["answer"]
    prompt = format_prompt(story, question)
    return {"prompt": prompt, "completion": answer, "full_text": prompt + answer + "<|im_end|>"}


def extract_answer(text: str) -> str | None:
    """Extract the direction answer from model output.

    Strips <think>...</think> blocks emitted by the Thinking model before scanning.
    """
    text = text.strip().lower()
    # Strip thinking block emitted by LFM2.5-1.2B-Thinking
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text in DIRECTIONS:
        return text
    # Match at end of output (DIRECTIONS already longest-first)
    for d in DIRECTIONS:
        if text.endswith(d):
            return d
    # Find last occurrence by end position. Using end position (idx + len(d))
    # means "upper-left" and "left" tie when "left" is a suffix of "upper-left"
    # at the same location; length then breaks the tie in favour of the longer
    # match (DIRECTIONS is longest-first, so the first candidate wins ties).
    best_end, best_len, best = -1, 0, None
    for d in DIRECTIONS:
        idx = text.rfind(d)
        if idx < 0:
            continue
        end = idx + len(d)
        if end > best_end or (end == best_end and len(d) > best_len):
            best_end, best_len, best = end, len(d), d
    return best
