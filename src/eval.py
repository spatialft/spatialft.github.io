"""Evaluation logic for spatial reasoning accuracy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.dataset import extract_answer


def evaluate(predictions: list[dict[str, Any]]) -> dict[str, float]:
    """
    Compute accuracy from a list of prediction dicts.

    Each dict must have: 'answer' (ground truth) and 'prediction' (raw model output).
    Returns overall accuracy plus per-hop-level breakdown if 'k' is present.
    """
    correct = 0
    total = 0
    by_k: dict[int, list[bool]] = {}

    for p in predictions:
        gold = p["answer"].strip().lower()
        pred = extract_answer(p["prediction"]) or ""
        hit = pred == gold
        correct += hit
        total += 1
        if "k" in p:
            by_k.setdefault(p["k"], []).append(hit)

    results: dict[str, float] = {"accuracy": correct / total if total else 0.0, "total": total}
    for k, hits in sorted(by_k.items()):
        results[f"accuracy_k{k}"] = sum(hits) / len(hits)

    return results


def save_results(results: dict[str, float], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {path}")


def load_predictions(path: str | Path) -> list[dict[str, Any]]:
    with open(path) as f:
        return json.load(f)
