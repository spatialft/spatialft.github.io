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

LoRA adapter fine-tuned on StepGame spatial QA (k=1-5) for AIPI 590.03 Project 1.

**Base model:** [LiquidAI/LFM2-350M](https://huggingface.co/LiquidAI/LFM2-350M)
**Training data:** 10,000 stratified StepGame examples (2,000 per k level, k=1-5)
**Method:** LoRA rank 16, 4-bit quantized, 3 epochs on a T4 GPU
**Eval results:** 70.4% overall accuracy (n=250); baseline was 16.0%

Per-hop breakdown: k=1 94%, k=2 84%, k=3 72%, k=4 50%, k=5 52%. Baseline was near random (16%) across all levels.

See the [project repo](https://github.com/spatialft/spatialft.github.io) for training notebooks and full evaluation details.

### Framework versions

- PEFT 0.18.1
