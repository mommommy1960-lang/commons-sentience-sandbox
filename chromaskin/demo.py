"""Render a measured room theme as a deterministic SVG proof of concept."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from xml.sax.saxutils import escape


def render_theme(panels: list[dict], theme: str = "snow-window") -> str:
    """Map one virtual scene across nonoverlapping rectangular panel coordinates."""
    if not panels:
        raise ValueError("At least one panel is required")
    if theme not in {"snow-window", "fireplace"}:
        raise ValueError("Unknown theme")
    occupied = []
    for panel in panels:
        if not isinstance(panel.get("name"), str) or not panel["name"]:
            raise ValueError("Each panel needs a name")
        values = [panel.get(key) for key in ("x", "y", "width", "height")]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError("Panel coordinates must be finite numbers")
        x, y, w, h = values
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            raise ValueError("Panel coordinates must be positive")
        rect = (x, y, x + w, y + h)
        for other in occupied:
            if max(rect[0], other[0]) < min(rect[2], other[2]) and max(rect[1], other[1]) < min(rect[3], other[3]):
                raise ValueError("Panels overlap")
        occupied.append(rect)

    width = max(rect[2] for rect in occupied)
    height = max(rect[3] for rect in occupied)
    if width > 10000 or height > 10000:
        raise ValueError("Demo canvas exceeds limit")
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}">',
             '<defs>']
    if theme == "snow-window":
        lines.append('<linearGradient id="scene" x2="0" y2="1"><stop stop-color="#305c82"/><stop offset="1" stop-color="#c9e4ef"/></linearGradient>')
    else:
        lines.append('<linearGradient id="scene" x2="0" y2="1"><stop stop-color="#361f28"/><stop offset="1" stop-color="#e88a35"/></linearGradient>')
    lines.append('</defs>')
    for index, (panel, rect) in enumerate(zip(panels, occupied)):
        x, y, right, bottom = rect
        name = escape(panel["name"], {'"': '&quot;'})
        lines.append(f'<clipPath id="panel-{index}"><rect x="{x:g}" y="{y:g}" width="{right-x:g}" height="{bottom-y:g}"/></clipPath>')
        lines.append(f'<g clip-path="url(#panel-{index})" data-panel="{name}">')
        lines.append(f'<rect width="{width:g}" height="{height:g}" fill="url(#scene)"/>')
        if theme == "snow-window":
            for i in range(55):
                sx = (i * 89 + 23) % int(math.ceil(width))
                sy = (i * 53 + 11) % int(math.ceil(height))
                lines.append(f'<circle cx="{sx}" cy="{sy}" r="2" fill="#fff"/>')
        else:
            lines.append(f'<path d="M 0 {height:g} Q {width*.25:g} {height*.18:g} {width*.5:g} {height*.7:g} T {width:g} {height*.12:g} L {width:g} {height:g} Z" fill="#ffca64"/>')
        lines.append('</g>')
        lines.append(f'<rect x="{x:g}" y="{y:g}" width="{right-x:g}" height="{bottom-y:g}" fill="none" stroke="#fff" stroke-width="2"/>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("snow-window", "fireplace"), default="snow-window")
    parser.add_argument("--output", type=Path, default=Path("chromaskin-demo.svg"))
    args = parser.parse_args()
    panels = [
        {"name": "wall-left", "x": 0, "y": 0, "width": 320, "height": 240},
        {"name": "wall-right", "x": 320, "y": 0, "width": 320, "height": 240},
    ]
    args.output.write_text(render_theme(panels, args.theme), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
