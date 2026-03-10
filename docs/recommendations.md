# Technical Recommendations

## Model

### Primary: LiquidAI/LFM2.5-1.2B-Thinking
- Check availability at https://huggingface.co/LiquidAI before committing
- The `-Thinking` variant adds chain-of-thought reasoning at inference time
- If unavailable, fall back to `LiquidAI/LFM2.5-1.2B-Instruct` and note it

### Unsloth compatibility risk
Unsloth optimizes Llama/Mistral/Qwen architectures natively. LFM2.5 uses a liquid neural
network (LNN) architecture, which may not be recognized.

**If Unsloth rejects LFM2.5:**
```python
# Fall back to standard PEFT without Unsloth
from peft import get_peft_model, LoraConfig
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer

config = LoraConfig(r=16, lora_alpha=32, target_modules=['q_proj','v_proj'])
model = get_peft_model(base_model, config)
```
This is slower but will work on any HF-compatible model.

**Alternative model if LFM2.5 proves incompatible:**
- `Qwen/Qwen3-0.6B` or `Qwen/Qwen3-1.7B` — Unsloth-native, strong baselines
- `meta-llama/Llama-3.2-1B-Instruct` — proven, widely documented

The presentation story changes slightly but the methodology stays the same.

---

## Dataset

### StepGame
- Original paper: "StepGame: A New Benchmark for Robust Multi-Hop Spatial Reasoning in Texts"
- k-hop difficulty: k=1 is a single relation ("A is left of B"), k=10 requires chaining 10 steps
- Expect baseline accuracy around 40-60% at k=1, dropping to 20-35% at k=10 for a 1B model
- 4000 training examples is sufficient for meaningful LoRA improvement

### Prompt format
The default prompt in `src/dataset.py` uses the ChatML format (`<|im_start|>`).
Check what format LFM2.5 expects — it may differ. Look for `tokenizer.chat_template`
after loading:
```python
print(tokenizer.chat_template)
```
If it prints a different template, update `format_prompt()` in `src/dataset.py` accordingly.

### Chain-of-thought augmentation (optional, improves results significantly)
Instead of just training on `answer`, include a reasoning chain in the completion:
```
The story says A is left of B, and B is above C.
Step 1: A is left of B → A.x < B.x
Step 2: B is above C → B.y > C.y
Therefore A is upper-left of C.
Answer: upper-left
```
Generating these chains is the main effort. Options:
1. Use Claude API to generate CoT for each training example (fast, costs ~$2 for 4000 examples)
2. Write a deterministic solver (StepGame has programmatic answers — see original repo)

Option 2 is more rigorous and fully reproducible. See the StepGame repo for the graph-based
answer generator which can be adapted to produce step-by-step reasoning.

---

## Fine-tuning hyperparameters

Defaults in notebook 3 are conservative and should work. If you see issues:

| Symptom | Fix |
|---------|-----|
| Loss not decreasing | Lower `learning_rate` to `1e-4` |
| OOM on T4 | Reduce `per_device_train_batch_size` to 2, increase `gradient_accumulation_steps` to 8 |
| Loss drops then spikes | Add `weight_decay=0.01` |
| Very slow convergence | Increase `lora_alpha` to `LORA_RANK * 4` |

LoRA rank 16 is a good default for a 1.2B model. If you have time for ablations,
try rank 8 (faster, slightly lower quality) and rank 32 (slower, potentially better).

---

## Evaluation

### Answer extraction edge cases
The `extract_answer()` function in `src/dataset.py` handles:
- Direct answer ("left")
- Answer at end of reasoning ("...therefore A is upper-left of C. upper-left")
- Answer embedded in text

Common failure mode: model outputs "to the left" instead of "left". Add normalization:
```python
text = text.replace("to the ", "").replace("of ", "")
```

### Statistical significance
With 250 eval examples, a 5% accuracy difference is meaningful.
For the presentation, report confidence intervals if time allows:
```python
import numpy as np
n = len(predictions)
acc = correct / n
ci = 1.96 * np.sqrt(acc * (1 - acc) / n)
print(f"{acc:.3f} ± {ci:.3f}")
```

---

## Colab tips

- Use `torch.cuda.empty_cache()` between notebooks if running in the same session
- Mount Google Drive to persist checkpoints across sessions:
  ```python
  from google.colab import drive
  drive.mount('/content/drive')
  OUTPUT_DIR = '/content/drive/MyDrive/aipi590/checkpoint'
  ```
- Colab T4 has 15GB VRAM. 4-bit quantized 1.2B + LoRA uses ~4GB — well within limits.
- Colab free tier disconnects after ~90 minutes idle. Notebook 3 training at 4000 examples
  should complete in ~30-45 minutes.
