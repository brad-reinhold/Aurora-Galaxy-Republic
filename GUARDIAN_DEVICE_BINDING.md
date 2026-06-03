# Guardian device binding — iPhone 17 Pro (node 6) + OnePlus 15 (node 7) (operator only)

**Platform nodes:** **`iphone_17_pro`** (iPhone 17 Pro) = node **6** (legacy **`s25_ultra`** in sync evidence); **`oneplus_15`** = node **7** (primary Guardian, Termux). See **`AGENTS.md`** and **`GUARDIAN_NODE_OS.md`** for rollout order (handsets **last**).

**Goal:** Bind the CEO shell and guardian loop to **authorized handsets** without creating **any** public Guardian vector.

---

## 1. On the handset (never committed)

1. Create directory: `mkdir -p ~/.secrets`  
2. Create **`~/.secrets/guardian-device-profile.json`** (mode `0600`) with at least:

   - `canonical_device_key` — operator-chosen stable id (e.g. `oneplus-15-ref-2026`).  
   - Optional `lineage_tag` — non-secret label for your own notes.

3. **From `Secrets.md` (private checkout):** copy the vault file to the device as **`~/Secrets.md`** (or set **`AGR_SECRETS_MD`**) and run **`python3 ~/.agr/agr_handset_identity_from_secrets_md.py --merge-termux`** (installed by **`s25_termux_setup.sh`** from **`GET /dl/agr-handset-secrets-md-py`**), or from a repo clone: **`CONFIRM=1 bash sovereign/scripts/handset-profile-from-secrets-md-termux.sh`**. Default role is **`oneplus_15`**; iPhone reference material: **`AGR_HANDSET_SECRETS_ROLE=iphone_17_pro`**.

4. Optionally set `AGR_GUARDIAN_DEVICE_SECRET_PATH` if the file lives elsewhere.

**`s25_ceo_os.py`** merges this file into enroll / heartbeat payloads as `identity_secret` (server may store correlation keys; **do not** log raw IMEI). **`http_json`** also sends optional **`x-device-*`** headers (and a **`User-Agent`** suffix from the first **`guardian_ua_substrings`** entry) when the profile contains **`model`**, **`serial`**, **`imei1`**, **`imei2`**, **`eid`**, **`wifi_mac`**, matching **`republic_os_server`** `_is_sovereign_device` when the **same** values are on the fleet profile. **`POST /api/s25/heartbeat`** uses **`device`** = **`platform_node_id`** from the profile (e.g. **`oneplus_15`**) when set, else legacy **`s25-ultra`**; override with **`AGR_HEARTBEAT_DEVICE`**.

---

## 2. IMEI and `device_hash` (local only)

- **`device_hash`** sent to `/api/s25/security/enroll` is a **SHA-256** of local identity material assembled in `collect_identity()` (model, fingerprint, serial fields when available, `android_id`, host).  
- If you incorporate IMEI into that material **on-device only**, it still must **never** appear in git, public URLs, or static JSON.

---

## 3. On the fleet (server env)

Optional **fail-closed enroll** (recommended):

- Set **`AGR_S25_CLIENT_GATE_TOKEN`** on the **server** and the **same value** in Termux (`export AGR_S25_CLIENT_GATE_TOKEN=...` in `~/.bashrc` or session). The CEO shell sends header **`X-AGR-S25-Client-Gate`**. When the server env is set, enroll without the header returns **403** `client_gate_required`.
- Set **`AGR_S25_ENROLL_DEVICE_HASHES`** to a comma-separated list of **allowed** `device_hash` values (64-char hex) for the OnePlus 15 (and any spare test hashes).  
- When this env var is **set**, enroll requests whose `device_hash` is **not** in the list receive **403** `enroll_not_authorized`.  
- When the env var is **unset**, behavior matches the previous open enroll (not recommended on internet-exposed origins).

Compute the hash once from the device (after CEO shell runs `collect_identity()`), or from a one-off local Python/sha256 of the same pipe-delimited string the shell uses — **offline**, then paste the hash into fleet env / vault, not IMEI.

---

## 4. Fleet server — hardware headers + CEO gate (never in git)

`republic_os_server` loads **`agr_guardian_device_binding`** at startup. Profile JSON resolution order:

