# AI-assisted (Claude Code, claude.ai) — https://claude.ai
"""Parse REQUIREMENTS_CHECKLIST.md and write docs/checklist/index.html."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "REQUIREMENTS_CHECKLIST.md"
OUT = ROOT / "docs" / "checklist" / "index.html"

GH = "https://github.com/spatialft/spatialft.github.io/blob/main"

# (description, url) for each item — shown as tooltip on hover.
# url=None for items with no single concrete link.
SOURCES: dict[str, tuple[str, str | None]] = {
    "PROP1": ("Defined in CLAUDE.md — spatial reasoning as the target property", f"{GH}/CLAUDE.md"),
    "PROP2": ("Justified in docs/slides.md — motivation section", f"{GH}/docs/slides.md"),
    "PROP3": ("src/eval.py — accuracy over 8 spatial directions", f"{GH}/src/eval.py"),
    "LIT1":  ("docs/references.md — cited papers", f"{GH}/docs/references.md"),
    "LIT2":  ("docs/slides.md — literature review section", f"{GH}/docs/slides.md"),
    "MOD1":  ("CLAUDE.md + README — LFM2.5-1.2B-Thinking selected and justified", f"{GH}/README.md"),
    "MOD2":  ("LFM2.5-1.2B is 1.2B parameters — always satisfied", f"{GH}/CLAUDE.md"),
    "MOD3":  ("notebooks/03_finetune.ipynb — local SFTTrainer, no API", f"{GH}/notebooks/03_finetune.ipynb"),
    "EVAL1": ("results/baseline/scores.json — accuracy key present", f"{GH}/results/baseline/scores.json"),
    "EVAL2": ("notebooks/02_dataset_prep.ipynb — ZhengyanShi/StepGame train vs validation splits", f"{GH}/notebooks/02_dataset_prep.ipynb"),
    "EVAL3": ("results/baseline/scores.json — baseline measured before fine-tuning", f"{GH}/results/baseline/scores.json"),
    "EVAL4": ("results/baseline/scores.json — accuracy_k{{n}} keys per hop level", f"{GH}/results/baseline/scores.json"),
    "FT1":   ("notebooks/03_finetune.ipynb — LoRA via SFTTrainer, r=16", f"{GH}/notebooks/03_finetune.ipynb"),
    "FT2":   ("notebooks/03_finetune.ipynb — LORA_RANK=16, lr=2e-4, batch=4, epochs=3", f"{GH}/notebooks/03_finetune.ipynb"),
    "FT3":   ("notebooks/03_finetune.ipynb — SFTTrainer.train() with full config", f"{GH}/notebooks/03_finetune.ipynb"),
    "RES1":  ("results/baseline/scores.json + results/finetuned/scores.json", f"{GH}/results"),
    "RES2":  ("notebooks/04_eval_comparison.ipynb — per-hop accuracy chart", f"{GH}/notebooks/04_eval_comparison.ipynb"),
    "RES3":  ("notebooks/04_eval_comparison.ipynb — analysis section", f"{GH}/notebooks/04_eval_comparison.ipynb"),
    "RES4":  ("docs/slides.md — conclusions section", f"{GH}/docs/slides.md"),
    "RES5":  ("docs/slides.md — failure analysis if no improvement", f"{GH}/docs/slides.md"),
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
        m = re.match(r"^## (.+)", line)
        if m:
            current = {"title": m.group(1).strip(), "items": []}
            sections.append(current)
            continue

        if current is None:
            continue

        # Table row:  | ID | description | anything | ✅/⬜ |
        m = re.match(
            r"^\|\s*([A-Z]+\d+)\s*\|(.+?)\|.*?\|\s*(✅|⬜)\s*\|", line
        )
        if m:
            item_id, label, status = m.groups()
            current["items"].append(
                {"id": item_id.strip(), "label": _clean(label), "done": status == "✅"}
            )
            continue

        # List item:  - [x] **ID** — description
        m = re.match(r"^-\s+\[(x| )\]\s+\*\*([A-Z]+\d+)\*\*\s*[—–-]?\s*(.+)", line)
        if m:
            checked, item_id, label = m.groups()
            current["items"].append(
                {"id": item_id.strip(), "label": _clean(label), "done": checked == "x"}
            )

    return [s for s in sections if s["items"]]


def _clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip(" —–-")


def _progress(items: list[dict]) -> tuple[int, int]:
    done = sum(1 for i in items if i["done"])
    return done, len(items)


def _source_attrs(item_id: str) -> tuple[str, bool]:
    """Return (extra HTML attributes string, has_source)."""
    if item_id not in SOURCES:
        return "", False
    text, url = SOURCES[item_id]
    escaped_text = html.escape(text, quote=True)
    url_attr = f' data-src-url="{url}"' if url else ""
    return f' data-src="{escaped_text}"{url_attr}', True


def render_html(sections: list[dict], generated_at: str) -> str:
    total_done = sum(i["done"] for s in sections for i in s["items"])
    total_all = sum(len(s["items"]) for s in sections)
    total_pct = round(100 * total_done / total_all) if total_all else 0

    section_html = ""
    for sec in sections:
        done, total = _progress(sec["items"])
        pct = round(100 * done / total) if total else 0

        rows = ""
        for item in sec["items"]:
            status_cls = "done" if item["done"] else "open"
            glyph = "✓" if item["done"] else "○"
            src_attrs, has_source = _source_attrs(item["id"])
            cls = f"{status_cls} has-source" if has_source else status_cls
            rows += (
                f'<tr class="{cls}"{src_attrs}>'
                f'<td class="item-glyph">{glyph}</td>'
                f'<td class="item-id">{item["id"]}</td>'
                f'<td class="item-label">{item["label"]}</td>'
                f"</tr>\n"
            )

        section_html += f"""
    <section class="checklist-section">
      <div class="section-header">
        <h2>{sec['title']}</h2>
        <span class="section-count">{done}/{total}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
      <table class="item-table">
        <tbody>{rows}</tbody>
      </table>
    </section>
