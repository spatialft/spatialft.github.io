---
description: |
  Reviews a pull request against the spatialft spatial reasoning fine-tuning project rubric.
  Posts a structured review comment on the PR.

strict: false

engine:
  id: copilot
  model: claude-sonnet-4

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

permissions: read-all

safe-outputs:
  add-comment:

tools:
  github:
    toolsets: [pull_requests, repos]

timeout-minutes: 10
---

# PR Review

Review PR #${{ github.event.pull_request.number }} for the spatialft spatial reasoning fine-tuning project against `REQUIREMENTS_CHECKLIST.md`.

Check:
- **Rubric compliance** — flag violations by ID (e.g. EVAL3, FT1, REPO1)
- **Notebook hygiene** — no large cell outputs committed, Colab setup cell present, no hardcoded local paths
- **Data integrity** — data files in `data/` not committed (gitignored), only `results/*/scores.json` and `results/examples.json` committed as artifacts
- **Security** — no `.env` committed, no API keys or HuggingFace tokens hardcoded in notebooks
- **Result validity** — if scores.json is changed, verify accuracy values are in [0, 1] and per-hop keys match expected format (`accuracy_k{n}`)
- **Fine-tuning correctness** — LoRA config targets attention modules, hyperparameters are reasonable for a T4 GPU (batch size, rank, learning rate)

Deduction triggers: committing model checkpoints or adapter weights (−10), hardcoded secrets in notebooks (−10), data leakage between train/eval splits (−10), PR without summary (−5), results committed without a corresponding notebook run (−3).

Post a comment on the PR with this format:
- **Summary** (2–3 sentences)
- **Checklist items affected**
- **Issues** (blocking, numbered)
- **Suggestions** (non-blocking, numbered)
- **Verdict**: Approve / Request Changes / Comment
