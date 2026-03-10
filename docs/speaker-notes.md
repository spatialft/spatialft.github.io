# Speaker Notes

Target: 10 minutes. Each slide ~1 minute. Keep transitions brisk.

---

## Slide 1 — Title (~20 sec)

"For project 1, we looked at spatial reasoning — specifically, whether a 1-billion-parameter
model can learn to chain together multiple positional relationships. We used LiquidAI's
LFM2.5, which is a novel architecture that's been getting attention on HuggingFace."

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

"Most fine-tuning projects use Llama or Qwen. We went with LFM2.5 from LiquidAI. It's
based on liquid neural networks — a continuous-time architecture originally developed at
MIT — rather than the standard transformer. At 1.2B parameters it runs on a free Colab T4,
and LiquidAI released a 'Thinking' variant that produces explicit reasoning steps. That
made it a natural fit for a task where reasoning chains matter. It was also trending on
HuggingFace at the time of this project, which is a useful signal that it's well-maintained."

---

## Slide 4 — The Dataset (~60 sec)

"StepGame is a synthetic spatial QA dataset where k is the number of hops required. At k=1,
you have one fact: A is left of B. At k=10, you have ten chained facts and the model has to
resolve the final relationship. There are 8 possible answer directions. We used 4,000 training
examples and held out 250 for evaluation (50 per hop level, k=1–5). The k-hop structure is valuable because it lets us
see exactly where the model starts to break down, and where fine-tuning helps most."

---

## Slide 5 — Methodology (~60 sec)

"The pipeline is straightforward. Baseline eval first — always measure before you touch
anything. Then we prepared the data using the StepGame dataset, formatted it with the
model's chat template, and ran LoRA fine-tuning using Unsloth. LoRA is a parameter-efficient
method that adds small adapter matrices to the frozen base model — so we're not retraining
1.2 billion parameters, we're training maybe 10 million. Unsloth cuts memory by about 70%
and speeds training up 2x, which is why the whole thing fits on a T4."

---

## Slide 6 — Baseline Results (~60 sec)

"Here's where the model starts. [Read out overall accuracy.] The important pattern is what
happens as k increases. At k=1 the model does reasonably well — it's seen directional
language in pretraining. But by k=5 or k=10, accuracy drops significantly. The model isn't
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
chain-of-thought training data where the completion includes step-by-step reasoning rather
than just the final answer, and two, more training examples at high k, since that's where
the model struggles most. Both are straightforward extensions."

---

## Slide 10 — Conclusions (~45 sec)

"To wrap up: we picked spatial reasoning as a measurable, practically relevant property.
We fine-tuned a novel 1.2B liquid neural network on 4,000 examples using efficient LoRA
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
The point is fine-tuning — a 1.2B model with targeted training should outperform a larger
base model on this specific task. That's the value of fine-tuning.

**"Why LoRA instead of full fine-tuning?"**
Memory. Full fine-tuning a 1.2B model in float16 needs ~12GB just for weights. LoRA
with 4-bit quantization uses ~4GB total, fitting on a free T4.

**"Why LFM2.5 specifically?"**
It's a genuine alternative architecture to transformers, which makes for a more interesting
project. The Thinking variant also aligns with the multi-hop nature of the task.

**"How do you know the eval set isn't in the training set?"**
StepGame examples are generated programmatically. We shuffled and split before formatting,
so train and eval come from the same distribution but are non-overlapping by index.
