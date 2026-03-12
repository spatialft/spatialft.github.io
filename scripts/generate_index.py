"""Generate docs/index.html from results/baseline/scores.json,
results/finetuned/scores.json, and results/examples.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
BASELINE_SCORES = ROOT / "results" / "baseline" / "scores.json"
FINETUNED_SCORES = ROOT / "results" / "finetuned" / "scores.json"
EXAMPLES_PATH = ROOT / "results" / "examples.json"
OUT = ROOT / "docs" / "index.html"


def load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def render(baseline: dict | None, finetuned: dict | None, examples: list | None) -> str:
    has_baseline = baseline is not None
    has_scores = has_baseline and finetuned is not None
    has_examples = examples is not None and len(examples) > 0

    # Build chart data
    if has_baseline:
        k_keys = sorted(
            {k for k in baseline.keys() if k.startswith("accuracy_k")},
            key=lambda x: int(x.replace("accuracy_k", "")),
        )
        if has_scores:
            k_keys = sorted(
                {k for k in list(baseline.keys()) + list(finetuned.keys()) if k.startswith("accuracy_k")},
                key=lambda x: int(x.replace("accuracy_k", "")),
            )
        k_labels = [k.replace("accuracy_", "") for k in k_keys]
        base_k = [round(baseline.get(k, 0) * 100, 1) for k in k_keys]
        ft_k = [round(finetuned.get(k, 0) * 100, 1) for k in k_keys] if has_scores else []
        base_overall = round(baseline["accuracy"] * 100, 1)
        ft_overall = round(finetuned["accuracy"] * 100, 1) if has_scores else None
        if has_scores:
            delta = round(ft_overall - base_overall, 1)
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
        else:
            delta = delta_str = None
    else:
        k_labels = base_k = ft_k = []
        base_overall = ft_overall = delta_str = delta = None

    chart_data = json.dumps({
        "kLabels": k_labels,
        "baseK": base_k,
        "ftK": ft_k,
        "hasFinetune": has_scores,
    })

    # No server-side HTML escaping needed — all user-controlled fields are
    # inserted via textContent in the client JS, not innerHTML.
    examples_json = json.dumps(examples or [])

    scores_section = ""
    if has_scores:
        scores_section = f"""
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
          <div class="score-label">Improvement</div>
          <div class="score-value {'positive' if delta >= 0 else 'negative'}">{delta_str}%</div>
        </div>
      </div>
      <div class="chart-wrap">
        <canvas id="hopChart"></canvas>
      </div>
    </section>
"""
    elif has_baseline:
        scores_section = f"""
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
      <div class="chart-wrap">
        <canvas id="hopChart"></canvas>
      </div>
      <p class="pending-note">Fine-tuning in progress — run notebooks 03 and 04 in Colab.</p>
    </section>
"""
    else:
        scores_section = """
    <section class="scores pending">
      <div class="pending-msg">
        <span class="pending-icon">⏳</span>
        <p>Evaluation results pending — run notebooks 01 and 04 in Colab.</p>
        <a href="/checklist/" class="btn">View checklist</a>
      </div>
    </section>
"""

    examples_section = ""
    if has_examples:
        examples_section = """
    <section class="examples">
      <h2>Model Predictions</h2>
      <p class="subtitle">Cases where fine-tuning corrected the model's spatial reasoning.</p>
      <div class="example-grid" id="exampleGrid"></div>
    </section>
