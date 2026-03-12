#!/usr/bin/env python3
"""Export the fine-tuned LFM2 adapter into a GGUF artifact for lm-arena."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_BASE_MODEL = "LiquidAI/LFM2-350M"
DEFAULT_ADAPTER_DIR = Path("results/finetuned/lora_adapter")
DEFAULT_EXPORT_ROOT = Path("results/finetuned/export")
DEFAULT_MERGED_DIR = DEFAULT_EXPORT_ROOT / "merged_hf"
DEFAULT_F16_GGUF = DEFAULT_EXPORT_ROOT / "LFM2-350M-StepGame-f16.gguf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge the StepGame LoRA adapter into LiquidAI/LFM2-350M and optionally "
            "convert the merged model into GGUF for lm-arena."
        )
    )
    parser.add_argument(
        "--base-model",
        default=DEFAULT_BASE_MODEL,
        help=f"Hugging Face base model to merge into the adapter. Default: {DEFAULT_BASE_MODEL}",
    )
    parser.add_argument(
        "--adapter-dir",
        type=Path,
        default=DEFAULT_ADAPTER_DIR,
        help=f"Path to the PEFT adapter directory. Default: {DEFAULT_ADAPTER_DIR}",
    )
    parser.add_argument(
        "--merged-dir",
        type=Path,
        default=DEFAULT_MERGED_DIR,
        help=f"Output directory for merged Hugging Face weights. Default: {DEFAULT_MERGED_DIR}",
    )
    parser.add_argument(
        "--gguf-out",
        type=Path,
        default=DEFAULT_F16_GGUF,
        help=f"Output path for the unquantized GGUF. Default: {DEFAULT_F16_GGUF}",
    )
    parser.add_argument(
        "--llama-cpp-dir",
        type=Path,
        help="Path to a local llama.cpp checkout. Required for GGUF conversion.",
    )
    parser.add_argument(
        "--quantize",
        choices=["Q4_K_M", "Q5_K_M", "Q8_0"],
        help="Optional quantization target. Requires llama-quantize in --llama-cpp-dir.",
    )
    parser.add_argument(
        "--quantized-out",
        type=Path,
        help="Output path for the quantized GGUF. Defaults next to --gguf-out.",
    )
    parser.add_argument(
        "--hf-token",
        help="Optional Hugging Face token for gated/private model access.",
    )
    parser.add_argument(
        "--skip-gguf",
        action="store_true",
        help="Only export merged Hugging Face weights. Skip GGUF conversion.",
    )
    return parser.parse_args()


def require_exists(path: Path, description: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return path


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def merge_adapter(
    *,
    base_model: str,
    adapter_dir: Path,
    merged_dir: Path,
    hf_token: str | None,
) -> None:
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Merging adapter {adapter_dir} into base model {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, token=hf_token)
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype="auto",
        token=hf_token,
    )
    model = PeftModel.from_pretrained(base, str(adapter_dir), token=hf_token)
    merged = model.merge_and_unload()

    merged_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)
    print(f"Merged model written to {merged_dir}")


def find_convert_script(llama_cpp_dir: Path) -> Path:
    candidates = [
        llama_cpp_dir / "convert_hf_to_gguf.py",
        llama_cpp_dir / "scripts" / "convert_hf_to_gguf.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find convert_hf_to_gguf.py in llama.cpp checkout. "
        f"Tried: {', '.join(str(c) for c in candidates)}"
    )


def find_quantize_binary(llama_cpp_dir: Path) -> Path:
    candidates = [
        llama_cpp_dir / "build" / "bin" / "llama-quantize",
        llama_cpp_dir / "bin" / "llama-quantize",
        llama_cpp_dir / "llama-quantize",
        llama_cpp_dir / "build" / "bin" / "quantize",
        llama_cpp_dir / "quantize",
    ]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError(
        "Could not find an executable llama-quantize binary in llama.cpp checkout. "
        f"Tried: {', '.join(str(c) for c in candidates)}"
    )


def convert_to_gguf(
    *,
    merged_dir: Path,
    gguf_out: Path,
    llama_cpp_dir: Path,
) -> None:
    convert_script = find_convert_script(llama_cpp_dir)
    gguf_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(convert_script),
        str(merged_dir),
        "--outfile",
        str(gguf_out),
        "--outtype",
        "f16",
    ]
    run(cmd)
    print(f"Unquantized GGUF written to {gguf_out}")


def quantize_gguf(
    *,
    gguf_in: Path,
    quantized_out: Path,
    quantize: str,
    llama_cpp_dir: Path,
) -> None:
    quantize_bin = find_quantize_binary(llama_cpp_dir)
    quantized_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(quantize_bin),
        str(gguf_in),
        str(quantized_out),
        quantize,
    ]
    run(cmd)
    print(f"Quantized GGUF written to {quantized_out}")


def default_quantized_path(gguf_out: Path, quantize: str) -> Path:
    return gguf_out.with_name(f"{gguf_out.stem}-{quantize}{gguf_out.suffix}")


def main() -> int:
    args = parse_args()
    adapter_dir = require_exists(args.adapter_dir, "Adapter directory")
    args.merged_dir.parent.mkdir(parents=True, exist_ok=True)

    if args.merged_dir.exists() and any(args.merged_dir.iterdir()):
        print(f"Removing existing merged export at {args.merged_dir}")
        shutil.rmtree(args.merged_dir)

    merge_adapter(
        base_model=args.base_model,
        adapter_dir=adapter_dir,
        merged_dir=args.merged_dir,
        hf_token=args.hf_token,
    )

    if args.skip_gguf:
        print("Skipping GGUF conversion as requested.")
        return 0

    if not args.llama_cpp_dir:
        raise ValueError("--llama-cpp-dir is required unless --skip-gguf is set")

    llama_cpp_dir = require_exists(args.llama_cpp_dir, "llama.cpp directory")
    convert_to_gguf(
        merged_dir=args.merged_dir,
        gguf_out=args.gguf_out,
        llama_cpp_dir=llama_cpp_dir,
    )

    if args.quantize:
        quantized_out = args.quantized_out or default_quantized_path(args.gguf_out, args.quantize)
        quantize_gguf(
            gguf_in=args.gguf_out,
            quantized_out=quantized_out,
            quantize=args.quantize,
            llama_cpp_dir=llama_cpp_dir,
        )

    print("\nNext steps for lm-arena:")
    print("1. Upload the quantized GGUF to a Hugging Face repo.")
    print("2. Add a new model entry to lm-arena.github.io/config/models.py.")
    print("3. Point hf_repo/hf_file at the uploaded GGUF and deploy inference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
