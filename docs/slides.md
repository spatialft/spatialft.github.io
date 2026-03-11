# Slide Deck — Content

10-minute presentation. Suggested pace: ~1 minute per slide.

---

## Slide 1 — Title

**Can a 1B Model Learn to Think in Space?**
Fine-Tuning LFM2.5-1.2B for Spatial Reasoning

> AIPI 590.03 — Project 1
> Jonas Neves · Daniel Ros · Keming Zhou

---

## Slide 2 — The Property: Spatial Reasoning

**Why spatial reasoning?**

- Fundamental to robotics, navigation, and embodied AI
- Multi-hop spatial inference is surprisingly hard for small models
- Clear, measurable degradation as complexity increases

**The challenge:**

> "Alice is to the left of Bob. Bob is above Carol. Dave is to the right of Alice.
> What is the relationship between Dave and Carol?"

A 1B model must chain multiple relations without losing track.

---

## Slide 3 — The Model: LFM2.5-1.2B-Thinking

**Why this model?**

- Novel **Liquid Neural Network** architecture (not a transformer)
- 1.2B parameters — fits on a free Colab T4 GPU
- **Thinking** variant adds explicit reasoning traces at inference
- Trending on HuggingFace — frontier of small-model research

[Include screenshot of HuggingFace model card]

---

## Slide 4 — The Dataset: StepGame

**StepGame** (Shi et al., 2022)

- Spatial QA benchmark with **k-hop difficulty levels** (k = 1 to 10)
- k = 1: single relation ("A is left of B")
- k = 10: chain of 10 relations to resolve
- We evaluate on k = 1 to 5 (50 examples per level)

**Our split:**
| Set | Examples |
|-----|----------|
| Train | 4,000 |
| Eval | 250 (50 per hop level, k=1–5) |

8 possible directions: left, right, above, below, upper-left, upper-right, lower-left, lower-right

---

## Slide 5 — Methodology

**Pipeline:** Baseline eval → Dataset prep → LoRA fine-tuning → Re-eval → Compare

**Fine-tuning approach:**
- LoRA (rank 16) via Unsloth — 4-bit quantized, T4-compatible
- 3 epochs, batch size 4 + gradient accumulation
- Learning rate 2e-4 with warmup

**Evaluation metric:**
- Exact-match accuracy overall and per hop level k

---

## Slide 6 — Baseline Results

**Before fine-tuning**

[Replace with actual numbers]

| Hop level | Accuracy |
|-----------|----------|
| k=1 | 62% |
| k=2 | 54% |
| k=3 | 36% |
| k=4 | 32% |
| k=5 | 18% |
| **Overall** | **40.4%** |

Key observation: accuracy drops sharply as k increases — the model loses
track of the chain.

[Include bar chart — baseline accuracy per hop level]

---

## Slide 7 — Training

**Loss curve during fine-tuning**

[Include training loss plot from Colab logs]

- Training time: ~34.7 minutes on T4
- Final training loss: ~0.006

**What we trained on:**
- Prompt: story + question (formatted with system instruction)
- Completion: correct direction label
- Optional: chain-of-thought reasoning steps

---

## Slide 8 — Fine-Tuned Results

**After fine-tuning**

[Replace with actual numbers]

| Hop level | Baseline | Fine-tuned | Delta |
|-----------|----------|------------|-------|
| k=1 | 62% | _% | +_% |
| k=2 | 54% | _% | +_% |
| k=3 | 36% | _% | +_% |
| k=4 | 32% | _% | +_% |
| k=5 | 18% | _% | +_% |
| **Overall** | **40.4%** | **_%** | **+_%** |

[Include full before/after bar chart — baseline vs fine-tuned per hop level]

---

## Slide 9 — Analysis

**Where did it improve most?**

- Expected: larger gains at low k (simpler cases), model learns the relation vocabulary
- Expected: smaller gains at high k (still struggles with long chains)
- Surprising finding (fill in after running): [e.g., "k=5 improved more than k=3"]

**Failure modes that remain:**
- [e.g., model outputs "to the left" instead of "left"]
- [e.g., model confuses upper-left vs left on diagonal cases]

**What would help further:**
- Chain-of-thought training data (step-by-step reasoning)
- More training examples at high k
- Larger LoRA rank

---

## Slide 10 — Conclusions

**Summary**

- LFM2.5-1.2B shows measurable baseline spatial reasoning capability
- LoRA fine-tuning on 4,000 examples improved accuracy by ~X% overall
- Gains are [larger/smaller/consistent] across hop levels

**Takeaways**

- Fine-tuning a small model on domain-specific data is practical and effective
- StepGame's k-hop structure makes evaluation principled and reproducible
- Liquid neural networks are a viable alternative architecture for targeted fine-tuning

**Repo:** [link]

---

## Backup slide — Example output

**Before fine-tuning:**
> Prompt: "A is left of B. B is above C. Where is A relative to C?"
> Model: "A is somewhere near C." *(wrong, non-directional)*

**After fine-tuning:**
> Model: "A is upper-left of C." *(correct)*