"""
    elif has_baseline:
        examples_section = """
    <section class="examples pending">
      <h2>Model Predictions</h2>
      <div class="pending-msg">
        <span class="pending-icon">⏳</span>
        <p>Example predictions pending — run notebook 04 in Colab.</p>
      </div>
    </section>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SpatialFT — AIPI 590.03</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #f8f9fa;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #1a202c;
      --muted: #64748b;
      --accent: #2563eb;
      --green: #16a34a;
      --red: #dc2626;
      --radius: 10px;
      --shadow: 0 1px 4px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.04);
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}

    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 2.5rem 2rem 2rem;
      text-align: center;
    }}

    header .eyebrow {{
      font-size: .8rem;
      font-weight: 600;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: .5rem;
    }}

    header h1 {{
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -.02em;
    }}

    header p {{
      color: var(--muted);
      margin-top: .4rem;
      font-size: .95rem;
    }}

    header nav {{
      margin-top: 1.25rem;
      display: flex;
      gap: .75rem;
      justify-content: center;
      flex-wrap: wrap;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      padding: .4rem .9rem;
      border-radius: 6px;
      font-size: .85rem;
      font-weight: 500;
      text-decoration: none;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      transition: border-color .15s, background .15s;
    }}

    .btn:hover {{ background: var(--bg); border-color: #94a3b8; }}
    .btn.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    .btn.primary:hover {{ background: #1d4ed8; border-color: #1d4ed8; }}

    main {{ max-width: 900px; margin: 2.5rem auto; padding: 0 1.5rem 4rem; }}

    section {{ margin-bottom: 2.5rem; }}

    h2 {{
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: .25rem;
    }}

    .subtitle {{ color: var(--muted); font-size: .9rem; margin-bottom: 1.25rem; }}

    /* Score cards */
    .score-cards {{
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 1.75rem;
    }}

    .score-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem 1.5rem;
      text-align: center;
      box-shadow: var(--shadow);
      min-width: 130px;
    }}

    .score-card.delta {{ border-color: var(--border); }}

    .score-label {{
      font-size: .75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--muted);
      margin-bottom: .3rem;
    }}

    .score-value {{
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -.03em;
    }}

    .score-value.muted {{ color: var(--muted); }}
    .score-value.accent {{ color: var(--accent); }}
    .score-value.positive {{ color: var(--green); }}
    .score-value.negative {{ color: var(--red); }}

    .score-arrow {{
      font-size: 1.5rem;
      color: var(--muted);
      flex-shrink: 0;
    }}

    /* Chart */
    .chart-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem;
      box-shadow: var(--shadow);
    }}

    /* Pending state */
    .pending-msg {{
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: var(--radius);
      padding: 2.5rem;
      text-align: center;
      color: var(--muted);
    }}

    .pending-icon {{ font-size: 1.75rem; display: block; margin-bottom: .5rem; }}
    .pending-msg p {{ margin-bottom: 1rem; }}
    .pending-note {{ color: var(--muted); font-size: .85rem; margin-top: .75rem; }}
    .pending-arrow {{ opacity: .4; }}

    /* Example cards */
    .example-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 1rem;
    }}

    .example-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.1rem 1.25rem;
      box-shadow: var(--shadow);
      font-size: .875rem;
    }}

    .example-card .k-badge {{
      display: inline-block;
      font-size: .7rem;
      font-weight: 600;
      background: #eff6ff;
      color: var(--accent);
      border-radius: 4px;
      padding: .15rem .45rem;
      margin-bottom: .6rem;
      letter-spacing: .04em;
    }}

    .example-card .story {{
      color: var(--muted);
      font-size: .8rem;
      margin-bottom: .5rem;
      line-height: 1.5;
    }}

    .example-card .question {{
      font-weight: 600;
      margin-bottom: .75rem;
    }}

    .predictions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: .5rem;
    }}

    .pred-box {{
      border-radius: 6px;
      padding: .5rem .75rem;
      font-size: .8rem;
    }}

    .pred-box .pred-label {{
      font-size: .7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .05em;
      margin-bottom: .2rem;
    }}

    .pred-box .pred-value {{
      font-weight: 700;
      font-size: .95rem;
    }}

    .pred-box.wrong {{ background: #fef2f2; border: 1px solid #fecaca; color: var(--red); }}
    .pred-box.right {{ background: #f0fdf4; border: 1px solid #bbf7d0; color: var(--green); }}

    .answer-row {{
      font-size: .75rem;
      color: var(--muted);
      margin-top: .6rem;
    }}

    footer {{
      text-align: center;
      color: var(--muted);
      font-size: .8rem;
      padding: 2rem;
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">AIPI 590.03 · Intelligent Agents · Project 1</div>
    <h1>Spatial Reasoning Fine-Tuning</h1>
    <p>Fine-tuning LFM2-350M on StepGame to improve spatial reasoning accuracy.</p>
    <nav>
      <a class="btn primary" href="/checklist/">Requirements Checklist</a>
      <a class="btn" href="https://colab.research.google.com/github/spatialft/spatialft.github.io/blob/main/notebooks/01_baseline_eval.ipynb" target="_blank" rel="noopener noreferrer">01 Baseline Eval</a>
      <a class="btn" href="https://colab.research.google.com/github/spatialft/spatialft.github.io/blob/main/notebooks/02_dataset_prep.ipynb" target="_blank" rel="noopener noreferrer">02 Dataset Prep</a>
      <a class="btn" href="https://colab.research.google.com/github/spatialft/spatialft.github.io/blob/main/notebooks/03_finetune.ipynb" target="_blank" rel="noopener noreferrer">03 Fine-Tune</a>
      <a class="btn" href="https://colab.research.google.com/github/spatialft/spatialft.github.io/blob/main/notebooks/04_eval_comparison.ipynb" target="_blank" rel="noopener noreferrer">04 Comparison</a>
    </nav>
  </header>

  <main>
    {scores_section}
    {examples_section}
  </main>

  <footer>
    SpatialFT · Duke University · AIPI 590.03 Intelligent Agents
  </footer>

  <script>
    const chartData = {chart_data};
    const examples = {examples_json};

    // Render hop chart
    if (chartData.kLabels.length > 0) {{
      const ctx = document.getElementById('hopChart').getContext('2d');
      const datasets = [{{
        label: 'Baseline',
        data: chartData.baseK,
        backgroundColor: '#94a3b8',
        borderRadius: 4,
      }}];
      if (chartData.hasFinetune) {{
        datasets.push({{
          label: 'Fine-tuned',
          data: chartData.ftK,
          backgroundColor: '#2563eb',
          borderRadius: 4,
        }});
      }}
      new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: chartData.kLabels,
          datasets,
        }},
        options: {{
          responsive: true,
          plugins: {{
            legend: {{ position: 'top' }},
            title: {{
              display: true,
              text: 'Accuracy by Hop Level (k)',
              font: {{ size: 13, weight: '600' }},
              color: '#1a202c',
            }},
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              max: 100,
              ticks: {{ callback: v => v + '%' }},
              grid: {{ color: '#f1f5f9' }},
            }},
            x: {{ grid: {{ display: false }} }},
          }},
        }},
      }});
    }}

    // Render example cards — use textContent for all user-controlled fields
    // to avoid template-literal injection (backticks / ${{}} in model output).
    const grid = document.getElementById('exampleGrid');
    if (grid && examples.length > 0) {{
      examples.forEach(ex => {{
        const card = document.createElement('div');
        card.className = 'example-card';

        const badge = document.createElement('span');
        badge.className = 'k-badge';
        badge.textContent = `k=${{ex.k}} hop${{ex.k !== 1 ? 's' : ''}}`;
        card.appendChild(badge);

        const story = document.createElement('div');
        story.className = 'story';
        story.textContent = ex.story;
        card.appendChild(story);

        const question = document.createElement('div');
        question.className = 'question';
        question.textContent = ex.question;
        card.appendChild(question);

        const preds = document.createElement('div');
        preds.className = 'predictions';
        [['Baseline', ex.baseline], ['Fine-tuned', ex.finetuned]].forEach(([label, pred]) => {{
          const box = document.createElement('div');
          box.className = 'pred-box ' + (pred === ex.answer ? 'right' : 'wrong');
          const lbl = document.createElement('div');
          lbl.className = 'pred-label';
          lbl.textContent = label;
          const val = document.createElement('div');
          val.className = 'pred-value';
          val.textContent = pred;
          box.appendChild(lbl);
          box.appendChild(val);
          preds.appendChild(box);
        }});
        card.appendChild(preds);

        const answerRow = document.createElement('div');
        answerRow.className = 'answer-row';
        answerRow.textContent = 'Ground truth: ';
        const strong = document.createElement('strong');
        strong.textContent = ex.answer;
        answerRow.appendChild(strong);
        card.appendChild(answerRow);

        grid.appendChild(card);
      }});
    }}
  </script>
</body>
</html>
"""


def main():
    baseline = load_json(BASELINE_SCORES)
    finetuned = load_json(FINETUNED_SCORES)
    examples = load_json(EXAMPLES_PATH)

    output = render(baseline, finetuned, examples)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(output)
    print(f"Generated {OUT}")


if __name__ == "__main__":
    main()
