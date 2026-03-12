# Speaker Notes

Target: 10 minutes. Each slide ~1 minute. Keep transitions brisk.

---

## Slide 1 — Title (~20 sec)

"For project 1, we looked at spatial reasoning. Specifically, whether a 350-million-parameter
model can learn to chain together multiple positional relationships. We used LiquidAI's
LFM2-350M because it is small, fast, and realistic for edge deployment."

---

## Slide 2 — The Property (~60 sec)

"Spatial reasoning is one of those capabilities that seems simple but degrades fast in small
models. Ask a model where Alice is relative to Carol after three intermediate hops, and it
often loses the thread. This is well-studied — there's a benchmark called StepGame that
was specifically designed to measure it — and it's practically relevant for robotics and
navigation. It also gives us a clean story for a 10-minute presentation: pick a difficulty
level, measure, improve, compare."

---

## Slide 3 — The Model (~75 sec)

"Most fine-tuning projects use Llama or Qwen. We went with LFM2-350M from LiquidAI because
the smaller checkpoint gives us a harder and more practical test. If fine-tuning helps here,
the result is useful for fast, low-cost deployments. It also keeps the full project easy to
run on a free Colab T4 without stretching memory or runtime."

---

## Slide 4 — The Dataset (~60 sec)

"StepGame is a synthetic spatial QA dataset where k is the number of hops required. At k=1,
you have one fact: A is left of B. At k=10, you have ten chained facts and the model has to
resolve the final relationship. There are 8 possible answer directions. We used 4,000 training
examples and held out 250 for evaluation (50 per hop level, k=1–5). The k-hop structure is valuable because it lets us
see exactly where the model starts to break down, and where fine-tuning helps most."

---

## Slide 5 — Methodology (~60 sec)

"The pipeline is straightforward. Baseline eval first. Always measure before you touch
anything. Then we prepared the data using the StepGame dataset, formatted it with the
model's chat template, and ran LoRA fine-tuning using PEFT. LoRA is a parameter-efficient
method that adds small adapter matrices to the frozen base model — so we're not retraining
the full base model, we're training a small set of adapter weights. That is why the whole
thing stays cheap and easy to rerun on a T4."

---

## Slide 6 — Baseline Results (~60 sec)

"Here's where the model starts. [Read out overall accuracy.] The important pattern is what
happens as k increases. At k=1 the model does reasonably well — it's seen directional
language in pretraining. But by k=4 or k=5, accuracy drops significantly. The model isn't
tracking intermediate steps; it's making a guess based on the last fact it read. This is
the behavior we want to fix."

---

## Slide 7 — Training (~45 sec)

"Training took about [X] minutes on a T4. [Point to loss curve.] Loss decreased steadily,
which is what we want — no instability, no divergence. We ran 3 epochs on 4,000 examples.
The LoRA adapter is about [X MB], which is a fraction of the base model size."

---

## Slide 8 — Fine-Tuned Results (~75 sec)

"After fine-tuning. [Read out the delta.] Overall accuracy went up by [X] percentage points.
The per-hop breakdown is more interesting. [Walk through the chart.] At low k, the model
was already decent and improved moderately. At higher k, [describe what you see — either
it improved more than expected, or it plateaued, or a specific k level jumped]. This tells
us [interpretation]. The chart makes this visually clear — you can see the fine-tuned bars
are consistently higher, with the gap [widening/narrowing] at harder hop levels."

---

## Slide 9 — Analysis (~60 sec)

"A few things worth noting. First, [mention the most interesting finding from your run].
Second, there are still failure modes — [mention the most common error pattern you saw in
spot-checking]. The two most obvious things that would improve results further are: one,
reasoning-augmented training data where the completion includes intermediate steps, and two,
more training examples at high k, since that's where
the model struggles most. Both are straightforward extensions."

---

## Slide 10 — Conclusions (~45 sec)

"To wrap up: we picked spatial reasoning as a measurable, practically relevant property.
We fine-tuned a 350M LiquidAI model on 4,000 examples using efficient LoRA
training. We got a [X]% improvement overall, with clear gains across hop levels. The main
lesson is that targeted fine-tuning on a focused dataset moves the needle even at small
scale. The repo is at [link] — all four notebooks are runnable end to end on a free Colab
T4. Thanks."

---

## Timing check

| Slide | Target | Notes |
|-------|--------|-------|
| 1 Title | 0:20 | Don't linger |
| 2 Property | 1:20 | Motivate clearly |
| 3 Model | 2:35 | Explain LNN briefly, don't go deep |
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
