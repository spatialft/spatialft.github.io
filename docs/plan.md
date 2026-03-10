# Project Plan

## Overview

Fine-tune **LiquidAI/LFM2.5-1.2B-Thinking** on spatial reasoning, measure improvement on
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

- [ ] Verify `LiquidAI/LFM2.5-1.2B-Thinking` exists on HuggingFace
      - If only `-Instruct` is available, use that and note it in the presentation
      - Check: https://huggingface.co/LiquidAI
- [ ] Verify StepGame dataset ID on HuggingFace datasets
      - Primary candidate: `sagi21805/StepGame`
      - Fallback: clone original repo https://github.com/ZhengxiangShi/StepGame and load from JSON
- [ ] Open a free Colab notebook, confirm T4 GPU is available
- [ ] Run `pip install -r requirements.txt` and confirm no conflicts
- [ ] Confirm Unsloth supports LFM2.5 architecture (check their GitHub issues/README)
      - Unsloth works best with Llama/Mistral/Qwen architectures
      - LFM2.5 is a liquid neural network — may need fallback to standard HF + PEFT

## Phase 2 — Baseline evaluation

- [ ] Run `notebooks/01_baseline_eval.ipynb` end to end
- [ ] Save `results/baseline/scores.json`
- [ ] Note overall accuracy and per-hop accuracy for k=1,3,5,10
- [ ] Spot-check 10 predictions manually — understand failure modes

## Phase 3 — Dataset preparation

- [ ] Run `notebooks/02_dataset_prep.ipynb`
- [ ] Confirm 4000 training / 250 eval examples (stratified across k=1–5) loaded correctly
- [ ] Inspect formatted prompts — ensure they match the model's expected chat template
- [ ] If LFM2.5 uses a different chat template than `<|im_start|>`, update `src/dataset.py`

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
| Property | Spatial reasoning | Measurable, well-benchmarked, LFM "Thinking" angle |
| Model | LFM2.5-1.2B-Thinking | Novel architecture, small enough for T4, Colab-friendly |
| Dataset | StepGame | Multi-hop structure gives clear difficulty gradient |
| Fine-tuning | LoRA via Unsloth | Memory efficient, fast on T4 |
| Evaluation metric | Accuracy per hop level k | Reveals where improvement occurs |
