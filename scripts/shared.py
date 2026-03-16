"""Shared utilities for scripts/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def render_template(template: str, replacements: dict[str, str]) -> str:
    output = template
    for key, value in replacements.items():
        output = output.replace(key, value)
    return output
