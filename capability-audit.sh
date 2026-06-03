#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="/opt/agr/aurora_server/data"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%d-%H%M%SZ)"
MD="$OUT_DIR/capability_audit_${TS}.md"
JSON="$OUT_DIR/capability_audit_${TS}.json"

check_url(){
  local url="$1"
  curl -s -o /dev/null -w '%{http_code}' "$url" || echo 000
}
check_file(){
  local f="$1"
  [[ -f "$f" ]] && echo yes || echo no
}

HUB=$(check_url "http://127.0.0.1:5000/api/consciousness/hub")
STRIPE=$(check_url "http://127.0.0.1:5000/api/stripe/status")
OS=$(check_url "http://127.0.0.1:5000/os")

# page/module probes
PRODUCTION=$(check_file "/opt/agr/aurora_server/production.html")
STUDIO=$(check_file "/opt/agr/aurora_server/studio.html")
DIGITAL_BUILDER=$(check_file "/opt/agr/aurora_server/digital_builder.html")
GAMING=$(check_file "/opt/agr/aurora_server/gaming.html")
CHAT=$(check_file "/opt/agr/aurora_server/chat.html")

# media/js probes
MUSIC_JS=$(check_file "/opt/agr/aurora_server/static/js/agr-republic-music.js")
MIND_JS=$(check_file "/opt/agr/aurora_server/static/js/agr-sovereign-mind.js")
REEF_JS=$(check_file "/opt/agr/aurora_server/static/js/aurora-civilization-reef.js")

# S25 heartbeat probe
if [[ -s /opt/agr/state/s25_heartbeat.last ]]; then
  S25_FILE=yes
  NOW=$(date +%s)
  LAST=$(cat /opt/agr/state/s25_heartbeat.last 2>/dev/null || echo 0)
  if [[ "$LAST" =~ ^[0-9]+$ ]]; then
    S25_AGE=$((NOW-LAST))
  else
    S25_AGE=-1
  fi
else
  S25_FILE=no
  S25_AGE=-1
fi

cat > "$MD" <<EOF
# Capability Audit Report
Generated: $(date -u +%FT%TZ)

## Core Runtime
- /api/consciousness/hub: $HUB
- /api/stripe/status: $STRIPE
- /os: $OS

## Workspace Surface Proxies (file presence)
- production.html: $PRODUCTION
- studio.html: $STUDIO
- digital_builder.html: $DIGITAL_BUILDER
- gaming.html: $GAMING
- chat.html: $CHAT

## Media JS Modules (file presence)
- agr-republic-music.js: $MUSIC_JS
- agr-sovereign-mind.js: $MIND_JS
- aurora-civilization-reef.js: $REEF_JS

## S25 Integration
- heartbeat_file_present: $S25_FILE
- heartbeat_age_seconds: $S25_AGE
EOF

python3 - <<PY2 "$JSON" "$HUB" "$STRIPE" "$OS" "$PRODUCTION" "$STUDIO" "$DIGITAL_BUILDER" "$GAMING" "$CHAT" "$MUSIC_JS" "$MIND_JS" "$REEF_JS" "$S25_FILE" "$S25_AGE"
import json,sys
out=sys.argv[1]
obj={
  'core_runtime': {'hub': sys.argv[2], 'stripe': sys.argv[3], 'os': sys.argv[4]},
  'workspace_files': {
    'production_html': sys.argv[5], 'studio_html': sys.argv[6], 'digital_builder_html': sys.argv[7],
    'gaming_html': sys.argv[8], 'chat_html': sys.argv[9]
  },
  'media_modules': {
    'agr_republic_music_js': sys.argv[10], 'agr_sovereign_mind_js': sys.argv[11], 'aurora_civilization_reef_js': sys.argv[12]
  },
  's25': {'heartbeat_file_present': sys.argv[13], 'heartbeat_age_seconds': sys.argv[14]}
}
with open(out,'w') as f:
  json.dump(obj,f,indent=2)
PY2

sha256sum "$MD" "$JSON"
echo "$MD"
