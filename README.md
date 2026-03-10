# AIPI 590.03 Intelligent Agents — Project 1: Spatial Reasoning Fine-Tuning

[![Generate Checklist](https://github.com/spatialft/spatialft.github.io/actions/workflows/checklist.yml/badge.svg)](https://github.com/spatialft/spatialft.github.io/actions/workflows/checklist.yml)
[![Checklist](https://img.shields.io/badge/requirements-checklist-blue)](https://spatialft.github.io/checklist/)

Fine-tune **LiquidAI/LFM2.5-1.2B-Thinking** to improve spatial reasoning, measure baseline performance, then re-evaluate to show improvement.

## Property: Spatial Reasoning

Small models struggle to reliably track multi-hop directional relationships ("A is left of B, B is above C — where is A relative to C?"). This project measures that capability, fine-tunes on chain-of-thought spatial data, and re-evaluates.

## Dataset

[StepGame](https://github.com/ZhengxiangShi/StepGame) — multi-step spatial QA with k-hop difficulty levels (k=1..10).

## Model

`LiquidAI/LFM2.5-1.2B-Thinking` via [Unsloth](https://github.com/unslothAI/unsloth) for efficient LoRA fine-tuning on a single T4 GPU.

## Project structure

```
data/
  raw/          downloaded StepGame splits
  processed/    formatted prompt/completion pairs
  eval/         held-out evaluation set
notebooks/
  01_baseline_eval.ipynb    measure baseline accuracy
  02_dataset_prep.ipynb     prepare fine-tuning data
  03_finetune.ipynb         LoRA fine-tuning with Unsloth
  04_eval_comparison.ipynb  compare before vs after
src/
  dataset.py    StepGame loading + prompt formatting
  eval.py       accuracy evaluation logic
  metrics.py    per-hop-level breakdown
results/
  baseline/     baseline predictions + scores
  finetuned/    post-fine-tune predictions + scores
```

## Quickstart (Colab T4)

```bash
pip install -r requirements.txt
# then open notebooks in order
```

## Results

| Split | Baseline | Fine-tuned |
|-------|----------|------------|
| k=1   | —        | —          |
| k=3   | —        | —          |
| k=5   | —        | —          |
| k=10  | —        | —          |
| **avg** | —      | —          |

## Team

Jonas Neves · Daniel Ros · Keming Zhou
