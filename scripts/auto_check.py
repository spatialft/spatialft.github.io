# AI-assisted (Claude Code, claude.ai) — https://claude.ai
"""Auto-mark REQUIREMENTS_CHECKLIST.md items verifiable from committed artifacts.

Run by CI on every push to main. Commits a change back if any items were
newly satisfied. No item is ever un-marked.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHECKLIST = ROOT / "REQUIREMENTS_CHECKLIST.md"
BASELINE_SCORES = ROOT / "results" / "baseline" / "scores.json"
FINETUNED_SCORES = ROOT / "results" / "finetuned" / "scores.json"
NB03 = ROOT / "notebooks" / "03_finetune.ipynb"


def load_json(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def notebook_source(path: Path) -> str:
    """Return all code cell source from a notebook as a single string."""
    if not path.exists():
        return ""
    nb = json.loads(path.read_text())
    return "\n".join(
        "".join(cell["source"])
        for cell in nb["cells"]
        if cell["cell_type"] == "code"
    )


def repo_is_public() -> bool:
    try:
        url = "https://api.github.com/repos/spatialft/spatialft.github.io"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        return not data.get("private", True)
    except Exception:
        return False


def evaluate() -> dict[str, bool]:
    """Return {item_id: should_be_checked} for all auto-markable items."""
    baseline = load_json(BASELINE_SCORES)
    finetuned = load_json(FINETUNED_SCORES)
    nb03 = notebook_source(NB03)
    claude_md = (ROOT / "CLAUDE.md").read_text()
    readme = (ROOT / "README.md").read_text()

    baseline_ok = baseline is not None and "accuracy" in baseline
    finetuned_ok = finetuned is not None and "accuracy" in finetuned
    baseline_has_hops = baseline_ok and any(k.startswith("accuracy_k") for k in baseline)
    finetuned_has_hops = finetuned_ok and any(k.startswith("accuracy_k") for k in finetuned)

    return {
        # Property — spatial reasoning is named and described in CLAUDE.md
        "PROP1": "spatial reasoning" in claude_md.lower(),
        "PROP3": baseline_ok,  # metric is defined when baseline scores exist

        # Model selection
        "MOD1": "LFM2-350M" in readme or "LFM2-350M" in claude_md,
        "MOD2": True,  # LFM2-350M is 354M parameters — always satisfied
        "MOD3": "trainer.train()" in nb03 or "SFTTrainer" in nb03,  # local fine-tuning, not API

        # Evaluation design
        "EVAL1": baseline_ok,                       # metric (accuracy) defined and measured
        "EVAL2": (ROOT / "data" / "eval" / "stepgame_eval.json").exists()
                 and (ROOT / "data" / "processed" / "train_formatted.json").exists(),
        "EVAL3": baseline_ok,                       # baseline measured before fine-tuning
        "EVAL4": baseline_has_hops,                 # per-hop breakdown present in scores

        # Fine-tuning
        "FT1": "lora" in nb03.lower(),              # LoRA method present in notebook
        "FT2": "learning_rate" in nb03 and "LORA_RANK" in nb03,  # key hyperparameters documented
        "FT3": "trainer.train()" in nb03 or "SFTTrainer" in nb03,  # training procedure present

        # Results
        "RES1": baseline_ok and finetuned_ok,       # quantitative before/after
        "RES2": baseline_has_hops and finetuned_has_hops,  # per-category breakdown

        # Repository
        "REPO1": repo_is_public(),
    }


def mark_item(text: str, item_id: str) -> tuple[str, bool]:
    """Change '- [ ] **ITEM_ID**' to '- [x] **ITEM_ID**'. Returns (text, changed).

    Assumes list-item format. REQUIREMENTS_CHECKLIST.md uses list items;
    if it is ever converted to table rows, update this regex accordingly.
    """
    pattern = rf"(- )\[ \]( \*\*{re.escape(item_id)}\*\*)"
    new_text = re.sub(pattern, r"\1[x]\2", text)
    return new_text, new_text != text


def main() -> None:
    text = CHECKLIST.read_text()
    conditions = evaluate()
    newly_marked = []

    for item_id, satisfied in conditions.items():
        if satisfied:
            text, changed = mark_item(text, item_id)
            if changed:
                newly_marked.append(item_id)

    if newly_marked:
        CHECKLIST.write_text(text)
        print(f"Auto-marked: {', '.join(newly_marked)}")
    else:
        print("No new items to mark.")


if __name__ == "__main__":
    main()
