---
base_model: LiquidAI/LFM2-350M
library_name: peft
pipeline_tag: text-generation
tags:
- base_model:adapter:LiquidAI/LFM2-350M
- lora
- sft
- transformers
- trl
---

# LFM2-350M LoRA adapter — StepGame spatial reasoning

LoRA adapter fine-tuned on StepGame spatial QA (k=1–5) for AIPI 590.03 Project 1.

**Base model:** [LiquidAI/LFM2-350M](https://huggingface.co/LiquidAI/LFM2-350M)
**Training data:** 4,000 StepGame examples (k=1–5 hop levels)
**Method:** LoRA rank 16, 4-bit quantized, 3 epochs on a T4 GPU
**Eval results:** 15.2% overall accuracy (n=250); baseline was 14.4%

Per-hop breakdown: k=1 improved from 16% to 34%; k=2–4 regressed; k=5 improved from 8% to 14%.

See the [project repo](https://github.com/spatialft/spatialft.github.io) for training notebooks and full evaluation details.

### Framework versions

- PEFT 0.18.1