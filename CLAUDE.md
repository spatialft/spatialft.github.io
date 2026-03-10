# CLAUDE.md — spatialft.github.io

AIPI 590.03 Intelligent Agents — Project 1: fine-tune **LiquidAI/LFM2.5-1.2B-Thinking** to improve spatial reasoning, measure baseline accuracy, then re-evaluate to show improvement.

## Project structure

```
data/
  raw/          StepGame splits (gitignored)
  processed/    prompt/completion pairs (gitignored)
  eval/         held-out evaluation set (gitignored)
notebooks/
  01_baseline_eval.ipynb
  02_dataset_prep.ipynb
  03_finetune.ipynb
  04_eval_comparison.ipynb
src/
  dataset.py    StepGame loading + prompt formatting
  eval.py       accuracy evaluation logic
  metrics.py    per-hop-level breakdown
results/
  baseline/     baseline predictions + scores
  finetuned/    post-fine-tune predictions + scores (checkpoint gitignored)
docs/
  checklist/    auto-generated from REQUIREMENTS_CHECKLIST.md
scripts/
  generate_checklist.py
```

## Deploy

GitHub Pages serves from the `gh-pages` branch root.

`make checklist` regenerates `docs/checklist/index.html` locally.
`make deploy-checklist` pushes it to `gh-pages` manually (CI handles this on push to `main`).

CI workflow: `.github/workflows/checklist.yml` — triggers on changes to `REQUIREMENTS_CHECKLIST.md` or `scripts/generate_checklist.py`.

## Checklist

Requirements tracked in `REQUIREMENTS_CHECKLIST.md`. Mark items `[x]` as they complete. The checklist page at `/checklist/` updates automatically on push to `main`.
