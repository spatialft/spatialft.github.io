# Speaker Notes

Target: 10 minutes. Keep transitions brisk.

---

## Danny — Slides 1–3

### Slide 1 — Title (~20 sec)

Can a **350M model** learn spatial reasoning? LFM2-350M, LiquidAI. Small, fast, edge-realistic.

### Slide 2 — The Property (~75 sec)

Spatial reasoning sounds easy. "A left of B, B above C, where's A relative to C?" We do it instantly. Small models can't. They lose the thread after two or three hops.

**Prior work confirms the gap.** StepGame authors tested specialized reasoning architectures. Best result: **53% mean accuracy**, sharp drops past k=3. Yamada et al. tested GPT-4 on spatial navigation: **29% vs 67% for humans**. GPT-3.5 fell below random.

Not just a small-model problem. Our question: can **targeted fine-tuning** help at 350M?

### Slide 3 — The Model (~75 sec)

Why not Llama or Qwen? We wanted the **hardest version** of this experiment. 350 million parameters. If LoRA works here, that's useful for **on-device deployment**. Runs on a free Colab T4, no memory tricks.

*Hand off to Keming.*

---

## Keming — Slides 4–7

### Slide 4 — The Dataset (~60 sec)

StepGame. Synthetic spatial QA. **k = number of hops.** k=1: one fact. k=10: ten chained relations.

**8 directions.** We trained on **4,000 examples**, held out **250 for eval** (50 per hop level). The k-hop structure shows exactly where the model breaks.

### Slide 5 — Methodology (~60 sec)

**Pipeline:** baseline eval, data prep, LoRA fine-tuning, re-eval, compare.

LoRA freezes the base model, trains **small adapter matrices** on top. Not retraining 350M parameters. Just a few million adapter weights. Runs on a T4 in under an hour.

### Slide 6 — Baseline Results (~60 sec)

Overall: **14.4%**. k=1 is 16%, barely above random (**12.5%** for 8 directions). k=4, k=5, it falls apart. The model reads the last sentence and guesses. That's what we're trying to fix.

### Slide 7 — Training (~45 sec)

[Point to loss curve.] Stable decline, no spikes. **3 epochs, 4,000 examples.** Under 35 minutes on a T4, adapter about **11 MB**.

*Hand off to Jonas.*

---

## Jonas — Slides 8–10

### Slide 8 — Fine-Tuned Results (~75 sec)

Overall: **15.2% vs 14.4%**. 0.8 points on 250 examples. That's noise.

But per-hop: **k=1 jumped from 16% to 34%**. That's the signal. k=2, 3, 4 all dropped. The adapter learned single-hop patterns at a cost.

**Caveat:** 50 examples per hop. CIs range **+/-8 to 13pp**. These are directions, not conclusions. The per-hop shape is the finding.

### Slide 9 — Analysis (~60 sec)

k=1 gain is the strongest signal, CI is wide. Spot-checked failures: model **collapses diagonals into axis-aligned guesses**. "Upper-left" becomes "left" or "above." Dropping part of the chain instead of composing it.

**What would help:** chain-of-thought training data, balanced training across all k levels.

### Slide 10 — Conclusions (~45 sec)

LoRA on 4,000 StepGame examples. **k=1 improved, k=2-4 regressed.** Per-hop breakdown is the whole story. Report only overall accuracy? You miss the trade-off entirely.

Repo at the link. All four notebooks run on a free T4. Thanks.

---

## Timing check

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
