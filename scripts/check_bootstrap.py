"""Check that notebook bootstrap cells share the same clone/path logic."""

import json
import sys
from pathlib import Path

NOTEBOOKS = sorted(Path("notebooks").glob("*.ipynb"))
# The bootstrap block: everything before the first `from src.` import
SPLIT_MARKER = "from src."


def extract_bootstrap(nb_path: Path) -> str:
    with open(nb_path) as f:
        cells = json.load(f)["cells"]
    # First code cell (skip leading markdown)
    for cell in cells:
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            # Keep only the lines before the colab_utils import
            lines = []
            for line in source.splitlines():
                if line.startswith(SPLIT_MARKER):
                    break
                lines.append(line)
            return "\n".join(lines)
    return ""


def main() -> None:
    if len(NOTEBOOKS) < 2:
        print("Fewer than 2 notebooks found, nothing to compare.")
        return

    bootstraps = [(nb, extract_bootstrap(nb)) for nb in NOTEBOOKS]
    ref_nb, ref_src = bootstraps[0]
    drifted = [nb for nb, src in bootstraps[1:] if src != ref_src]

    if drifted:
        print(f"Bootstrap drift detected vs {ref_nb}:")
        for nb in drifted:
            print(f"  {nb}")
        sys.exit(1)
    else:
        print(f"All {len(NOTEBOOKS)} notebook bootstrap cells are in sync.")


if __name__ == "__main__":
    main()
