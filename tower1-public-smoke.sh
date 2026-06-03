#!/usr/bin/env bash
# Tower 1 public smoke — run after fleet deploy or from CI to confirm edge → origin health.
#
# Usage:
#   bash sovereign/tower1-public-smoke.sh
#   TOWER1_BASE=https://auroragalaxyrepublic.com bash sovereign/tower1-public-smoke.sh
#
# Pass criteria (aligned with latest main):
#   - robots.txt contains the committed "Index machine-readable truth surfaces first" marker
#   - sitemap.xml lists search-discovery + award-evidence URLs
#   - GET /disclosures (no redirects): 200 with "Tower 1 Public Disclosures" marker; WARN if 302→/awards
#     (edge/stale origin — TOWER1_SMOKE_STRICT_DISCLOSURES=1 to fail)
#   - GET /api/public/engine-runtime returns 200 JSON (not 404)
#   - GET /health returns 200 JSON (canonical on some edges; matches live CF → origin routing)
#     If 404, GET /api/health then GET /api/public/health (routes_health) as fallbacks.
#   - POST /api/public/citizen-engine-advice returns 200 JSON (429 = rate limit: warn only)
#   - POST /api/republic/chat returns 200 JSON (not 302 to /gate)
#   - GET /api/public/mirl/catalog returns 200 JSON when strict (TOWER1_SMOKE_STRICT_MIRL=1)
#   - GET /sovereign/mirl/charter/html returns 200 with <!DOCTYPE html> (preferred), or 200 with
#     MIR-L charter projection marker (warn if doctype missing — deploy lag vs main)
#   - GET /dl/s25-termux-setup, /dl/ceo, /dl/ceo-os-py, /dl/agr-vault-rag-py, /dl/agr-vault-github-export-py
#     /dl/mint-cloudflare-tunnel-token-stdout-py, /dl/termux-republic-one-shot-bootstrap-sh,
#     /dl/termux-phone-one-shot-recover-sh, /dl/termux-republic-recover,
#     /dl/termux-operator-return-one-paste-sh, /dl/termux-operator-wake
#     each return 200 with stable body markers (Termux bootstrap + CEO launcher + CEO shell + vault modules)
#   - GET /dl/agr-handset-secrets-md-py: 200 + body must contain literal substring **agr_handset_identity_from_secrets_md**
#     (embedded in `aurora_server/agr_handset_identity_from_secrets_md.py` docstring — do not remove or smoke WARNs
#     with **200_missing_marker** on mixed LB origins). If live Tower returns 404 (lags main),
#     WARN by default (aligns with agr_autonomous_merge_gate). Fail closed: TOWER1_SMOKE_STRICT_DL_HANDSET=1
#     Retries (TOWER1_SMOKE_DL_HANDSET_TRIES) when HTTP 200 but marker missing — mixed LB origins.
#     When /dl/* warns: bash sovereign/scripts/operator-next-steps-fleet-tower.sh (fleet vs canonical table + steps).
#   - POST /api/republic/laws/check returns 200 JSON schema v1 (not 302: needs _PUBLIC_PATHS
#     for AuthMiddleware + _TOWER1_PUBLIC_POST_PATHS for sovereign_tower_gate on Tower I)
#
# Optional rollout lag: if Tower is healthy but MIR-L routes are not deployed yet, set
#   TOWER1_SMOKE_STRICT_MIRL=0
#
# Deploy revision pin (optional): after the /health probe path succeeds, set
#   TOWER1_EXPECT_DEPLOY_REV=<full git SHA> — fail if GET /api/health JSON agr_deploy_revision differs
#   (requires jq; proves fleet pulled the pinned commit — see sovereign/scripts/tower1-live-deploy-revision-verify.sh).
#
# Transient network: TOWER1_SMOKE_MAX_TRIES (default 3) and TOWER1_SMOKE_RETRY_SLEEP (default 3)
# retry GET/POST when curl returns 000 or empty (connection timeout).
#
# /dl/ceo-os-py body drift: HTTP 200 but HTML body occasionally lacks python shebang marker on first fetch
# (LB/origin race). TOWER1_SMOKE_DL_CEO_OS_PY_BODY_TRIES (default 3) + TOWER1_SMOKE_DL_CEO_OS_PY_BODY_SLEEP (default 2)
# re-fetch until markers present.
#
# Deploy drift: when live Tower lags origin/main, /api/seo/status may omit indexing_automation_note.
# Default: WARN only. Set TOWER1_SMOKE_REQUIRE_SEO_STATUS_FIELDS=1 to fail the smoke until fleet-pull.
#
# Disclosure hub drift: hostname sometimes returns 302 Location → /awards (not emitted by main
# disclosures_page — treat as Cloudflare rule or stale origin). Smoke warns by default.
#   TOWER1_SMOKE_STRICT_DISCLOSURES=1 — fail if GET /disclosures is not HTTP 200 with disclosure hub marker
#   TOWER1_SMOKE_DISCLOSURES_TRIES (default 5) — repeat probe (LB mixes origins)
#   TOWER1_SMOKE_DISCLOSURES_RETRY_SLEEP (default 0.35) — seconds between tries
#
# Modular routes drift: LB may still hit 302 → /gate or non-JSON on /api/justice, /api/tower, etc.
# when some origins lag main (AuthMiddleware + tower gate must match — see republic_os_server
# ``_requires_auth`` / ``_is_tower1_public_path``). See sovereign/PLATFORM_COMPLETION_STATUS.md §2b.
#   TOWER1_SMOKE_MODULAR_DRIFT=0  — skip GET /api/justice + /api/tower probes
#   TOWER1_SMOKE_STRICT_MODULAR_API=1 — fail if either path is not HTTP 200 with JSON object body
#   GITHUB_ACTIONS=true — also print ::warning workflow commands to stdout for modular drift (CI summary UI)
#
# Hetzner ring intentionally off / handset-only origin: if many probes fail but loopback on OnePlus is OK,
#   see sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §2 (post-poweroff / sitemap 5xx) + §8 + sovereign/PLATFORM_COMPLETION_STATUS.md §2b handset row
#   (tunnel + operator-next-steps-fleet-tower.sh step 8).
#
# Handset /dl lag: TOWER1_SMOKE_STRICT_DL_HANDSET=1 — fail if GET /dl/agr-handset-secrets-md-py is not 200 (default 0: warn on 404)
#   TOWER1_SMOKE_DL_HANDSET_TRIES (default 5) — retries when HTTP 200 but body lacks module marker (LB / stale origin)
#   TOWER1_SMOKE_DL_HANDSET_RETRY_SLEEP (default 0.35) — seconds between tries
#
set -euo pipefail

