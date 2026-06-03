#!/usr/bin/env bash
# Submit all URLs from the committed sitemap to IndexNow via Tower 1 POST /api/seo/indexnow.
#
# Usage (after fleet has deployed latest main):
#   bash sovereign/indexnow-submit-sitemap.sh
#
# Optional:
#   TOWER1_BASE=https://auroragalaxyrepublic.com
#   SITEMAP_PATH=/path/to/sitemap.xml
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${TOWER1_BASE:-https://auroragalaxyrepublic.com}"
BASE="${BASE%/}"
SITEMAP="${SITEMAP_PATH:-${ROOT}/aurora_server/static/sitemap.xml}"
TMP_PAYLOAD="$(mktemp)"
trap 'rm -f "$TMP_PAYLOAD"' EXIT

if [[ ! -f "$SITEMAP" ]]; then
  echo "indexnow-submit-sitemap: missing sitemap file: $SITEMAP" >&2
  exit 2
fi

export INDEXNOW_SITEMAP_PATH="$SITEMAP"
export INDEXNOW_PAYLOAD_PATH="$TMP_PAYLOAD"
python3 - <<'PY'
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

sitemap = Path(os.environ["INDEXNOW_SITEMAP_PATH"])
out = Path(os.environ["INDEXNOW_PAYLOAD_PATH"])
root = ET.parse(sitemap).getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
urls: list[str] = []
for el in root.findall("sm:url", ns):
    loc = el.find("sm:loc", ns)
    if loc is not None and (loc.text or "").strip():
        urls.append(loc.text.strip())
if not urls:
    for el in root.iter():
        if el.tag.endswith("loc") and el.text:
            t = el.text.strip()
            if t.startswith("http"):
                urls.append(t)

out.write_text(
    json.dumps({"host": "auroragalaxyrepublic.com", "urls": urls}),
    encoding="utf-8",
)
print(len(urls))
PY

n="$(python3 -c "import json; print(len(json.load(open('$TMP_PAYLOAD'))['urls']))")"
echo "[indexnow] sitemap=$SITEMAP urls=$n submit_via=${BASE}/api/seo/indexnow"

resp="$(curl -sS -w "\n%{http_code}" -X POST "${BASE}/api/seo/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary "@${TMP_PAYLOAD}" \
  --max-time 90)"
code="$(echo "$resp" | tail -n1)"
body="$(echo "$resp" | sed '$d')"
echo "$body"
[[ "$code" == "200" ]] || { echo "[indexnow] HTTP $code" >&2; exit 1; }
echo "[indexnow] OK"
