"""Generate docs/demo.html from results/examples.json."""

from __future__ import annotations

import json
from pathlib import Path

from shared import load_json, render_template

ROOT         = Path(__file__).parent.parent
EXAMPLES     = ROOT / "results" / "examples.json"
TEMPLATE     = ROOT / "scripts" / "templates" / "demo.html"
OUT          = ROOT / "docs" / "demo.html"


def main() -> None:
    examples = load_json(EXAMPLES) or []
    template = TEMPLATE.read_text()
    output = render_template(template, {"__EXAMPLES_JSON__": json.dumps(examples)})
    OUT.write_text(output)
    print(f"Written {OUT}")


if __name__ == "__main__":
    main()