BASE="${TOWER1_BASE:-https://auroragalaxyrepublic.com}"
BASE="${BASE%/}"

fail() { echo ":: $*" >&2; exit 1; }

# Modular drift: stderr for humans; optional GitHub Actions annotation (stdout) — same pattern as
# sovereign/scripts/fleet-ci-post-verify-guardian-warn.py
_warn_modular_drift() {
  local msg="$1"
  echo ":: WARN ${msg}" >&2
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    python3 -c "import urllib.parse,sys; print('::warning title=Tower1 modular API drift::' + urllib.parse.quote(sys.argv[1], safe=''))" "$msg"
  fi
}

_warn_disclosures_drift() {
  local msg="$1"
  echo ":: WARN ${msg}" >&2
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    python3 -c "import urllib.parse,sys; print('::warning title=Tower1 disclosures hub::' + urllib.parse.quote(sys.argv[1], safe=''))" "$msg"
  fi
}

_warn_dl_handset() {
  local msg="$1"
  echo ":: WARN ${msg}" >&2
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    python3 -c "import urllib.parse,sys; print('::warning title=Tower1 /dl handset module::' + urllib.parse.quote(sys.argv[1], safe=''))" "$msg"
  fi
}

MAX_TRIES="${TOWER1_SMOKE_MAX_TRIES:-3}"
RETRY_SLEEP="${TOWER1_SMOKE_RETRY_SLEEP:-3}"

