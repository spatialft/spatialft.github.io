#!/usr/bin/env python3
"""
Export the finetuned LFM2-350M model to ONNX for browser inference via Transformers.js.

Produces:
  results/finetuned/export/onnx/
    model.onnx          full precision (fp32)
    model_fp16.onnx     fp16
    model_q4.onnx       int4 quantized  ← Transformers.js default for WebGPU
    tokenizer.json      (+ other tokenizer files copied from merged_hf)

Usage:
  python scripts/export_onnx.py
  make export-onnx

To test in lfm2-web after export:
  npx serve results/finetuned/export/onnx -p 3000
  Then set MODEL_ID = 'http://localhost:3000' in lfm2-web/index.html
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MERGED_MODEL = Path("results/finetuned/export/merged_hf")
DEFAULT_OUTPUT = Path("results/finetuned/export/onnx")


def run(cmd):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not MERGED_MODEL.exists():
        print(f"Error: merged model not found at {MERGED_MODEL}", file=sys.stderr)
        print("Run notebook 03_finetune.ipynb first.", file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    # Step 1: fp32 ONNX export via optimum
    print("\n[1/3] Exporting to ONNX (fp32)…")
    run([
        "optimum-cli", "export", "onnx",
        "--model", str(MERGED_MODEL),
        "--task", "text-generation-with-past",
        str(args.output),
    ])

    # Step 2: fp16
    print("\n[2/3] Converting to fp16…")
    try:
        import onnx
        from onnxconverter_common import float16
        m = onnx.load(str(args.output / "model.onnx"))
        onnx.save(float16.convert_float_to_float16(m), str(args.output / "model_fp16.onnx"))
        print("  model_fp16.onnx written")
    except ImportError:
        print("  Skipped — pip install onnx onnxconverter-common")

    # Step 3: int4 quantization
    print("\n[3/3] Quantizing to int4 (q4)…")
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType
        quantize_dynamic(
            str(args.output / "model.onnx"),
            str(args.output / "model_q4.onnx"),
            weight_type=QuantType.QInt4,
        )
        print("  model_q4.onnx written")
    except ImportError:
        print("  Skipped — pip install onnxruntime")
    except AttributeError:
        print("  Skipped — QInt4 requires onnxruntime >= 1.17")

    # Copy tokenizer + config
    print("\nCopying tokenizer files…")
    for f in MERGED_MODEL.iterdir():
        if f.suffix in (".json", ".jinja", ".txt"):
            shutil.copy2(f, args.output / f.name)

    print(f"\nDone. ONNX artifacts → {args.output}/")
    print("\nTo test:")
    print(f"  npx serve {args.output} -p 3000")
    print("  Set MODEL_ID = 'http://localhost:3000' in lfm2-web/index.html")


if __name__ == "__main__":
    main()
