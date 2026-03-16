# Slide Deck — Content

10-minute presentation. Suggested pace: ~1 minute per slide.

---

## Slide 1 — Title

**Can a 350M Model Learn Spatial Reasoning?**
Fine-Tuning LFM2-350M for Spatial Reasoning

> AIPI 590.03 — Project 1
> Jonas Neves · Daniel Ros · Keming Zhou

---

## Slide 2 — The Property: Spatial Reasoning

**Why spatial reasoning?**

- Fundamental to robotics, navigation, and embodied AI
- Multi-hop spatial inference is surprisingly hard for small models
- Clear, measurable degradation as complexity increases

**Prior work:**

- Shi et al. (2022): specialized reasoning architectures scored 15–53% mean accuracy on StepGame; all degraded sharply beyond k=3
- Yamada et al. (2024): GPT-4 achieved 29% on spatial navigation tasks vs. 67% for humans; GPT-3.5 fell below random chance
- Spatial reasoning remains hard even for frontier models. Can targeted fine-tuning help a 350M model?

**The challenge:**

> "Alice is to the left of Bob. Bob is above Carol. Dave is to the right of Alice.
> What is the relationship between Dave and Carol?"

A 350M model must chain multiple relations without losing track.

---

## Slide 3 — The Model: LFM2-350M

**Why this model?**

- 354M parameters (Amini et al., 2025), materially smaller and faster to iterate on
- 32k context window with an edge-focused LFM2 architecture
- Good fit for on-device and low-latency deployment constraints
- If targeted tuning works at 350M, the result generalizes to cheap, fast inference

*(Show HuggingFace model card)*

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
- LoRA (Hu et al., 2022; rank 16) via `transformers` + `peft`, 4-bit quantized, T4-compatible
- 3 epochs, batch size 2 × 8 gradient accumulation steps (effective batch 16)
- Learning rate 2e-4 with warmup

**Evaluation metric:**
- Exact-match accuracy overall and per hop level k

---

## Slide 6 — Baseline Results

**Before fine-tuning**

| Hop level | Accuracy |
|-----------|----------|
| k=1 | 16% |
| k=2 | 16% |
| k=3 | 18% |
| k=4 | 14% |
| k=5 | 8% |
| **Overall** | **14.4%** |

Key observation: accuracy is low across all hop levels, with a further drop at k=5.
A 350M model with no spatial fine-tuning is close to random on this benchmark (1-in-8 directions).

*(Show baseline accuracy chart)*

---

## Slide 7 — Training

**Loss curve during fine-tuning**

*(Show training loss curve)*

- Training time: under 35 min on T4
- Loss decreased steadily; final loss near zero
- LoRA adapter: ~11 MB (see project page for exact values)

**What we trained on:**
- Prompt: story + question (formatted with system instruction)
- Completion: correct direction label
- Direct-answer supervision (reasoning augmentation was not explored)

---

## Slide 8 — Fine-Tuned Results

**After fine-tuning**

| Hop level | Baseline | Fine-tuned | Delta |
|-----------|----------|------------|-------|
| k=1 | 16% | 34% | +18% |
| k=2 | 16% | 8% | −8% |
| k=3 | 18% | 10% | −8% |
| k=4 | 14% | 10% | −4% |
| k=5 | 8% | 14% | +6% |
| **Overall** | **14.4%** | **15.2%** | **+0.8%** |

At n=50 per hop, 95% CIs range from +/-8pp (at low accuracies) to +/-13pp (near 34%), so these shifts are directional, not conclusive. The 0.8pp overall gain is within noise (n=250).

*(Show comparison chart)*

---

## Slide 9 — Analysis

**What the results show:**

- k=1 improved sharply (+18pp): suggests the adapter picked up single-hop relation vocabulary, though CI is wide at n=50
- k=2–4 regressed (−4 to −8pp): multi-hop chaining appears disrupted, but each shift is within the per-hop noise floor
- k=5 recovered slightly (+6pp): within noise at this sample size

**Likely cause:**
The training set has more k=1 and k=2 examples; the adapter may have overfit short-context patterns at the expense of the intermediate hop range.

**Observed failure pattern:**
On medium-hop questions, wrong answers often collapse diagonal relations into simpler axis-aligned guesses like `above` or `right`, which suggests the model is dropping part of the relation chain instead of composing it.

**What would help further:**
- Chain-of-thought training data (step-by-step reasoning)
- Balanced training across all k levels

---

## Slide 10 — Conclusions

**Summary**

- LoRA fine-tuning on 4,000 examples shifted the distribution: strong gain at k=1, regressions at k=2–4
- Overall accuracy moved from 14.4% to 15.2% (+0.8pp on n=250 — within noise)
- The k-hop breakdown tells the more useful story: the adapter specializes rather than generalizes

**Takeaways**

- Targeted tuning can teach a small model some short-range spatial patterns, especially at k=1.
- That same adapter does not generalize cleanly to multi-hop chaining, so overall accuracy hides the trade-off unless the results are broken out by hop level.

**Repo:** [spatialft.github.io](https://github.com/spatialft/spatialft.github.io)

---

## Backup slide — Example output

*(From committed evaluation predictions)*

**Prompt:**
> "L is slightly off center to the top left and V is slightly off center to the bottom right. A is to the bottom right of V. What is the relation of the agent L to the agent A?" *(k=2)*

**Baseline:** "right" *(wrong)*
**Fine-tuned:** "upper-left" *(correct)*