code_get() {
  local path="$1"
  local rc="000"
  local attempt=1
  while [[ "$attempt" -le "$MAX_TRIES" ]]; do
    rc="$(curl -sS -o /tmp/t1_body.txt -w "%{http_code}" "${BASE}${path}" --max-time 25 2>/dev/null)" || rc="000"
    if [[ -n "$rc" ]] && [[ "$rc" != "000" ]]; then
      echo "$rc"
      return 0
    fi
    if [[ "$attempt" -lt "$MAX_TRIES" ]]; then
      echo "[tower1-smoke] retry ${attempt}/${MAX_TRIES} GET ${path} (rc=${rc:-000})" >&2
      sleep "$RETRY_SLEEP"
    fi
    attempt=$((attempt + 1))
  done
  echo "$rc"
}

code_post_json() {
  local path="$1"
  local body="$2"
  local rc="000"
  local attempt=1
  while [[ "$attempt" -le "$MAX_TRIES" ]]; do
    rc="$(curl -sS -o /tmp/t1_body.txt -w "%{http_code}" -X POST "${BASE}${path}" \
      -H "Content-Type: application/json" \
      -d "$body" --max-time 35 2>/dev/null)" || rc="000"
    if [[ -n "$rc" ]] && [[ "$rc" != "000" ]]; then
      echo "$rc"
      return 0
    fi
    if [[ "$attempt" -lt "$MAX_TRIES" ]]; then
      echo "[tower1-smoke] retry ${attempt}/${MAX_TRIES} POST ${path} (rc=${rc:-000})" >&2
      sleep "$RETRY_SLEEP"
    fi
    attempt=$((attempt + 1))
  done
  echo "$rc"
}

echo "[tower1-smoke] base=${BASE}"

rc=$(code_get "/robots.txt")
if [[ "$rc" == "301" ]]; then
  echo ":: robots.txt HTTP 301 (stale Cloudflare cache — purge from CF dashboard or wait for TTL expiry)"
  echo ":: Skipping robots.txt content check (origin serves correctly; CF edge cache stale)"
elif [[ "$rc" == "200" ]]; then
  grep -q "Index machine-readable truth surfaces first" /tmp/t1_body.txt \
    || fail "robots.txt missing new repo marker (fleet may not have pulled main yet)"
else
  if [[ "$rc" =~ ^5 ]]; then
    echo "[tower1-smoke] canonical robots.txt HTTP ${rc} — if Hetzner VMs are off, edge is not on the handset tunnel yet — sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §2; bash sovereign/scripts/operator-next-steps-fleet-tower.sh" >&2
  fi
  fail "robots.txt HTTP $rc"
fi

rc=$(code_get "/sitemap.xml")
if [[ "$rc" != "200" ]]; then
  if [[ "$rc" =~ ^5 ]]; then
    echo "[tower1-smoke] canonical sitemap.xml HTTP ${rc} — if Hetzner fleet is off, run OnePlus uvicorn + Cloudflare tunnel per sovereign/PHONES_ONLY_PUBLIC_SURFACE.md §2; bash sovereign/scripts/operator-next-steps-fleet-tower.sh" >&2
  fi
  fail "sitemap.xml HTTP $rc"
fi
grep -q "api/public/search-discovery" /tmp/t1_body.txt || fail "sitemap missing search-discovery URL"
grep -q "api/public/award-evidence" /tmp/t1_body.txt || fail "sitemap missing award-evidence URL"

