# AI-assisted (Claude Code, claude.ai) — https://claude.ai
"""Parse REQUIREMENTS_CHECKLIST.md and write docs/checklist/index.html."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path

from shared import render_template

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "REQUIREMENTS_CHECKLIST.md"
OUT = ROOT / "docs" / "checklist" / "index.html"
TEMPLATE = ROOT / "scripts" / "templates" / "checklist.html"

GH = "https://github.com/spatialft/spatialft.github.io/blob/main"

# (description, url) for each item — shown as tooltip on hover.
# url=None for items with no single concrete link.
SOURCES: dict[str, tuple[str, str | None]] = {
    "PROP1": ("Defined in CLAUDE.md — spatial reasoning as the target property", f"{GH}/CLAUDE.md"),
    "PROP2": ("Justified in docs/slides.md — motivation section", f"{GH}/docs/slides.md"),
    "PROP3": ("src/eval.py — accuracy over 8 spatial directions", f"{GH}/src/eval.py"),
    "LIT1": ("docs/references.md — cited papers", f"{GH}/docs/references.md"),
    "LIT2": ("docs/slides.md — literature review section", f"{GH}/docs/slides.md"),
    "MOD1": ("CLAUDE.md + README — LFM2-350M selected and justified", f"{GH}/README.md"),
    "MOD2": ("LFM2-350M is 354M parameters — always satisfied", f"{GH}/CLAUDE.md"),
    "MOD3": ("notebooks/03_finetune.ipynb — local SFTTrainer, no API", f"{GH}/notebooks/03_finetune.ipynb"),
    "EVAL1": ("results/baseline/scores.json — accuracy key present", f"{GH}/results/baseline/scores.json"),
    # HuggingFace dataset is ZhengyanShi/StepGame; GitHub repo is ZhengxiangShi/StepGame (different platform usernames, same dataset)
    "EVAL2": ("notebooks/02_dataset_prep.ipynb — ZhengyanShi/StepGame (HF) train vs validation splits", f"{GH}/notebooks/02_dataset_prep.ipynb"),
    "EVAL3": ("results/baseline/scores.json — baseline measured before fine-tuning", f"{GH}/results/baseline/scores.json"),
    "EVAL4": ("results/baseline/scores.json — accuracy_k{n} keys per hop level", f"{GH}/results/baseline/scores.json"),
    "FT1": ("notebooks/03_finetune.ipynb — LoRA via SFTTrainer, r=16", f"{GH}/notebooks/03_finetune.ipynb"),
    "FT2": ("notebooks/03_finetune.ipynb — LORA_RANK=16, lr=2e-4, batch=4, epochs=3", f"{GH}/notebooks/03_finetune.ipynb"),
    "FT3": ("notebooks/03_finetune.ipynb — SFTTrainer.train() with full config", f"{GH}/notebooks/03_finetune.ipynb"),
    "RES1": ("results/baseline/scores.json + results/finetuned/scores.json", f"{GH}/results"),
    "RES2": ("notebooks/04_eval_comparison.ipynb — per-hop accuracy chart", f"{GH}/notebooks/04_eval_comparison.ipynb"),
    "RES3": ("notebooks/04_eval_comparison.ipynb — analysis section", f"{GH}/notebooks/04_eval_comparison.ipynb"),
    "RES4": ("docs/slides.md — conclusions section", f"{GH}/docs/slides.md"),
    "RES5": ("docs/slides.md — failure analysis if no improvement", f"{GH}/docs/slides.md"),
    "PRES1": ("docs/slides.md — property and motivation slide", f"{GH}/docs/slides.md"),
    "PRES2": ("docs/slides.md — literature review slide", f"{GH}/docs/slides.md"),
    "PRES3": ("docs/slides.md — model and dataset slide", f"{GH}/docs/slides.md"),
    "PRES4": ("spatialft.github.io — live results page with charts", "https://spatialft.github.io/"),
    "PRES5": ("docs/slides.md — methodology and lessons learned", f"{GH}/docs/slides.md"),
    "PRES6": ("docs/slides.md — verify no code blocks", f"{GH}/docs/slides.md"),
    "PRES7": ("docs/slides.md", f"{GH}/docs/slides.md"),
    "PRES8": ("docs/speaker-notes.md — timing notes", f"{GH}/docs/speaker-notes.md"),
    "PRES9": ("docs/speaker-notes.md — Q&A preparation", f"{GH}/docs/speaker-notes.md"),
    "REPO1": ("github.com/spatialft/spatialft.github.io — public repository", "https://github.com/spatialft/spatialft.github.io"),
    "REPO2": ("github.com/spatialft/spatialft.github.io — code matches presentation", "https://github.com/spatialft/spatialft.github.io"),
    "REPO3": ("spatialft.github.io — live project portfolio page", "https://spatialft.github.io/"),
}


def parse_checklist(text: str) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None

    for line in text.splitlines():
        section_match = re.match(r"^## (.+)", line)
        if section_match:
            current = {"title": section_match.group(1).strip(), "items": []}
            sections.append(current)
            continue

        if current is None:
            continue

        table_match = re.match(r"^\|\s*([A-Z]+\d+)\s*\|(.+?)\|.*?\|\s*(✅|⬜)\s*\|", line)
        if table_match:
            item_id, label, status = table_match.groups()
            current["items"].append({"id": item_id.strip(), "label": clean(label), "done": status == "✅"})
            continue

        list_match = re.match(r"^-\s+\[(x| )\]\s+\*\*([A-Z]+\d+)\*\*\s*[—–-]?\s*(.+)", line)
        if list_match:
            checked, item_id, label = list_match.groups()
            current["items"].append({"id": item_id.strip(), "label": clean(label), "done": checked == "x"})

    return [section for section in sections if section["items"]]


def clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip(" —–-")


def progress(items: list[dict]) -> tuple[int, int]:
    done = sum(1 for item in items if item["done"])
    return done, len(items)


def source_attrs(item_id: str) -> tuple[str, bool]:
    if item_id not in SOURCES:
        return "", False
    text, url = SOURCES[item_id]
    escaped_text = html.escape(text, quote=True)
    url_attr = f' data-src-url="{html.escape(url, quote=True)}"' if url else ""
    return f' data-src="{escaped_text}"{url_attr}', True


def render_sections(sections: list[dict]) -> str:
    html_sections = []
    for section in sections:
        done, total = progress(section["items"])
        pct = round(100 * done / total) if total else 0

        rows = []
        for item in section["items"]:
            status_cls = "done" if item["done"] else "open"
            glyph = "✓" if item["done"] else "○"
            attrs, has_source = source_attrs(item["id"])
            row_class = f"{status_cls} has-source" if has_source else status_cls
            rows.append(
                f'<tr class="{row_class}"{attrs}>'
                f'<td class="item-glyph">{glyph}</td>'
                f'<td class="item-id">{item["id"]}</td>'
                f'<td class="item-label">{html.escape(item["label"])}</td>'
                "</tr>"
            )

        html_sections.append(
            f"""
    <section class="checklist-section">
      <div class="section-header">
        <h2>{html.escape(section['title'])}</h2>
        <span class="section-count">{done}/{total}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
      <table class="item-table">
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
"""
        )

    return "".join(html_sections)


def render_html(sections: list[dict], generated_at: str) -> str:
    total_done = sum(item["done"] for section in sections for item in section["items"])
    total_all = sum(len(section["items"]) for section in sections)
    total_pct = round(100 * total_done / total_all) if total_all else 0
    template = TEMPLATE.read_text()
    return render_template(
        template,
        {
            "__TOTAL_PCT__": str(total_pct),
            "__TOTAL_DONE__": str(total_done),
            "__TOTAL_ALL__": str(total_all),
            "__SECTION_HTML__": render_sections(sections),
            "__GENERATED_AT__": generated_at,
        },
    )


def main() -> None:
    text = SOURCE.read_text()
    sections = parse_checklist(text)
    if not sections:
        raise SystemExit(f"ERROR: no items parsed from {SOURCE} — check the format")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    output = render_html(sections, generated_at)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(output)
    print(f"Written → {OUT}")


if __name__ == "__main__":
    main()