"""

    return f"""<!-- AUTO-GENERATED — edit REQUIREMENTS_CHECKLIST.md, not this file -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Requirements Checklist — AIPI 590 Project 1</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #f8f7f4; --surface: #ffffff; --border: #e5e2db;
      --text: #1a1916; --text-muted: #6b6860;
      --green: #16a34a; --green-bg: #f0fdf4;
      --accent: #2563eb;
      --radius-sm: 6px; --radius-md: 12px;
      --shadow-sm: 0 1px 3px rgba(0,0,0,.07);
      --font: 'Inter', system-ui, -apple-system, sans-serif;
    }}
    html {{ font-size: 16px; -webkit-font-smoothing: antialiased; }}
    body {{ font-family: var(--font); background: var(--bg); color: var(--text); min-height: 100dvh; }}
    a {{ color: inherit; }}
    .container {{ width: 100%; max-width: 780px; margin: 0 auto; padding: 0 24px; }}

    .site-header {{ border-bottom: 1px solid var(--border); padding: 20px 0; background: var(--surface); }}
    .site-header .container {{ display: flex; align-items: center; gap: 16px; }}
    .back-link {{ font-size: 0.85rem; color: var(--text-muted); text-decoration: none; }}
    .back-link:hover {{ color: var(--text); }}
    .header-title {{ font-size: 1rem; font-weight: 600; }}

    .overall {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
      padding: 24px; margin: 32px 0 24px; box-shadow: var(--shadow-sm); }}
    .overall-row {{ display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }}
    .overall-pct {{ font-size: 2rem; font-weight: 700; }}
    .overall-label {{ font-size: 0.9rem; color: var(--text-muted); }}
    .progress-bar {{ height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; margin-top: 4px; }}
    .progress-fill {{ height: 100%; background: var(--green); border-radius: 4px; transition: width .3s; }}

    .checklist-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
      padding: 20px 24px; margin-bottom: 16px; box-shadow: var(--shadow-sm); }}
    .section-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }}
    .section-header h2 {{ font-size: 0.95rem; font-weight: 600; }}
    .section-count {{ font-size: 0.8rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }}
    .checklist-section .progress-bar {{ margin-bottom: 16px; }}

    .item-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .item-table tr {{ border-top: 1px solid var(--border); position: relative; }}
    .item-table tr:first-child {{ border-top: none; }}
    .item-table td {{ padding: 7px 4px; vertical-align: top; }}
    .item-glyph {{ width: 20px; color: var(--text-muted); font-size: 0.75rem; padding-top: 8px; }}
    .item-id {{ width: 64px; font-weight: 600; font-size: 0.78rem; white-space: nowrap; padding-top: 8px; }}
    .item-label {{ color: var(--text-muted); line-height: 1.45; }}
    tr.done .item-glyph {{ color: var(--green); }}
    tr.done .item-id {{ color: var(--text); }}
    tr.done .item-label {{ color: var(--text); }}
    tr.has-source {{ cursor: default; }}

    /* Tooltip */
    .tooltip {{
      display: none;
      position: fixed;
      z-index: 100;
      background: #1a1916;
      color: #f5f4f1;
      font-size: 0.78rem;
      line-height: 1.5;
      padding: 8px 12px;
      border-radius: 6px;
      max-width: 320px;
      box-shadow: 0 4px 16px rgba(0,0,0,.25);
    }}
    .tooltip.visible {{ display: block; }}
    .tooltip a {{
      display: inline-block;
      margin-top: 4px;
      color: #93c5fd;
      text-decoration: underline;
    }}

    .page-footer {{ text-align: center; font-size: 0.8rem; color: var(--text-muted); padding: 32px 0 48px; }}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a class="back-link" href="../">← AIPI 590 Project 1</a>
      <span class="header-title">Requirements Checklist</span>
    </div>
  </header>

  <div id="tooltip" class="tooltip"></div>

  <main style="padding-bottom: 48px;">
    <div class="container">
      <div class="overall">
        <div class="overall-row">
          <span class="overall-pct">{total_pct}%</span>
          <span class="overall-label">{total_done} of {total_all} items complete</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:{total_pct}%"></div></div>
      </div>
      {section_html}
    </div>
  </main>

  <footer class="page-footer">
    Auto-generated from <code>REQUIREMENTS_CHECKLIST.md</code> · {generated_at}
  </footer>

  <script>
    const tip = document.getElementById('tooltip');
    let hideTimer;

    document.querySelectorAll('tr.has-source').forEach(row => {{
      const text = row.dataset.src;
      const url  = row.dataset.srcUrl;

      row.addEventListener('mouseenter', () => {{
        clearTimeout(hideTimer);
        tip.innerHTML = url
          ? `${{text}}<br><a href="${{url}}" target="_blank" rel="noopener noreferrer">Open ↗</a>`
          : text;
        tip.classList.add('visible');
        position(row);
      }});

      row.addEventListener('mouseleave', () => {{
        hideTimer = setTimeout(() => tip.classList.remove('visible'), 200);
      }});
    }});

    tip.addEventListener('mouseenter', () => clearTimeout(hideTimer));
    tip.addEventListener('mouseleave', () => tip.classList.remove('visible'));

    function position(row) {{
      const pad = 8;
      const rect = row.getBoundingClientRect();
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      let x = rect.right + pad;
      let y = rect.top;
      if (x + tw > window.innerWidth - pad) x = rect.left - tw - pad;
      if (y + th > window.innerHeight - pad) y = window.innerHeight - th - pad;
      tip.style.left = x + 'px';
      tip.style.top  = y + 'px';
    }}
  </script>
</body>
</html>
"""


def main() -> None:
    text = SOURCE.read_text()
    sections = parse_checklist(text)
    if not sections:
        raise SystemExit(f"ERROR: no items parsed from {SOURCE} — check the format")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = render_html(sections, generated_at)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"Written → {OUT}")


if __name__ == "__main__":
    main()