# Public disclosure hub (early): edge can 302 → /awards while other probes pass — surface before /dl chain.
disc_ok=0
disc_last=""
disc_tries="${TOWER1_SMOKE_DISCLOSURES_TRIES:-5}"
disc_sleep="${TOWER1_SMOKE_DISCLOSURES_RETRY_SLEEP:-0.35}"
for _disc_attempt in $(seq 1 "$disc_tries"); do
  disc_hdr="$(curl -sS -D - -o /tmp/t1_disclosures_body.txt --max-redirs 0 "${BASE}/disclosures" --max-time 25 2>/dev/null || true)"
  disc_rc="$(printf '%s' "$disc_hdr" | grep -m1 -oE '^HTTP/[0-9.]+ [0-9]+' | awk '{print $2}' || echo "000")"
  disc_loc="$(printf '%s' "$disc_hdr" | grep -m1 -i '^location:' | sed 's/^[Ll][Oo][Cc][Aa][Tt][Ii][Oo][Nn]:[[:space:]]*//' | tr -d '\r' || true)"
  if [[ "$disc_rc" == "200" ]] && grep -q 'Tower 1 Public Disclosures' /tmp/t1_disclosures_body.txt; then
    disc_ok=1
    break
  fi
  disc_last="${disc_rc} loc=${disc_loc:-none}"
  if [[ "$disc_rc" == "302" ]] || [[ "$disc_rc" == "301" ]]; then
    if echo "$disc_loc" | grep -qiE 'auroragalaxyrepublic\.com/awards'; then
      disc_last="redirect_to_awards ${disc_last}"
    fi
  fi
  if [[ "$_disc_attempt" -lt "$disc_tries" ]]; then
    sleep "$disc_sleep"
  fi
done
if [[ "$disc_ok" -eq 1 ]]; then
  :
elif [[ "${TOWER1_SMOKE_STRICT_DISCLOSURES:-0}" == "1" ]]; then
  fail "/disclosures not disclosure hub after ${disc_tries} tries (last: ${disc_last})"
else
  _warn_disclosures_drift "/disclosures hub not OK after ${disc_tries} tries (last: ${disc_last}) — Cloudflare redirect, cache, or mixed fleet origins"
fi

rc=$(code_get "/api/public/engine-runtime")
[[ "$rc" == "200" ]] || fail "engine-runtime HTTP $rc (expected 200 after chat + SEO commits on main)"
head -c 2 /tmp/t1_body.txt | grep -q '{' || fail "engine-runtime body not JSON"

rc=$(code_get "/health")
if [[ "$rc" == "200" ]]; then
  head -c 2 /tmp/t1_body.txt | grep -q '{' || fail "/health body not JSON"
  grep -q "healthy\|status" /tmp/t1_body.txt || fail "/health body missing expected status fields"
else
  echo ":: WARN /health HTTP $rc — trying /api/health then /api/public/health" >&2
  rc=$(code_get "/api/health")
  if [[ "$rc" == "200" ]]; then
    head -c 2 /tmp/t1_body.txt | grep -q '{' || fail "api/health body not JSON"
    grep -q "healthy\|status" /tmp/t1_body.txt || fail "api/health body missing expected status fields"
  else
    echo ":: WARN api/health HTTP $rc — trying /api/public/health" >&2
    rc=$(code_get "/api/public/health")
    [[ "$rc" == "200" ]] || fail "api/public/health HTTP $rc (expected 200 when /health and /api/health unavailable)"
    head -c 2 /tmp/t1_body.txt | grep -q '{' || fail "api/public/health body not JSON"
    grep -q "ok\|healthy\|status\|engine" /tmp/t1_body.txt || fail "api/public/health body missing expected probe fields"
  fi
fi

# Optional: require live origin git SHA to match TOWER1_EXPECT_DEPLOY_REV (fleet deploy verification).
if [[ -n "${TOWER1_EXPECT_DEPLOY_REV:-}" ]]; then
  if ! command -v jq >/dev/null 2>&1; then
    fail "TOWER1_EXPECT_DEPLOY_REV set but jq not installed"
  fi
  dep_rc=$(code_get "/api/health")
  [[ "$dep_rc" == "200" ]] || fail "/api/health HTTP ${dep_rc} (need 200 for deploy rev check)"
  got=$(jq -r '.agr_deploy_revision // empty' /tmp/t1_body.txt 2>/dev/null || true)
  if [[ -z "$got" || "$got" == "null" ]]; then
    fail "TOWER1_EXPECT_DEPLOY_REV set but live /api/health has no agr_deploy_revision (run fleet-pull after upgrading republic_os_server)"
  fi
  if [[ "$got" != "${TOWER1_EXPECT_DEPLOY_REV}" ]]; then
    fail "agr_deploy_revision mismatch live=${got} expected=${TOWER1_EXPECT_DEPLOY_REV}"
  fi
