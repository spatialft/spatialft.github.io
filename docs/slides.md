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

**The challenge:**

> "Alice is to the left of Bob. Bob is above Carol. Dave is to the right of Alice.
> What is the relationship between Dave and Carol?"

A 350M model must chain multiple relations without losing track.

---

## Slide 3 — The Model: LFM2-350M

**Why this model?**

- 354M parameters, materially smaller and faster to iterate on
- 32k context window with an edge-focused LFM2 architecture
- Good fit for on-device and low-latency deployment constraints
- If targeted tuning works at 350M, the result generalizes to cheap, fast inference

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
- LoRA (rank 16) via `transformers` + `peft`, 4-bit quantized, T4-compatible
- 3 epochs, batch size 4 + gradient accumulation
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
- Optional: reasoning-augmented completions if direct-answer tuning plateaus

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

The adapter learns k=1 well, but at the cost of k=2–4. The 0.8pp overall gain is within noise (n=250).

[Include full before/after bar chart — baseline vs fine-tuned per hop level]

---

## Slide 9 — Analysis

**What the results show:**

- k=1 improved sharply (+18pp): the adapter learns single-hop relation vocabulary
- k=2–4 regressed (−4 to −8pp): multi-hop chaining appears to have been disrupted
- k=5 recovered slightly (+6pp): unclear whether meaningful at this sample size

**Likely cause:**
The training set has more k=1 and k=2 examples; the adapter may have overfit short-context patterns at the expense of the intermediate hop range.

**What would help further:**
- Chain-of-thought training data (step-by-step reasoning)
- Balanced training across all k levels
- Larger LoRA rank

---

## Slide 10 — Conclusions

**Summary**

- LoRA fine-tuning on 4,000 examples shifted the distribution: strong gain at k=1, regressions at k=2–4
- Overall accuracy moved from 14.4% to 15.2% (+0.8pp on n=250 — within noise)
- The k-hop breakdown tells the more useful story: the adapter specializes rather than generalizes

**Takeaways**

- Small models can pick up short-range spatial patterns with targeted tuning
- Multi-hop generalization requires more than format-matched training data
- StepGame's per-hop structure exposes trade-offs that an overall accuracy number hides

**Repo:** [link]

---

## Backup slide — Example output

**Before fine-tuning:**
> Prompt: "A is left of B. B is above C. Where is A relative to C?"
> Model: "A is somewhere near C." *(wrong, non-directional)*

**After fine-tuning:**
> Model: "A is upper-left of C." *(correct)*
