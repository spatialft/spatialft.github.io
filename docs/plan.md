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
| `slides.md` | Slide-by-slide content |
| `speaker-notes.md` | Speaker notes for each slide |
| `recommendations.md` | Technical decisions, risks, and alternatives |

---

## Phase 1 — Setup (do this first)

- [ ] Verify `LiquidAI/LFM2-350M` exists on HuggingFace
      - If unavailable, use `LiquidAI/LFM2-700M` and note it in the presentation
      - Check: https://huggingface.co/LiquidAI
- [ ] Dataset: `ZhengyanShi/StepGame` on HuggingFace (confirmed working)
- [ ] Open a free Colab notebook, confirm T4 GPU is available
- [ ] Run `pip install -r requirements.txt` and confirm no conflicts
- [ ] Confirm the training path supports `LiquidAI/LFM2-350M`
      - Prefer the existing `transformers` + `peft` notebook path
      - If an accelerated path works, treat it as optional rather than required

## Phase 2 — Baseline evaluation

- [ ] Run `notebooks/01_baseline_eval.ipynb` end to end
- [ ] Save `results/baseline/scores.json`
- [ ] Note overall accuracy and per-hop accuracy for k=1 through k=5
- [ ] Spot-check 10 predictions manually — understand failure modes

## Phase 3 — Dataset preparation

- [ ] Run `notebooks/02_dataset_prep.ipynb`
- [ ] Confirm 4000 training / 250 eval examples (stratified across k=1–5) loaded correctly
- [ ] Inspect formatted prompts — ensure they match the model's expected chat template
- [ ] If LFM2-350M uses a different chat template than `<|im_start|>`, update `src/dataset.py`

## Phase 4 — Fine-tuning

- [ ] Run `notebooks/03_finetune.ipynb`
- [ ] Monitor training loss — should decrease steadily over 3 epochs
- [ ] If loss plateaus or diverges, see `docs/recommendations.md` for hyperparameter tuning
- [ ] Save LoRA adapter to `results/finetuned/lora_adapter/`

## Phase 5 — Evaluation and comparison

- [ ] Run `notebooks/04_eval_comparison.ipynb`
- [ ] Save `results/finetuned/scores.json`
- [ ] Verify results page at spatialft.github.io shows before/after chart
- [ ] Document delta in `README.md` results table

## Phase 6 — Presentation

- [ ] Deliver 10-minute live presentation (see `docs/slides.md` and `docs/speaker-notes.md`)
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