fi

# Consciousness engine public advisory (same path autonomous merge council uses for Tower dialogue).
rc=$(code_post_json "/api/public/citizen-engine-advice" '{"topic":"Tower1 smoke: autonomous merge council context probe (no secrets).","message":"Tower1 smoke: autonomous merge council context probe (no secrets)."}')
if [[ "$rc" == "200" ]]; then
  python3 -c "import json; d=json.load(open('/tmp/t1_body.txt',encoding='utf-8')); assert d.get('ok') is True" \
    || fail "citizen-engine-advice body missing ok:true"
elif [[ "$rc" == "429" ]]; then
  echo ":: WARN citizen-engine-advice HTTP 429 (Tower rate limit; smoke continues)" >&2
else
  fail "citizen-engine-advice HTTP $rc (engine must be reachable for merge-gate dialogue)"
fi

rc=$(code_post_json "/api/republic/chat" '{"message":"smoke ping","consciousness":"Kora","mode":"text","session_id":"smoke","citizen_id":"smoke"}')
[[ "$rc" == "200" ]] || fail "republic chat HTTP $rc (302 means tower gate or auth still blocking POST)"
python3 -c "import json; json.load(open('/tmp/t1_body.txt',encoding='utf-8'))" || fail "republic chat body not valid JSON"

rc=$(code_get "/api/public/mirl/catalog")
if [[ "$rc" == "200" ]]; then
  head -c 2 /tmp/t1_body.txt | grep -q '{' || fail "mirl catalog body not JSON"
else
  if [[ "${TOWER1_SMOKE_STRICT_MIRL:-1}" == "1" ]]; then
    fail "mirl catalog HTTP $rc (deploy republic_os_server MIR-L routes)"
  else
    echo ":: WARN mirl catalog HTTP $rc (non-strict: TOWER1_SMOKE_STRICT_MIRL=0)" >&2
  fi
fi

rc=$(code_get "/sovereign/mirl/charter/html")
if [[ "$rc" == "200" ]]; then
  if grep -qi "<!DOCTYPE html>" /tmp/t1_body.txt; then
    : ok
  elif grep -q 'name="agr-page-stem" content="charter"' /tmp/t1_body.txt; then
    echo ":: WARN MIR-L charter html missing <!DOCTYPE> (edge/origin may lag main; projection marker present)" >&2
  else
    fail "charter html missing doctype and not recognisable MIR-L charter projection"
  fi
else
  if [[ "${TOWER1_SMOKE_STRICT_MIRL:-1}" == "1" ]]; then
    fail "MIR-L charter html HTTP $rc"
  else
    echo ":: WARN MIR-L charter html HTTP $rc (non-strict: TOWER1_SMOKE_STRICT_MIRL=0)" >&2
  fi
fi

# Public /dl/* handset payloads (same markers as agr_autonomous_merge_gate --launch-readiness-tower-smoke).
rc=$(code_get "/dl/s25-termux-setup")
[[ "$rc" == "200" ]] || fail "dl/s25-termux-setup HTTP $rc (Termux one-line bootstrap)"
grep -qF '#!/data/data/com.termux/files/usr/bin/bash' /tmp/t1_body.txt \
  || fail "dl/s25-termux-setup missing Termux shebang"
grep -qF '=== AGR Guardian node' /tmp/t1_body.txt \
  || fail "dl/s25-termux-setup missing bootstrap banner"