1. **`AGR_GUARDIAN_DEVICE_PROFILE_PATH`** (explicit file)
2. **`/opt/agr/.secrets/guardian-device-profile.json`** when present (fleet default; directory via **`CONFIRM=1 bash sovereign/scripts/fleet-guardian-secrets-remote-init.sh`**). Override directory with **`AGR_FLEET_GUARDIAN_SECRETS_DIR`** or filename with **`AGR_GUARDIAN_DEVICE_PROFILE_BASENAME`** (must be a single basename, no path segments).
3. **`~/.secrets/guardian-device-profile.json`** on the server user that runs uvicorn
- Optional per-field env overrides: **`AGR_DEVICE_MODEL`**, **`AGR_DEVICE_SERIAL`**, **`AGR_DEVICE_EID`**, **`AGR_DEVICE_WIFI_MAC`**, **`AGR_DEVICE_IMEI1`**, **`AGR_DEVICE_IMEI2`**, **`AGR_DEVICE_FCC_ID`**, **`AGR_DEVICE_PHONE`**, **`AGR_DEVICE_WG_IP`**.
- **Secrets.md merge (optional):** set **`AGR_MERGE_HANDSET_FROM_SECRETS_MD=1`** and **`AGR_HANDSET_SECRETS_ROLE=oneplus_15`** or **`iphone_17_pro`** so **`agr_guardian_device_binding`** fills **empty** hardware fields from repo-root **`Secrets.md`** (same handset block as the device scripts). JSON profile and **`AGR_DEVICE_*`** still win. After materializing **`/opt/agr/.secrets/guardian-device-profile.json`**, prefer **`AGR_MERGE_HANDSET_FROM_SECRETS_MD=0`** on production.
- Extra User-Agent substrings (comma-separated): **`AGR_GUARDIAN_UA_SUBSTRINGS`** (or **`guardian_ua_substrings`** array in JSON).
- Extra never-exile IPs (comma-separated): **`AGR_GUARDIAN_WHITELIST_IPS`** (or **`guardian_whitelist_ips`** / **`whitelist_ips`** array in JSON).

**Guardian beacon cookie:** set **`guardian_beacon_secret`** in the profile JSON or **`AGR_GUARDIAN_BEACON_SECRET`** on the server. If unset, the server derives a stable value from **`ADMIN_PASS_HASH`** / **`SESSION_SECRET`** (rotate by setting an explicit secret). After changing it, call **`POST /api/guardian/set-beacon`** again from a browser so the cookie matches.

**Fleet status (read-only):** **`FLEET_STATUS_FORMAT=json bash sovereign/fleet-status-read-only.sh`** includes booleans **`fleet_guardian_secrets_dir`**, **`fleet_guardian_profile_nonempty`**, and **`root_guardian_profile_nonempty`** (directory exists; file exists and size greater than zero; same for **`/root/.secrets/guardian-device-profile.json`**). No file contents are read or logged. Override paths with **`FLEET_STATUS_GUARDIAN_SECRETS_DIR`** and **`FLEET_STATUS_GUARDIAN_PROFILE`** (basename only). Batch SSH check without full **`fleet-status`**: **`bash sovereign/scripts/fleet-guardian-secrets-verify-remote.sh`**. Optional **`FLEET_GUARDIAN_SECRETS_VERIFY_REQUIRE_PROFILE=1`** on that script exits non-zero when an SSH-ok host has no non-empty fleet or root profile (fail-closed gate).

**Fleet CI post-verify:** **`bash sovereign/fleet-ci-post-verify.sh`** runs **`bash sovereign/scripts/fleet-bash-syntax-check.sh`** ( **`bash -n`** on **`sovereign/lib/*`** fleet helpers, **`export-operator-env-from-secrets-md.sh`**, and the same fleet shell scripts **`chmod +x`**'d in **fleet-deploy-pull**, including **`tower1-public-smoke.sh`**, **`indexnow-submit-sitemap.sh`**, and **`fleet-verify-public-http.sh`**) before any SSH (set **`FLEET_CI_POST_VERIFY_SKIP_BASH_N=1`** to skip). Operators may run **`fleet-bash-syntax-check.sh`** alone before **`fleet-pull`**.

**Fleet profile from vault:** on a node with private **`Secrets.md`** in the repo tree: **`CONFIRM=1 bash sovereign/scripts/fleet-guardian-profile-from-secrets-md.sh`** writes **`/opt/agr/.secrets/guardian-device-profile.json`** (default role **`oneplus_15`**; set **`AGR_HANDSET_SECRETS_ROLE=iphone_17_pro`** for node-6 reference file on a dedicated host). Then **`systemctl restart agr-republic`**.

---

## Related

- `sovereign/GUARDIAN_NODE_OS.md`  
- `aurora_server/routes/routes_s25_heartbeat.py` — `s25_security_enroll`  
- `aurora_server/agr_guardian_device_binding.py` — profile + env merge
