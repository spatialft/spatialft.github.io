"""Generate docs/index.html from results and static templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared import load_json, render_template

ROOT = Path(__file__).parent.parent
BASELINE_SCORES = ROOT / "results" / "baseline" / "scores.json"
FINETUNED_SCORES = ROOT / "results" / "finetuned" / "scores.json"
TRAINING_STATS = ROOT / "results" / "finetuned" / "training_stats.json"
EXAMPLES_PATH = ROOT / "results" / "examples.json"
TEMPLATE = ROOT / "scripts" / "templates" / "index.html"
OUT = ROOT / "docs" / "index.html"


def pct_interval_text(value: float, total: int) -> str:
    if total <= 0:
        return "n/a"
    se = (value * (1 - value) / total) ** 0.5
    low = max(0.0, value - 1.96 * se)
    high = min(1.0, value + 1.96 * se)
    return f"{low * 100:.1f}%-{high * 100:.1f}%"


def render_scores_section(baseline: dict | None, finetuned: dict | None) -> str:
    if baseline is None:
        return """
    <section class="scores pending">
      <div class="pending-msg">
        <span class="pending-icon">⏳</span>
        <p>Evaluation results pending. Run notebooks 01 and 04 in Colab.</p>
        <a href="/checklist/" class="btn">View checklist</a>
      </div>
    </section>
"""

    base_overall = round(baseline["accuracy"] * 100, 1)
    if finetuned is None:
        return f"""
    <section class="scores">
      <div class="score-cards">
        <div class="score-card">
          <div class="score-label">Baseline</div>
          <div class="score-value muted">{base_overall}%</div>
        </div>
        <div class="score-arrow pending-arrow">→</div>
        <div class="score-card pending-card">
          <div class="score-label">Fine-tuned</div>
          <div class="score-value muted">—</div>
        </div>
      </div>
      <p class="pending-note">Fine-tuning in progress. Run notebooks 03 and 04 in Colab.</p>
    </section>
"""

    total = baseline.get("total", finetuned.get("total", 0))
    ft_overall = round(finetuned["accuracy"] * 100, 1)
    delta = round(ft_overall - base_overall, 1)
    delta_str = f"+{delta}" if delta >= 0 else str(delta)
    delta_class = "positive" if delta > 0 else "negative" if delta < 0 else "muted"
    baseline_ci = pct_interval_text(baseline["accuracy"], total)
    finetuned_ci = pct_interval_text(finetuned["accuracy"], total)

    return f"""
    <section class="scores">
      <div class="score-cards">
        <div class="score-card">
          <div class="score-label">Baseline</div>
          <div class="score-value muted">{base_overall}%</div>
        </div>
        <div class="score-arrow">→</div>
        <div class="score-card">
          <div class="score-label">Fine-tuned</div>
          <div class="score-value accent">{ft_overall}%</div>
        </div>
        <div class="score-card delta">
          <div class="score-label">Change</div>
          <div class="score-value {delta_class}">{delta_str}%</div>
        </div>
      </div>
      <p class="pending-note">
        Accuracy on {total} held-out examples (50 per hop level, k=1-5). Approx. 95% intervals:
        baseline {baseline_ci}, fine-tuned {finetuned_ci}. Treat the {delta_str}% overall change as exploratory.
        Per-hop intervals are wide (n=50 each), so individual hop deltas are directional, not conclusive.
      </p>
      <div class="chart-wrap">
        <img
          class="comparison-chart"
          src="./assets/comparison.png"
          alt="Baseline and fine-tuned accuracy by hop level"
        />
      </div>
    </section>
"""


def render_training_section(finetuned: dict | None, training_stats: dict | None) -> str:
    if finetuned is None:
        return ""

    stats = training_stats or {}
    time_str = f'{stats["training_time_min"]:.1f} min' if "training_time_min" in stats else "—"
    loss_str = f'~{stats["final_loss"]:.3f}' if "final_loss" in stats else "—"
    size_str = f'{stats["adapter_size_mb"]:.1f} MB' if "adapter_size_mb" in stats else "—"

    return f"""
    <section class="training">
      <h2>Training Details</h2>
      <p class="subtitle">Loss decreased steadily over 3 epochs, so optimization was stable. That stability did not translate into a strong overall evaluation gain.</p>
      <div class="chart-wrap training-wrap">
        <img
          class="training-chart"
          src="./assets/loss-curve.png"
          alt="Training loss curve during LoRA fine-tuning"
        />
      </div>
      <div class="training-stats">
        <div class="training-stat">
          <div class="score-label">Training Time</div>
          <div class="training-value">{time_str}</div>
        </div>
        <div class="training-stat">
          <div class="score-label">Final Loss</div>
          <div class="training-value">{loss_str}</div>
        </div>
        <div class="training-stat">
          <div class="score-label">Adapter Size</div>
          <div class="training-value">{size_str}</div>
        </div>
      </div>
    </section>
"""


def render_examples_section(examples: list[dict[str, Any]] | None, has_baseline: bool) -> str:
    if examples:
        outcomes = {example.get("outcome") for example in examples}
        if outcomes == {"improvement"} or outcomes == {None}:
            subtitle = (
                "Illustrative cases where the fine-tuned adapter corrected a baseline mistake. "
                "These are curated wins, not a representative sample."
            )
        else:
            subtitle = (
                "Illustrative evaluation examples spanning improvement, regression, stable-correct, "
                "and stable-wrong outcomes."
            )
        return """
    <section class="examples">
      <h2>Model Predictions</h2>
      <p class="subtitle">__EXAMPLES_SUBTITLE__</p>
      <div class="example-grid" id="exampleGrid"></div>
    </section>
""".replace("__EXAMPLES_SUBTITLE__", subtitle)
    if has_baseline:
        return """
    <section class="examples pending">
      <h2>Model Predictions</h2>
      <div class="pending-msg">
        <span class="pending-icon">⏳</span>
        <p>Example predictions pending. Run notebook 04 in Colab.</p>
      </div>
    </section>
"""
    return ""


def render(
    baseline: dict | None,
    finetuned: dict | None,
    examples: list[Any] | None,
    training_stats: dict | None = None,
) -> str:
    has_baseline = baseline is not None
    examples_json = json.dumps(examples or [])
    template = TEMPLATE.read_text()

    return render_template(
        template,
        {
            "__SCORES_SECTION__": render_scores_section(baseline, finetuned),
            "__TRAINING_SECTION__": render_training_section(finetuned, training_stats),
            "__EXAMPLES_SECTION__": render_examples_section(examples, has_baseline),
            "__EXAMPLES_JSON__": examples_json,
        },
    )


def main() -> None:
    baseline = load_json(BASELINE_SCORES)
    finetuned = load_json(FINETUNED_SCORES)
    training_stats = load_json(TRAINING_STATS)
    examples = load_json(EXAMPLES_PATH)
    output = render(baseline, finetuned, examples, training_stats)
    OUT.write_text(output)
    print(f"Written {OUT}")


if __name__ == "__main__":
    main()