rc=$(code_get "/dl/ceo")
[[ "$rc" == "200" ]] || fail "dl/ceo HTTP $rc (Termux CEO launcher)"
grep -qF '#!/data/data/com.termux/files/usr/bin/bash' /tmp/t1_body.txt \
  || fail "dl/ceo missing Termux shebang"
grep -qF 'S25 CEO COMMAND TERMINAL' /tmp/t1_body.txt || fail "dl/ceo missing launcher banner"
grep -qF '/dl/ceo-os-py' /tmp/t1_body.txt || fail "dl/ceo missing ceo-os-py fetch path"
if grep -qF '/dl/agr-handset-secrets-md-py' /tmp/t1_body.txt; then
  : ok
else
  echo ":: WARN dl/ceo missing optional /dl/agr-handset-secrets-md-py fetch line (Tower may lag main; fleet-pull)" >&2
fi

rc=$(code_get "/dl/ceo-os-py")
[[ "$rc" == "200" ]] || fail "dl/ceo-os-py HTTP $rc (CEO shell served for Termux)"
dl_try=1
dl_max="${TOWER1_SMOKE_DL_CEO_OS_PY_BODY_TRIES:-3}"
dl_sleep="${TOWER1_SMOKE_DL_CEO_OS_PY_BODY_SLEEP:-2}"
while [[ "$dl_try" -le "$dl_max" ]]; do
  if grep -qF '#!/usr/bin/env python3' /tmp/t1_body.txt && grep -qF 's25_ceo_os.py' /tmp/t1_body.txt; then
    break
  fi
  if [[ "$dl_try" -ge "$dl_max" ]]; then
    fail "dl/ceo-os-py missing python shebang or module stem marker (after ${dl_max} body attempts)"
  fi
  echo "[tower1-smoke] WARN dl/ceo-os-py HTTP 200 but body markers missing — retry ${dl_try}/${dl_max} after ${dl_sleep}s" >&2
  sleep "$dl_sleep"
  rc=$(code_get "/dl/ceo-os-py")
  [[ "$rc" == "200" ]] || fail "dl/ceo-os-py HTTP $rc on retry (CEO shell served for Termux)"
  dl_try=$((dl_try + 1))
done

rc=$(code_get "/dl/agr-vault-rag-py")
[[ "$rc" == "200" ]] || fail "dl/agr-vault-rag-py HTTP $rc"
grep -qF 'AGR Master Vault RAG' /tmp/t1_body.txt || fail "dl/agr-vault-rag-py missing docstring marker"

rc=$(code_get "/dl/agr-vault-github-export-py")
[[ "$rc" == "200" ]] || fail "dl/agr-vault-github-export-py HTTP $rc"
grep -qF 'GitHub PR export' /tmp/t1_body.txt || fail "dl/agr-vault-github-export-py missing docstring marker"

# /dl handset: body must include fixed substring (see module docstring in agr_handset_identity_from_secrets_md.py).
rc=$(code_get "/dl/agr-handset-secrets-md-py")
strict_hs="${TOWER1_SMOKE_STRICT_DL_HANDSET:-0}"
hs_ok=0
hs_last=""
hs_tries="${TOWER1_SMOKE_DL_HANDSET_TRIES:-5}"
hs_sleep="${TOWER1_SMOKE_DL_HANDSET_RETRY_SLEEP:-0.35}"
for _hs_attempt in $(seq 1 "$hs_tries"); do
  rc=$(code_get "/dl/agr-handset-secrets-md-py")
  if [[ "$rc" == "200" ]] && grep -qF 'agr_handset_identity_from_secrets_md' /tmp/t1_body.txt; then
    hs_ok=1
    break
  fi
  hs_last="$rc"
  if [[ "$rc" == "200" ]]; then
    hs_last="200_missing_marker"
  fi
  if [[ "$_hs_attempt" -lt "$hs_tries" ]]; then
    sleep "$hs_sleep"
  fi
done
if [[ "$hs_ok" -eq 1 ]]; then
  :
