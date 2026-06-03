#!/usr/bin/env python3
"""
Build a cinematic UI baseline stylesheet and rollout map from aesthetic tokens.

Outputs:
  - /opt/agr/aurora_server/data/public_aesthetic_baseline.css
  - /opt/agr/aurora_server/data/public_cinematic_rollout.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

AURORA = Path(os.environ.get("AGR_BASE_DIR", "/opt/agr/aurora_server"))
DATA = AURORA / "data"
TOKENS = DATA / "republic_aesthetic_tokens.json"
MANIFEST = DATA / "public_aesthetic_manifest.json"
OUT_CSS = DATA / "public_aesthetic_baseline.css"
OUT_ROLLOUT = DATA / "public_cinematic_rollout.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def build_css(tokens: dict) -> str:
    palettes = tokens.get("palette_families", {})
    typo = tokens.get("typography", {}).get("tokens", {})

    lines = [
        "/* Aurora Republic Cinematic Baseline */",
        f"/* generated_at: {now_iso()} */",
        ":root {",
        f"  --agr-font-display: \"{typo.get('font_display', 'AGR-Ceremonial-Display')}\";",
        f"  --agr-font-ui: \"{typo.get('font_ui', 'AGR-Sovereign-Sans')}\";",
        f"  --agr-font-reading: \"{typo.get('font_reading', 'AGR-Scholarly-Serif')}\";",
        "  --agr-radius-lg: 18px;",
        "  --agr-radius-md: 12px;",
        "  --agr-shadow-cinematic: 0 20px 50px rgba(0, 0, 0, 0.35);",
        "}",
        "",
        "body[data-agr-cinematic='on'] {",
        "  font-family: var(--agr-font-ui), sans-serif;",
        "  background: var(--agr-bg, #090a10);",
        "  color: var(--agr-text, #eef6ff);",
        "}",
        "",
        "body[data-agr-cinematic='on'][data-agr-light='on'] {",
        "  background: radial-gradient(circle at 52% 18%, #ffffff 0%, #f6fbff 38%, #e9f3ff 70%, #d8e9ff 100%);",
        "  color: #10233e;",
        "}",
        "",
        "body[data-agr-cinematic='on'] .agr-surface {",
        "  background: var(--agr-surface, #111521);",
        "  border: 1px solid color-mix(in srgb, var(--agr-primary, #75e2ff) 40%, transparent);",
        "  border-radius: var(--agr-radius-lg);",
        "  box-shadow: var(--agr-shadow-cinematic);",
        "}",
        "",
        "body[data-agr-cinematic='on'][data-agr-light='on'] .agr-surface {",
        "  background: color-mix(in srgb, var(--agr-surface, #f7fbff) 88%, #ffffff 12%);",
        "  border: 1px solid color-mix(in srgb, var(--agr-primary, #4f87da) 30%, #ffffff 70%);",
        "  box-shadow: 0 20px 50px rgba(79, 135, 218, 0.18);",
        "}",
        "",
        "body[data-agr-cinematic='on'][data-agr-light='on'] .agr-hero-glow {",
        "  background: linear-gradient(140deg, rgba(255,255,255,0.95) 0%, rgba(139,197,255,0.25) 55%, rgba(79,135,218,0.18) 100%);",
        "  border: 1px solid rgba(139, 197, 255, 0.45);",
        "}",
        "",
    ]

    for family, row in palettes.items():
        colors = row.get("colors", {})
        lines.extend(
            [
                f"[data-agr-theme='{family}'] {{",
                f"  --agr-bg: {colors.get('bg', '#090a10')};",
                f"  --agr-surface: {colors.get('surface', '#111521')};",
                f"  --agr-primary: {colors.get('primary', '#75e2ff')};",
                f"  --agr-secondary: {colors.get('secondary', '#a6bcff')};",
                f"  --agr-accent: {colors.get('accent', '#d6f2ff')};",
                f"  --agr-text: {colors.get('text', '#eef6ff')};",
                "}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_rollout(tokens: dict, manifest: dict) -> dict:
    defaults = tokens.get("cluster_theme_defaults", {})
    entries = manifest.get("entries", [])
    pages = []
    for row in entries:
        cluster = row.get("cluster", "culture_archive")
        pages.append(
            {
                "page": row.get("page"),
                "cluster": cluster,
                "theme": row.get("theme_family", defaults.get(cluster, "lapis_meridian")),
                "audio_mode": row.get("audio_mode", "ambient_civic"),
                "cinematic_attr": "data-agr-cinematic='on'",
                "light_mode_attr": (
                    "data-agr-light='on'"
                    if row.get("theme_family", defaults.get(cluster, "lapis_meridian")) == "skyward_radiance"
                    else "data-agr-light='off'"
                ),
            }
        )
    return {
        "generated_at": now_iso(),
        "total_pages": len(pages),
        "default_font_policy": tokens.get("typography", {}).get("policy", "self-hosted-only"),
        "pages": pages,
    }


def main() -> None:
    if not TOKENS.exists():
        raise FileNotFoundError(f"Missing tokens file: {TOKENS}")
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Missing manifest file: {MANIFEST}")

    DATA.mkdir(parents=True, exist_ok=True)
    tokens = load_json(TOKENS)
    manifest = load_json(MANIFEST)

    css = build_css(tokens)
    rollout = build_rollout(tokens, manifest)

    OUT_CSS.write_text(css)
    OUT_ROLLOUT.write_text(json.dumps(rollout, indent=2))

    print(str(OUT_CSS))
    print(str(OUT_ROLLOUT))


if __name__ == "__main__":
    main()
