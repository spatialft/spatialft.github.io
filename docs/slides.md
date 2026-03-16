# Slide Deck

10-minute presentation. Three speakers.

---

## Danny — Slides 1–3

---

### Slide 1 — Title (~20 sec)

**Can a 350M Model Learn Spatial Reasoning?**
Fine-Tuning LFM2-350M for Spatial Reasoning

> AIPI 590.03 — Project 1
> Jonas Neves · Daniel Ros · Keming Zhou

**Notes:** Can a **350M model** learn spatial reasoning? LFM2-350M, LiquidAI. Small, fast, edge-realistic.

---

### Slide 2 — The Property: Spatial Reasoning (~75 sec)

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

**Notes:** Spatial reasoning sounds easy. "A left of B, B above C, where's A relative to C?" We do it instantly. Small models can't. **Prior work confirms the gap.** StepGame: best result **53% mean**, sharp drops past k=3. Yamada et al.: GPT-4 at **29% vs 67% for humans**. GPT-3.5 below random. Not just a small-model problem. Our question: can **targeted fine-tuning** help at 350M?

---

### Slide 3 — The Model: LFM2-350M (~75 sec)

**Why this model?**

- 354M parameters (Amini et al., 2025), materially smaller and faster to iterate on
- 32k context window with an edge-focused LFM2 architecture
- Good fit for on-device and low-latency deployment constraints
- If targeted tuning works at 350M, the result generalizes to cheap, fast inference

*(Show HuggingFace model card)*

**Notes:** Why not Llama or Qwen? We wanted the **hardest version** of this experiment. 350 million parameters. If LoRA works here, that's useful for **on-device deployment**. Runs on a free Colab T4, no memory tricks. *Hand off to Keming.*

---

## Keming — Slides 4–7

---

### Slide 4 — The Dataset: StepGame (~60 sec)

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

**Notes:** StepGame. Synthetic spatial QA. **k = number of hops.** k=1: one fact. k=10: ten chained relations. **8 directions.** We trained on **4,000 examples**, held out **250 for eval** (50 per hop level). The k-hop structure shows exactly where the model breaks.

---

### Slide 5 — Methodology (~60 sec)

**Pipeline:** Baseline eval → Dataset prep → LoRA fine-tuning → Re-eval → Compare

**Fine-tuning approach:**
- LoRA (Hu et al., 2022; rank 16) via `transformers` + `peft`, 4-bit quantized, T4-compatible
- 3 epochs, batch size 2 × 8 gradient accumulation steps (effective batch 16)
- Learning rate 2e-4 with warmup

**Evaluation metric:**
- Exact-match accuracy overall and per hop level k

**Notes:** **Pipeline:** baseline eval, data prep, LoRA fine-tuning, re-eval, compare. LoRA freezes the base model, trains **small adapter matrices** on top. Not retraining 350M parameters. Just a few million adapter weights. Runs on a T4 in under an hour.

---

### Slide 6 — Baseline Results (~60 sec)

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

**Notes:** Overall: **14.4%**. k=1 is 16%, barely above random (**12.5%** for 8 directions). k=4, k=5, it falls apart. The model reads the last sentence and guesses. That's what we're trying to fix.

---

### Slide 7 — Training (~45 sec)

**Loss curve during fine-tuning**

*(Show training loss curve)*

- Training time: under 35 min on T4
- Loss decreased steadily; final loss near zero
- LoRA adapter: ~11 MB (see project page for exact values)

**What we trained on:**
- Prompt: story + question (formatted with system instruction)
- Completion: correct direction label
- Direct-answer supervision (reasoning augmentation was not explored)

**Notes:** [Point to loss curve.] Stable decline, no spikes. **3 epochs, 4,000 examples.** Under 35 minutes on a T4, adapter about **11 MB**. *Hand off to Jonas.*

---

## Jonas — Slides 8–10

---

### Slide 8 — Fine-Tuned Results (~75 sec)

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

**Notes:** Overall: **15.2% vs 14.4%**. 0.8 points on 250 examples. That's noise. But per-hop: **k=1 jumped from 16% to 34%**. That's the signal. k=2, 3, 4 all dropped. The adapter learned single-hop patterns at a cost. **Caveat:** 50 examples per hop. CIs range **+/-8 to 13pp**. These are directions, not conclusions. The per-hop shape is the finding.

---

### Slide 9 — Analysis (~60 sec)

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

**Notes:** k=1 gain is the strongest signal, CI is wide. Spot-checked failures: model **collapses diagonals into axis-aligned guesses**. "Upper-left" becomes "left" or "above." Dropping part of the chain instead of composing it. **What would help:** chain-of-thought training data, balanced training across all k levels.

---

### Slide 10 — Conclusions (~45 sec)

**Summary**

- LoRA fine-tuning on 4,000 examples shifted the distribution: strong gain at k=1, regressions at k=2–4
- Overall accuracy moved from 14.4% to 15.2% (+0.8pp on n=250 — within noise)
- The k-hop breakdown tells the more useful story: the adapter specializes rather than generalizes

**Takeaways**

- Targeted tuning can teach a small model some short-range spatial patterns, especially at k=1.
- That same adapter does not generalize cleanly to multi-hop chaining, so overall accuracy hides the trade-off unless the results are broken out by hop level.

**Repo:** [spatialft.github.io](https://github.com/spatialft/spatialft.github.io)

**Notes:** LoRA on 4,000 StepGame examples. **k=1 improved, k=2-4 regressed.** Per-hop breakdown is the whole story. Report only overall accuracy? You miss the trade-off entirely. Repo at the link. All four notebooks run on a free T4. Thanks.

---

## Backup slide — Example output

*(From committed evaluation predictions)*

**Prompt:**
> "L is slightly off center to the top left and V is slightly off center to the bottom right. A is to the bottom right of V. What is the relation of the agent L to the agent A?" *(k=2)*

**Baseline:** "right" *(wrong)*
**Fine-tuned:** "upper-left" *(correct)*

---

## Timing

| Slide | Speaker | Target | Notes |
|-------|---------|--------|-------|
| 1 Title | Danny | 0:20 | Don't linger |
| 2 Property + Lit | Danny | 1:35 | Motivate + prior work |
| 3 Model | Danny | 2:50 | Why 350M, hand off |
| 4 Dataset | Keming | 3:50 | k-hop is the key concept |
| 5 Method | Keming | 4:50 | LoRA in one sentence |
| 6 Baseline | Keming | 5:50 | Let the numbers land |
| 7 Training | Keming | 6:35 | Loss curve, hand off |
| 8 Results | Jonas | 7:50 | Payoff slide, take your time |
| 9 Analysis | Jonas | 8:50 | Failure pattern + next steps |
| 10 Conclusions | Jonas | 9:35 | Brisk, confident |
| Buffer | | 9:35–10:00 | Q&A or pad slide 8/9 |

---

## Common questions (Jonas fields these)

**"Why not a bigger model?"**
The point is fine-tuning at constrained scale. If it works at 350M, that's cheap, fast, deployable.

**"Why LoRA instead of full fine-tuning?"**
Memory and speed. 4-bit LoRA runs on free Colab hardware.

**"Why LFM2-350M specifically?"**
Smallest in the family with a serious instruction-tuned release. Best test of whether targeted tuning rescues a constrained model.

**"How do you know eval isn't in training?"**
StepGame is generated programmatically. We shuffled and split before formatting. Same distribution, non-overlapping by index.