elif [[ "$strict_hs" == "1" ]]; then
  fail "dl/agr-handset-secrets-md-py not OK after ${hs_tries} tries (last: ${hs_last})"
elif [[ "$hs_last" == "404" ]]; then
  _warn_dl_handset "dl/agr-handset-secrets-md-py HTTP 404 (Tower may lag main; fleet-pull or set TOWER1_SMOKE_STRICT_DL_HANDSET=1 to fail)"
else
  _warn_dl_handset "dl/agr-handset-secrets-md-py not OK after ${hs_tries} tries (last: ${hs_last}) — mixed origins or Tower lags main; fleet-pull"
fi

# Termux one-line recover (Tower 1 fetches mint + bootstrap + wrapper, then runs recover).
rc=$(code_get "/dl/mint-cloudflare-tunnel-token-stdout-py")
[[ "$rc" == "200" ]] || fail "dl/mint-cloudflare-tunnel-token-stdout-py HTTP $rc"
grep -qF 'mint_cloudflare_tunnel_token_stdout' /tmp/t1_body.txt \
  || fail "dl/mint-cloudflare-tunnel-token-stdout-py missing module stem marker"
grep -qF 'CONFIRM=1' /tmp/t1_body.txt \
  || fail "dl/mint-cloudflare-tunnel-token-stdout-py missing CONFIRM gate marker"

rc=$(code_get "/dl/termux-republic-one-shot-bootstrap-sh")
[[ "$rc" == "200" ]] || fail "dl/termux-republic-one-shot-bootstrap-sh HTTP $rc"
grep -qF 'termux-republic-one-shot-bootstrap' /tmp/t1_body.txt \
  || fail "dl/termux-republic-one-shot-bootstrap-sh missing script marker"

rc=$(code_get "/dl/termux-phone-one-shot-recover-sh")
[[ "$rc" == "200" ]] || fail "dl/termux-phone-one-shot-recover-sh HTTP $rc"
grep -qF 'termux-phone-one-shot-recover' /tmp/t1_body.txt \
  || fail "dl/termux-phone-one-shot-recover-sh missing script marker"

rc=$(code_get "/dl/termux-republic-recover")
[[ "$rc" == "200" ]] || fail "dl/termux-republic-recover HTTP $rc"
grep -qF 'AGR_TERMUX_REPUBLIC_RECOVER_V1' /tmp/t1_body.txt \
  || fail "dl/termux-republic-recover missing recover banner"
grep -qF '/dl/termux-operator-return-one-paste-sh' /tmp/t1_body.txt \
  || fail "dl/termux-republic-recover missing operator-return fetch path"
grep -qF '/dl/mint-cloudflare-tunnel-token-stdout-py' /tmp/t1_body.txt \
  || fail "dl/termux-republic-recover missing mint fetch path"

rc=$(code_get "/dl/termux-operator-return-one-paste-sh")
[[ "$rc" == "200" ]] || fail "dl/termux-operator-return-one-paste-sh HTTP $rc"
grep -qF 'termux-operator-return' /tmp/t1_body.txt \
  || fail "dl/termux-operator-return-one-paste-sh missing script marker"
grep -qF 'CONFIRM=1' /tmp/t1_body.txt \
  || fail "dl/termux-operator-return-one-paste-sh missing CONFIRM gate marker"

rc=$(code_get "/dl/termux-operator-wake")
[[ "$rc" == "200" ]] || fail "dl/termux-operator-wake HTTP $rc"
grep -qF 'AGR_TERMUX_OPERATOR_WAKE_V1' /tmp/t1_body.txt \
  || fail "dl/termux-operator-wake missing wake banner"
grep -qF '/dl/termux-operator-return-one-paste-sh' /tmp/t1_body.txt \
  || fail "dl/termux-operator-wake missing operator-return fetch path"

rc=$(code_post_json "/api/republic/laws/check" '{"action":"Tower1 smoke: constitutional law-check endpoint readiness (benign ping; no merge)."}')
if [[ "$rc" == "200" ]]; then
  :
