# Export for `lm-arena`

`lm-arena.github.io` loads single-file GGUF artifacts from Hugging Face via `hf_repo` + `hf_file`. This repo does not produce that format by default. Notebook 03 saves a PEFT LoRA adapter to `results/finetuned/lora_adapter/`, which must be merged back into the base model and converted to GGUF first.

Use:

```sh
make export-lm-arena ARGS="--llama-cpp-dir /path/to/llama.cpp --quantize Q4_K_M"
```

That command:

1. merges `results/finetuned/lora_adapter/` into `LiquidAI/LFM2-350M`
2. saves merged Hugging Face weights under `results/finetuned/export/merged_hf/`
3. converts the merged model to `results/finetuned/export/LFM2-350M-StepGame-f16.gguf`
4. optionally quantizes to `results/finetuned/export/LFM2-350M-StepGame-f16-Q4_K_M.gguf`

After exporting:

1. upload the quantized GGUF to a Hugging Face repo
2. add a new model entry in `config/models.py` in the `lm-arena.github.io` repository
3. set `hf_repo` to that repo and `hf_file` to the GGUF filename

Example `lm-arena` config values:

```python
name="lfm2spatial",
model_id="lfm2-350m-stepgame",
display_name="LFM2 350M Spatial",
hf_repo="<your-hf-username>/LFM2-350M-StepGame-GGUF",
hf_file="LFM2-350M-StepGame-f16-Q4_K_M.gguf",
owned_by="spatialft",
dockerfile="llama-server",
```
