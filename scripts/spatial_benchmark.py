"""
Spatial benchmark runner for spatialft.github.io.

Evaluates LM-Arena-hosted models on the StepGame held-out eval set (250 examples,
k=1–5), computing overall + per-hop accuracy and latency.

Modes:
  --list-models          Print JSON array of online model IDs and exit
  --model <id>           Benchmark a single model; write to /tmp/spatial-bench-result.json
  --merge <dir>          Merge per-model result files into the dated JSON + index
  --quality-gate <file>  Exit 1 if no model scored above random (1/8 ≈ 12.5%)
  (no args)              Sequential: benchmark all online models (local dev)

Writes results to:
  results/live/YYYY-MM-DD.json   full run (one key per model)
  results/live/index.json        list of available run dates, newest first
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

# Add repo root so we can import src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset import SYSTEM_PROMPT, extract_answer
from src.eval import evaluate

REGISTRY    = os.environ.get("REGISTRY", "https://tunnel-registry.jonasneves.workers.dev")
TIMEOUT     = 90            # seconds per prompt — spatial tasks can be slower than MMLU
MAX_TOKENS  = 64
EVAL_PATH   = Path(__file__).parent.parent / "data" / "eval" / "stepgame_eval.json"
OUT_DIR     = Path(__file__).parent.parent / "results" / "live"
RESULT_FILE = Path("/tmp/spatial-bench-result.json")

RANDOM_ACCURACY = 1 / 8     # 8-class classification random baseline


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def get_online_models() -> list[str]:
    try:
        res = requests.get(f"{REGISTRY}/v1/models", timeout=10)
        res.raise_for_status()
        return [m["id"] for m in res.json().get("data", [])]
    except Exception as e:
        print(f"Failed to fetch models: {e}")
        return []


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def run_prompt(model_id: str, story: str, question: str) -> dict:
    """
    Send a single StepGame prompt as a chat request (streaming SSE).
    Returns: text, latency_ms, tps, error.
    """
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"{story}\n\n{question}"},
        ],
        "max_tokens": MAX_TOKENS,
        "stream": True,
    }
    t0 = time.monotonic()
    try:
        res = requests.post(
            f"{REGISTRY}/v1/chat/completions",
            json=payload,
            timeout=TIMEOUT,
            stream=True,
        )
        res.raise_for_status()

        text = ""
        completion_chunks = 0
        usage_tokens = None

        for raw in res.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"].get("content") or ""
                if delta:
                    text += delta
                    completion_chunks += 1
                if chunk.get("usage") and chunk["usage"].get("completion_tokens"):
                    usage_tokens = chunk["usage"]["completion_tokens"]
            except Exception:
                pass

        latency_ms = (time.monotonic() - t0) * 1000
        count = usage_tokens if usage_tokens is not None else completion_chunks
        tps = count / (latency_ms / 1000) if latency_ms > 0 and count else 0
        return {"text": text.strip(), "latency_ms": latency_ms, "tps": tps, "error": None}

    except requests.exceptions.Timeout:
        latency_ms = (time.monotonic() - t0) * 1000
        return {"text": None, "latency_ms": latency_ms, "tps": 0, "error": "timeout"}
    except Exception as e:
        latency_ms = (time.monotonic() - t0) * 1000
        return {"text": None, "latency_ms": latency_ms, "tps": 0, "error": str(e)}


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark_model(model_id: str) -> dict:
    print(f"\n=== {model_id} ===")
    examples = json.loads(EVAL_PATH.read_text())

    predictions = []
    latencies: list[float] = []
    tps_values: list[float] = []

    for i, ex in enumerate(examples):
        result = run_prompt(model_id, ex["story"], ex["question"])
        text = result["text"] or ""
        pred = extract_answer(text) or ""
        gold = ex["answer"]

        predictions.append({"answer": gold, "prediction": text, "k": ex["k"]})

        if result["latency_ms"]:
            latencies.append(result["latency_ms"])
        if result["tps"] > 0:
            tps_values.append(result["tps"])

        hit = "✓" if pred == gold else "✗"
        print(f"  [{i+1:3d}/{len(examples)}] k={ex['k']} {result['latency_ms']:.0f}ms  "
              f"pred={pred!r} gold={gold!r} {hit}")

    scores = evaluate(predictions)

    return {
        "model":           model_id,
        "date":            date.today().isoformat(),
        "run_at":          datetime.now(timezone.utc).isoformat(),
        "total":           len(examples),
        "accuracy":        scores["accuracy"],
        **{k: v for k, v in scores.items() if k.startswith("accuracy_k")},
        "p50_latency_ms":  round(statistics.median(latencies), 1) if latencies else None,
        "avg_latency_ms":  round(statistics.mean(latencies), 1)   if latencies else None,
        "avg_tps":         round(statistics.mean(tps_values), 1)  if tps_values else None,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_results(today: str, all_results: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    run_file = OUT_DIR / f"{today}.json"
    existing: dict = {}
    if run_file.exists():
        try:
            existing = json.loads(run_file.read_text())
        except Exception:
            pass
    existing.update(all_results)
    run_file.write_text(json.dumps(existing, indent=2))
    print(f"\nResults written to {run_file} ({len(existing)} models)")

    index_file = OUT_DIR / "index.json"
    runs: list[str] = []
    if index_file.exists():
        try:
            runs = json.loads(index_file.read_text())
        except Exception:
            pass
    if today not in runs:
        runs.insert(0, today)
    index_file.write_text(json.dumps(runs, indent=2))
    print(f"Index updated: {runs[:5]}{'...' if len(runs) > 5 else ''}")


# ---------------------------------------------------------------------------
# CLI modes
# ---------------------------------------------------------------------------

def cmd_list_models() -> None:
    print(json.dumps(get_online_models()))


def cmd_single(model_id: str) -> None:
    metrics = benchmark_model(model_id)
    RESULT_FILE.write_text(json.dumps({"model_id": model_id, "metrics": metrics}))
    print(f"Result written to {RESULT_FILE}")


def cmd_merge(results_dir: str) -> None:
    today = date.today().isoformat()
    all_results: dict = {}
    for f in sorted(Path(results_dir).glob("*/spatial-bench-result.json")):
        data = json.loads(f.read_text())
        all_results[data["model_id"]] = data["metrics"]
        print(f"  merged: {data['model_id']}")
    if not all_results:
        print("No results to merge — exiting.")
        return
    write_results(today, all_results)


def cmd_quality_gate(results_file: str) -> None:
    data = json.loads(Path(results_file).read_text())
    total = len(data)
    above = [m for m, v in data.items() if v.get("accuracy", 0) > RANDOM_ACCURACY]
    below = [m for m in data if m not in above]

    print(f"Quality gate: {len(above)}/{total} models above random baseline ({RANDOM_ACCURACY:.1%})")
    if below:
        print(f"  at/below random: {', '.join(below)}")

    if not above:
        print("FAILED — no models scored above random. Check connectivity or prompt format.")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as f:
                f.write("## ⚠️ Quality gate failed\n")
                f.write(f"0/{total} models scored above random ({RANDOM_ACCURACY:.1%}) on StepGame.\n")
                f.write(f"Models: {', '.join(below)}\n")
        raise SystemExit(1)


def cmd_all() -> None:
    models = get_online_models()
    if not models:
        print("No models online — exiting.")
        return
    print(f"Online models: {models}")
    today = date.today().isoformat()
    all_results: dict = {}
    for model_id in models:
        all_results[model_id] = benchmark_model(model_id)
    write_results(today, all_results)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-models",  action="store_true", help="Print JSON array of online model IDs")
    parser.add_argument("--model",        metavar="ID",   help="Benchmark a single model")
    parser.add_argument("--merge",        metavar="DIR",  help="Merge per-model result files")
    parser.add_argument("--quality-gate", metavar="FILE", help="Exit 1 if no models above random baseline")
    args = parser.parse_args()

    if args.list_models:
        cmd_list_models()
    elif args.model:
        cmd_single(args.model)
    elif args.merge:
        cmd_merge(args.merge)
    elif args.quality_gate:
        cmd_quality_gate(args.quality_gate)
    else:
        cmd_all()


if __name__ == "__main__":
    main()
