# Project Plan

> Phase checklists below are planning notes — they are not connected to
> `REQUIREMENTS_CHECKLIST.md` and are not auto-tracked by CI.

## Overview

Fine-tune **LiquidAI/LFM2-350M** on spatial reasoning, measure improvement on
StepGame, and present findings in a 10-minute live presentation.

## Files in this directory

| File | Purpose |
|------|---------|
| `plan.md` | This file — master checklist and decisions |
| `recommendations.md` | Technical decisions, risks, and alternatives |

---

## Phase 1 — Setup (do this first)

- [x] Verify `LiquidAI/LFM2-350M` exists on HuggingFace
- [x] Dataset: `ZhengyanShi/StepGame` on HuggingFace (confirmed working)
- [x] Open a free Colab notebook, confirm T4 GPU is available
- [x] Run `pip install -r requirements.txt` and confirm no conflicts
- [x] Confirm the training path supports `LiquidAI/LFM2-350M`
      - Using `transformers` + `peft` path

## Phase 2 — Baseline evaluation

- [x] Run `notebooks/01_baseline_eval.ipynb` end to end
- [x] Save `results/baseline/scores.json`
- [x] Note overall accuracy and per-hop accuracy for k=1 through k=5
- [x] Spot-check predictions — understand failure modes

## Phase 3 — Dataset preparation

- [x] Run `notebooks/02_dataset_prep.ipynb`
- [x] Confirm 10,000 training / 250 eval examples (stratified across k=1–5) loaded correctly
- [x] Inspect formatted prompts — ensure they match the model's expected chat template

## Phase 4 — Fine-tuning

- [x] Run `notebooks/03_finetune.ipynb`
- [x] Monitor training loss — decreased steadily over 3 epochs
- [x] Save LoRA adapter to `results/finetuned/lora_adapter/`

## Phase 5 — Evaluation and comparison

- [x] Run `notebooks/04_eval_comparison.ipynb`
- [x] Save `results/finetuned/scores.json`
- [x] Verify results page at spatialft.github.io shows before/after chart
- [x] Document delta in `README.md` results table

## Phase 6 — Presentation

- [ ] Deliver 10-minute live presentation
- [ ] Submit Canvas link + repo link

---

## Key decisions made

| Decision | Choice | Reason |
|----------|--------|--------|
| Property | Spatial reasoning | Measurable, well-benchmarked, clear difficulty gradient |
| Model | LFM2-350M | Fastest model in the project setup, cheap to iterate, edge-friendly |
| Dataset | StepGame | Multi-hop structure gives clear difficulty gradient |
| Fine-tuning | LoRA via PEFT | Memory efficient and architecture-agnostic |
| Evaluation metric | Accuracy per hop level k | Reveals where improvement occurs |
