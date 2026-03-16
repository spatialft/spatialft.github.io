"""Generate docs/benchmark.html from live benchmark results."""

from __future__ import annotations

import json
from pathlib import Path

from shared import load_json, render_template

ROOT            = Path(__file__).parent.parent
LIVE_INDEX      = ROOT / "results" / "live" / "index.json"
LIVE_DIR        = ROOT / "results" / "live"
BASELINE_SCORES = ROOT / "results" / "baseline" / "scores.json"
FINETUNED_SCORES= ROOT / "results" / "finetuned" / "scores.json"
TEMPLATE        = ROOT / "scripts" / "templates" / "benchmark.html"
OUT             = ROOT / "docs" / "benchmark.html"


def load_latest_live() -> tuple[dict | None, str | None]:
    index = load_json(LIVE_INDEX)
    if not index:
        return None, None
    latest_date = index[0]
    data = load_json(LIVE_DIR / f"{latest_date}.json")
    return data, latest_date


def main() -> None:
    live_data, run_date = load_latest_live()
    baseline  = load_json(BASELINE_SCORES)
    finetuned = load_json(FINETUNED_SCORES)

    reference = {}
    if baseline:
        reference["baseline"] = baseline
    if finetuned:
        reference["finetuned"] = finetuned

    output = render_template(
        TEMPLATE.read_text(),
        {
            "__LIVE_DATA_JSON__":  json.dumps(live_data or {}),
            "__REFERENCE_JSON__":  json.dumps(reference),
            "__RUN_DATE__":        run_date or "",
            "__MODEL_COUNT__":     str(len(live_data) if live_data else 0),
        },
    )
    OUT.write_text(output)
    print(f"Written {OUT}")


if __name__ == "__main__":
    main()