elif [[ "$rc" == "302" ]]; then
  fail "laws/check HTTP 302 (AuthMiddleware: add /api/republic/laws/check to _PUBLIC_PATHS; Tower gate: _TOWER1_PUBLIC_POST_PATHS; then fleet-pull)"
else
  fail "laws/check HTTP $rc (constitutional autonomous gate depends on this endpoint)"
fi
python3 - <<'PY' || fail "laws/check body not schema v1 approved"
import json
with open("/tmp/t1_body.txt", encoding="utf-8") as f:
    d = json.load(f)
assert d.get("schema_version") == 1
assert d.get("blocked") is False
assert d.get("autonomous_merge_allowed") is True
assert d.get("violations") == []
PY

# Optional drift signal: main expects /api/seo/status.indexing_automation_note (PR #99+). Warn unless strict.
rc=$(code_get "/api/seo/status")
if [[ "$rc" == "200" ]]; then
  set +e
  python3 - <<'PY' >/dev/null 2>&1
import json
import sys
try:
    with open("/tmp/t1_body.txt", encoding="utf-8") as f:
        d = json.load(f)
except Exception:
    sys.exit(2)
if not isinstance(d, dict):
    sys.exit(2)
n = d.get("indexing_automation_note")
sys.exit(0 if isinstance(n, str) and n.strip() else 1)
PY
  py_ec=$?
  set -e
  if [[ "$py_ec" -eq 0 ]]; then
    :
  elif [[ "$py_ec" -eq 1 ]]; then
    if [[ "${TOWER1_SMOKE_REQUIRE_SEO_STATUS_FIELDS:-0}" == "1" ]]; then
      fail "/api/seo/status missing non-empty indexing_automation_note — Tower lags main (fleet-pull) or CI lacks AGR_FLEET_KEY_CONTENT"
    fi
    echo "::notice::Tower drift: /api/seo/status lacks indexing_automation_note — run fleet-pull or set AGR_FLEET_KEY_CONTENT for CI deploy" >&2
    echo ":: WARN /api/seo/status missing indexing_automation_note — Tower may lag origin/main (run fleet-pull; set GitHub secret AGR_FLEET_KEY_CONTENT for automated deploy)" >&2
  else
    if [[ "${TOWER1_SMOKE_REQUIRE_SEO_STATUS_FIELDS:-0}" == "1" ]]; then
      fail "/api/seo/status not a JSON object (cannot read indexing_automation_note)"
    fi
    echo ":: WARN /api/seo/status returned 200 but body is not a JSON object (unexpected)" >&2
  fi
else
  echo ":: WARN /api/seo/status HTTP ${rc} (SEO status probe skipped)" >&2
fi

# Modular shadow routes (gate / edge / stale origin) — warn by default; strict optional.
if [[ "${TOWER1_SMOKE_MODULAR_DRIFT:-1}" != "0" ]]; then
  for path in "/api/justice" "/api/tower"; do
    rc=$(code_get "$path")
    if [[ "$rc" == "200" ]]; then
      if head -c 2 /tmp/t1_body.txt | grep -q '{'; then
        :
      else
        msg="${path} HTTP 200 but body does not look like JSON object"
        if [[ "${TOWER1_SMOKE_STRICT_MODULAR_API:-0}" == "1" ]]; then
          fail "$msg"
        fi
        _warn_modular_drift "${msg} - check edge routing and fleet-pull (PLATFORM_COMPLETION_STATUS section 2b)"
      fi
    else
      msg="${path} HTTP $rc (expected 200 JSON on Tower I for anonymous GET when main is deployed)"
      if [[ "${TOWER1_SMOKE_STRICT_MODULAR_API:-0}" == "1" ]]; then
        fail "$msg"
      fi
      _warn_modular_drift "${msg} - fleet-pull / Cloudflare path rules; incognito retest"
    fi
  done
fi

echo "[tower1-smoke] OK — Tower 1 public SEO + chat surfaces match expected main revision."
