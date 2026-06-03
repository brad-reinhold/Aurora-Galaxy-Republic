#!/usr/bin/env python3
"""
Generate differentiated page aesthetic manifest from the design bible tokens.

Outputs:
  - /opt/agr/aurora_server/data/public_aesthetic_manifest.json
  - /opt/agr/aurora_server/data/public_aesthetic_manifest.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path


AURORA_SERVER = Path(os.environ.get("AGR_BASE_DIR", "/opt/agr/aurora_server"))
DATA_DIR = AURORA_SERVER / "data"
TOKENS_PATH = DATA_DIR / "republic_aesthetic_tokens.json"
OUT_JSON = DATA_DIR / "public_aesthetic_manifest.json"
OUT_MD = DATA_DIR / "public_aesthetic_manifest.md"


@dataclass(frozen=True)
class ClusterRule:
    name: str
    keywords: tuple[str, ...]


CLUSTER_RULES: tuple[ClusterRule, ...] = (
    ClusterRule("governance_law", ("governance", "law", "charter", "council", "assembly", "constitution", "declaration")),
    ClusterRule("citizen_identity", ("citizen", "account", "login", "profile", "totp", "security", "recover", "reset")),
    ClusterRule("production_media", ("studio", "production", "media", "builder", "digital_builder", "platform_studio", "video_forge")),
    ClusterRule("science_quantum_agi", ("quantum", "agi", "science", "research", "robotics", "consciousness", "space")),
    ClusterRule("culture_archive", ("archive", "art", "museum", "literature", "philosophy", "poetry", "sacred")),
    ClusterRule("security_operations", ("sentinel", "attack", "adversary", "audit", "ops", "command_center")),
    ClusterRule("commerce_finance", ("market", "finance", "pricing", "economy", "subscription")),
    ClusterRule("social_comms", ("chat", "social", "comms", "video_chat", "holographic", "voice")),
    ClusterRule("ceremonial", ("oath", "creed", "lumen", "tower", "constellation", "academy")),
)


def load_tokens() -> dict:
    if not TOKENS_PATH.exists():
        raise FileNotFoundError(f"Token file missing: {TOKENS_PATH}")
    return json.loads(TOKENS_PATH.read_text())


def detect_cluster(page_name: str) -> str:
    n = page_name.lower()
    for rule in CLUSTER_RULES:
        if any(k in n for k in rule.keywords):
            return rule.name
    return "culture_archive"


def build_manifest(tokens: dict) -> dict:
    defaults = tokens["cluster_theme_defaults"]
    palettes = tokens["palette_families"]
    html_pages = sorted(p.name for p in AURORA_SERVER.glob("*.html"))
    entries = []
    counts: dict[str, int] = {}

    for page in html_pages:
        cluster = detect_cluster(page)
        theme = defaults.get(cluster, "lapis_meridian")
        counts[cluster] = counts.get(cluster, 0) + 1
        entries.append(
            {
                "page": page,
                "cluster": cluster,
                "theme_family": theme,
                "theme_colors": palettes[theme]["colors"],
                "materials": palettes[theme]["materials"],
                "audio_mode": (
                    "governance_chamber" if cluster == "governance_law"
                    else "studio_focus" if cluster == "production_media"
                    else "cinematic_ceremony" if cluster == "ceremonial"
                    else "ambient_civic"
                ),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_pages": len(html_pages),
        "cluster_counts": counts,
        "typography": tokens["typography"]["tokens"],
        "entries": entries,
    }


def write_outputs(manifest: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, indent=2))

    lines = [
        "# Public Aesthetic Manifest",
        f"Generated: {manifest['generated_at']}",
        f"Total Pages: {manifest['total_pages']}",
        "",
        "## Cluster Counts",
    ]
    for cluster, count in sorted(manifest["cluster_counts"].items()):
        lines.append(f"- {cluster}: {count}")
    lines.extend(["", "## Page Assignments"])
    for row in manifest["entries"]:
        lines.append(f"- {row['page']}: {row['cluster']} -> {row['theme_family']} ({row['audio_mode']})")
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    tokens = load_tokens()
    manifest = build_manifest(tokens)
    write_outputs(manifest)
    print(str(OUT_JSON))
    print(str(OUT_MD))


if __name__ == "__main__":
    main()

