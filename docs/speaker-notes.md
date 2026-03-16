# Speaker Notes

Target: 10 minutes. Each slide ~1 minute. Keep transitions brisk.

---

## Slide 1 — Title (~20 sec)

"Our project: can a 350-million-parameter model learn spatial reasoning? LFM2-350M from LiquidAI. Small, fast, edge-realistic."

---

## Slide 2 — The Property (~60 sec)

"Spatial reasoning sounds easy. 'Alice is left of Bob, Bob is above Carol, where is Alice relative to Carol?' We can do that. Small models can't. They lose the thread after two or three hops. There's a benchmark for exactly this, StepGame. We picked it because the difficulty scales cleanly: one hop, two hops, up to ten. Measure, fine-tune, re-measure."

---

## Slide 3 — The Model (~75 sec)

"Why not Llama or Qwen? We wanted the hardest version of this experiment. 350 million parameters. If LoRA can teach spatial reasoning at this scale, that's actually useful for on-device deployment. And practically, the whole thing runs on a free Colab T4 without any memory tricks."

---

## Slide 4 — The Dataset (~60 sec)

"StepGame. Synthetic spatial QA. k is the number of hops. k=1, one fact: 'A is left of B.' k=10, ten chained facts, resolve the final relation. Eight possible directions. We trained on 4,000 examples, held out 250 for eval, 50 per hop level. The k-hop structure is the whole point. It shows you exactly where the model breaks."

---

## Slide 5 — Methodology (~60 sec)

"Baseline eval first. You have to know where you're starting. Then data prep with the model's chat template, then LoRA fine-tuning through PEFT. For anyone unfamiliar: LoRA freezes the base model and trains small adapter matrices on top. We're not retraining 350 million parameters. Just a few million adapter weights. That's why it runs on a T4 in under an hour."

---

## Slide 6 — Baseline Results (~60 sec)

"Here's the baseline. [Read overall accuracy.] Now look at the per-hop breakdown. k=1 is 16%, barely above random (12.5% for 8 directions). It gets worse from there. k=4, k=5? It falls apart. The model isn't chaining anything. It reads the last sentence and guesses. That's what we're trying to fix."

---

## Slide 7 — Training (~45 sec)

"[Point to loss curve.] Stable decline, no spikes. Three epochs on 4,000 examples. The exact training time, final loss, and adapter size are in the repo's training_stats.json. Short version: under 35 minutes on a T4, adapter is about 11 megabytes. Tiny."

---

## Slide 8 — Fine-Tuned Results (~75 sec)

"OK, results. Overall: 15.2% vs 14.4% baseline. 0.8 points on 250 examples. That's noise. But the per-hop numbers are more interesting. k=1 jumped from 16% to 34%. That's the biggest signal. k=2, 3, 4 all dropped. So the adapter learned single-hop patterns and it came at a cost. Important caveat: each hop level is only 50 examples, so 95% confidence intervals on individual hops range from plus or minus 8 to 13 points depending on the observed accuracy. These are directions, not conclusions. The overall number is noise; the per-hop shape is the finding."

---

## Slide 9 — Analysis (~60 sec)

"What did we actually learn? The k=1 jump is the strongest signal, though the CI is wide. When we spot-checked medium-hop failures, there's a pattern: the model collapses diagonal answers into axis-aligned ones. 'Upper-left' becomes 'left' or 'above.' It's dropping part of the chain instead of composing it. Two things that would help: chain-of-thought training data where the completion walks through each step, and more high-k training examples. We didn't have time for either, but they're the obvious next moves."

---

## Slide 10 — Conclusions (~45 sec)

"Summary. LoRA on 4,000 StepGame examples. k=1 improved, k=2 through 4 regressed. The per-hop breakdown is the whole story. If we'd only reported overall accuracy, we'd have missed the trade-off entirely. Repo is at the link. All four notebooks run on a free T4. Thanks."

---

## Timing check

| Slide | Target | Notes |
|-------|--------|-------|
| 1 Title | 0:20 | Don't linger |
| 2 Property | 1:20 | Motivate clearly |
| 3 Model | 2:35 | Explain LFM2 briefly, don't go deep |
| 4 Dataset | 3:35 | k-hop is the key concept |
| 5 Method | 4:35 | LoRA in one sentence is enough |
| 6 Baseline | 5:35 | Let the numbers land |
| 7 Training | 6:20 | Show loss curve, keep brief |
| 8 Results | 7:35 | This is the payoff slide — take your time |
| 9 Analysis | 8:35 | One interesting finding + honest limitations |
| 10 Conclusions | 9:20 | Brisk, confident |
| Buffer | 9:20–10:00 | Questions or pad slide 8/9 if needed |

---

## Common questions to prepare for

**"Why not just use a bigger model?"**
The point is fine-tuning. A 350M model is cheap, fast, and realistic for deployment, so the
question is how much task-specific accuracy we can recover with targeted training.

**"Why LoRA instead of full fine-tuning?"**
Memory and speed. LoRA with 4-bit loading keeps the experiment lightweight and repeatable on
free Colab hardware.

**"Why LFM2-350M specifically?"**
It is the smallest model in the family that still has a serious instruction-tuned release.
That makes it the best test of whether focused fine-tuning can rescue a very constrained model.

**"How do you know the eval set isn't in the training set?"**
StepGame examples are generated programmatically. We shuffled and split before formatting,
so train and eval come from the same distribution but are non-overlapping by index.
