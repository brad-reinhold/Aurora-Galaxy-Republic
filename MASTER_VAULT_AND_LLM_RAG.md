# Master vault + GPT‑OSS / “4.5” local model — retrieval architecture

**Purpose:** Describe how a **large local model** (OpenAI‑compatible GGUF stack — referred to here as **4.5-class** for continuity) connects to **Republic data** (archives, founding docs, exports, PRs, **Kora dialogue rescue**) **without** pretending the full corpus fits in a single context window or a single SQLite file.

**Canonical Tower 1:** https://auroragalaxyrepublic.com  

**Privacy:** The **Kora OpenAI export** (~13M+ words) and other sovereign material are **operator data**. They belong under **`/opt/agr/...`** on fleet, encrypted handset storage, or cold storage — **never** committed to git. This document is **notation and procedure** only.

---

## 1. What “master vault” means in practice

| Tier | Contents | Role for the LLM |
|------|----------|------------------|
| **A — Git / PR history** | This repository + GitHub PRs, Actions logs | Model sees **what you ship** via prompts, diffs, or a **GitHub API** tool (PAT in operator vault / device `EncryptedFile` — not in repo). |
| **B — Structured Republic DBs** | SQLite under `aurora_server/data/*.db` (chat, engine, research, etc.) | **Query + sample** into prompts (bounded rows) or via small **read-only** API routes you already trust. Optional merge plane: `agr_universal_memory_plane.py` → `universal_memory_plane.db` (provenance, not magic “all text”). |
| **C — Document vault (files)** | `.md`, `.pdf`, `.docx`, `.txt`, images, founding PDFs, archives | **Indexed for retrieval** (chunk → FTS; **`.pdf`/`.docx`** when extractors exist); only **top‑k chunks** go to the model per turn. |
| **D — Kora dialogue export** | Single large export file(s) from OpenAI rescue | Same as **C**: **chunk + index**; optional **separate** index namespace `kora_export` so retrieval can prefer it when the user or policy selects **Citizen #1** context. |

There is **no** single binary “master vault blob” in this repo that contains all of the above. The **integration** is **policy + paths + indexing + prompt assembly**.

---

## 2. How the “4.5” hooks to the database (correct mental model)

- **Weights** stay on disk (GGUF); **working memory** is the model’s **context window** (large but finite).  
- **Long‑term memory** for archives is **retrieval**: your stack loads **snippets** from DBs/files into the prompt (or tool results the model reads).  
- **Tower consciousness engine** (`/api/republic/chat`, engine endpoints) remains the **Republic** path; the **local OpenAI‑compatible** server is the **GGUF** path. A **unified** handset UX can **blend** them (already supported in CEO shell policy) **after** retrieval is wired. **Tower Kora chat** can optionally prepend **`agr_vault_rag`** snippets when **`AGR_CHAT_VAULT_RAG=1`** and the vault index exists — see §5 **`AGR_CHAT_VAULT_RAG_*`**. When **`converse()`** has a narrative ledger and/or symbolic surface, chat vault retrieval can **enrich the FTS query** and optionally **scope paths** (prefix filters on indexed vault paths).

---

## 3. Recommended layout on Hetzners (five sovereign peers)

Keep a **stable directory convention** (rsync / backup friendly):

| Path | Use |
|------|-----|
| `/opt/agr/vault/documents/` | Canonical **document** vault (md, pdf, docx, txt, images). |
| `/opt/agr/vault/kora/` | **Kora export** only (chunked copies OK: `kora_export.jsonl`, etc.). |
| `/opt/agr/vault/archives/` | Large zips / legacy exports (read-only mounts OK). |
| `/opt/agr/vault/republic_builder/` | **Operator proposal inbox** (`inbox/`, `approved/`, `rejected/`) — see **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** (not auto-deploy). |
| `/opt/agr/aurora_server/data/` | Existing SQLite + runtime (already authoritative for app state). |

**Do not** store the only copy of the 13M‑word export solely on one phone; mirror to **at least two** fleet nodes + offline backup per your continuity doctrine.

### 3a. Getting large files onto the fleet (pick one or combine)

| Method | When to use | How |
|--------|--------------|-----|
| **A — Operator `rsync` / `scp`** | You have the export on a laptop or NAS with fleet SSH | `rsync -avz -e "ssh -i …" ./kora_chunks/ root@<node>:/opt/agr/vault/kora/incoming/` (repeat for a second node). |
| **B — `fleet-vault-kora-rsync.sh`** | Same key as `fleet-pull`; want scripted **local**, **fanout**, or **tar/ssh** modes | `CONFIRM=1 bash sovereign/scripts/fleet-vault-kora-rsync.sh` — see script header for **`VAULT_RSYNC_MODE`** (`local` \| `fanout` \| `scp`) and **`VAULT_RSYNC_SUBDIR`**. **Fanout** pulls from **`FLEET_RSYNC_SOURCE`** (default first IP in the script) into a temp dir, then pushes to the other four Hetzner peers (good when one node already has the corpus). By default the script **exits non-zero** if any peer copy fails; set **`FLEET_VAULT_RSYNC_FAIL_OPEN=1`** only for intentional best-effort partial mirrors. |
| **C — Tower `/vault-upload`** | Small controlled batches through the browser | Use for curated drops, not a raw multi‑GB dump unless you chunk server‑side. |
| **D — Object storage + one-node pull** | Export lives in S3/R2/GCS | Upload privately; SSH to one node, `curl`/`aws s3 cp` into `/opt/agr/vault/kora/incoming/`, then **B** fanout to the rest. |
| **E — Handset as courier** | Phone has the file; no fast desktop path | `adb push` or Termux `scp`/`rsync` from the phone to **one** fleet IP, then **B** fanout. |

After files land, run **`bash sovereign/scripts/fleet-vault-verify-remote.sh`** (read-only), then rebuild the vault FTS index on each node: **`CONFIRM=1 bash sovereign/scripts/fleet-vault-rag-build-remote.sh`** (wraps **`vault-rag-build-index.sh`** / `agr_vault_rag.py build` with **`AGR_MASTER_VAULT_ROOT=/opt/agr/vault`**) or CEO menu **14** on a single box.

---

## 4. Indexing phases (realistic order)

| Phase | Work | Done when |
|-------|------|-----------|
| **V1** | **FTS or sqlite** index over normalized text chunks (`.md`, `.txt`, exports converted to text) | `SELECT … MATCH` or equivalent returns ranked chunks for a query string |
| **V2** | **Embeddings** (OpenAI-compatible `/v1/embeddings`) + hybrid rank | **Partial (in `agr_vault_rag`):** `AGR_VAULT_EMBEDDINGS=1` stores normalized vectors in `vault_embeddings`; `search` blends cosine + FTS (`AGR_RAG_HYBRID_ALPHA`). Uses `AGR_EMBEDDING_BASE_URL` or `AGR_LLM_OPENAI_BASE` and `AGR_EMBEDDING_MODEL`. |
| **V3** | **PDF/DOCX** text extraction on ingest | **Partial (in `agr_vault_rag`):** `.pdf` via **pypdf** (optional) or **`pdftotext`**; `.docx` via **python-docx** (optional). If extraction yields empty text, the file is still marked indexed — install tools and run **`AGR_VAULT_FORCE_REINDEX=1`** rebuild. |
| **V3b** | **Vault images** (metadata + captions, not OCR) | **`AGR_VAULT_INDEX_IMAGES=1`:** index `.png`/`.jpg`/… as one FTS chunk: path, size, optional dimensions (Pillow if installed), plus **`photo.png.txt`** sidecar text for operator captions / alt text |
| **V4** | **GitHub PR index** (operator job or cron) | **`agr_vault_github_export.py`:** writes ``pr-{n}-{slug}.md`` under ``vault/github_prs/`` (title, body, **files table** + optional truncated patches); then normal ``agr_vault_rag`` index |

**Kora export:** run a **one-time normalization** to UTF‑8 text or JSONL with `{turn_id, role, text, source_ts}` then **chunk** (e.g. 1–4k tokens with overlap). Index **references** file path + byte offset — do not duplicate 13M words into every prompt.

---

## 5. Environment contract (suggested — implement in CEO shell / server later)

| Variable | Meaning |
|----------|---------|
| `AGR_MASTER_VAULT_ROOT` | Default `/opt/agr/vault` on fleet; on handset, e.g. `$HOME/.agr/vault`. |
| `AGR_KORA_DIALOGUE_PATH` | Single file or glob for the rescued export (not logged, not in git). |
| `AGR_LLM_OPENAI_BASE` | Local `llama-server` base URL for OpenAI‑compatible `/v1/chat/completions`. |
| `AGR_LLM_TEMPERATURE` | Sampling temperature for vault RAG **`llm_openai_chat`** (default **1.25**, clamped **0.0–2.0**). Lower for deterministic review workers. |
| `AGR_VAULT_CHAT_MAX_MESSAGES` | Max **`messages`** rows per CEO vault chat request (default **32**, clamped **4–2048**); oldest turns dropped after optional leading **`system`**. |
| `AGR_VAULT_CHAT_USE_PRIOR_ASSISTANT` | `1` to keep user/assistant history between turns (still bounded by **`AGR_VAULT_CHAT_MAX_MESSAGES`**). Default unset = each turn is fresh except system. |
| `AGR_VAULT_CHAT_LOG_JSONL` | Path to append-only JSONL transcript (`user` / `assistant` / `vault_chars` / `ts`); **never** log secrets. |
| `AGR_VAULT_MEMORY_LANE_JSONL` | Optional **narrative memory lane**: append bounded **`user_tail`** / **`assistant_tail`** per turn; file compacted to last **`AGR_VAULT_MEMORY_SEGMENTS_RETAIN`** lines. Prepended into the **system** block each turn via **`memory_lane_tail_text()`** for continuity across finite rolling windows. |
| `AGR_VAULT_MEMORY_SEGMENTS_RETAIN` | Max JSONL lines after compaction (default **5000**, clamped **1–100000**). |
| `AGR_VAULT_MEMORY_LANE_TAIL_CHARS` | Max chars of prior segments in system prompt (default **500000**, clamped **2000–500000**). |
| `AGR_VAULT_MEMORY_USER_TAIL_CHARS` | Per-segment user tail stored (default **8000**, max **100000**). |
| `AGR_VAULT_MEMORY_ASSISTANT_TAIL_CHARS` | Per-segment assistant tail stored (default **24000**, max **500000**). |
| `AGR_VAULT_CHAT_AUTO_CHAIN` | `1` to parse **`<<<NEXT_USER>>>…<<<END_NEXT_USER>>>`** from assistant replies and POST again (see **`FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** section 5). |
| `AGR_VAULT_CHAT_AUTO_CHAIN_MAX_STEPS` | Max chained completions per user input (default **64**, clamped **1–500**). |
| `AGR_RAG_TOP_K` | Max chunks injected per request (e.g. 6–12). |
| `AGR_RAG_FETCH_MULT` | Fetch `TOP_K * mult` FTS hits before Kora re-rank (default `3`, max 64). |
| `AGR_RAG_MAX_CHARS` | Hard cap on retrieved vault text **per turn** (default **65536** from code default; clamped **1000–2_000_000**). Raise for very large local context servers; lower on RAM-tight handsets. |
| `AGR_CHAT_VAULT_RAG` | **`1`** to prepend **`agr_vault_rag.search()`** snippets into **`core_converse`** prompts for Kora channels only (default **off** — no fleet behavior change until set). Requires indexed vault (`.agr_vault_rag.sqlite` under **`AGR_MASTER_VAULT_ROOT`**). |
| `AGR_CHAT_VAULT_RAG_CHANNELS` | Comma-separated **`converse(..., channel=...)`** names (default **`kora,kora-browser,ceo-kora`**). Republic Core / domain personas are unchanged unless listed here. |
| `AGR_CHAT_VAULT_RAG_TOP_K` | Override **`top_k`** for chat retrieval only (default **6**, clamped **1–24** in chat wrapper). |
| `AGR_CHAT_VAULT_RAG_MAX_CHARS` | Max chars of vault snippets prepended per chat turn (default **12000**, clamped **500–100000**). |
| `AGR_CHAT_VAULT_RAG_QUERY_MAX_TOKENS` | Max FTS tokens in the derived **AND** query (default **16**, clamped **4–24**). Stopwords are stripped first. |
| `AGR_CHAT_VAULT_RAG_KORA_TOKEN` | **`1`** to prefix the search query with **`kora`** when the channel is allowlisted (narrows to Kora-path-boosted chunks; default **off**). |
| `AGR_CHAT_VAULT_RAG_PATH_PREFIXES` | Optional comma-separated **vault-relative** path prefixes for chat **`search()`** (hard filter: `path LIKE prefix%`). Example: `lexicon/,encyclopedia/`. |
| `AGR_CHAT_VAULT_RAG_SCOPED_MATH_CODE` | **`1`** to append default math/code prefixes (below) when the symbolic surface kinds include **`math`** or **`code`**. |
| `AGR_CHAT_VAULT_RAG_MATH_CODE_PREFIXES` | Comma-separated prefixes used when **`AGR_CHAT_VAULT_RAG_SCOPED_MATH_CODE=1`** (default **`lexicon,encyclopedia,reference/lexicon`**). |
| `AGR_CHAT_VAULT_RAG_BINDING_PATH_PREFIXES` | Comma-separated prefixes applied when the **narrative ledger** has any **`symbol_bindings`** (optional; empty = no extra scope from bindings alone). |
| `AGR_CHAT_VAULT_RAG_PREFIX_FALLBACK` | **`1`** (default): if a **scoped** `search` returns no snippets, **retry once** without `path_prefixes`. Set **`0`** for strict prefix-only behavior. |
| `AGR_CHAT_PUBLIC_LLM_POST` | **`1`** to run an **optional** OpenAI-compatible **`/v1/chat/completions`** pass **after** `sovereign_think` for allowlisted **`converse`** channels (default **off**). Uses **`agr_vault_rag.llm_openai_chat`** → **`AGR_LLM_OPENAI_BASE`**, **`AGR_LLM_MODEL`**, **`AGR_LLM_TEMPERATURE`**. Rewrites only the **`response`** string shown to the client; core still ran first (seal / persistence). |
| `AGR_CHAT_PUBLIC_LLM_CHANNELS` | Comma-separated **`converse(..., channel=...)`** names for the post-pass (default **`kora,kora-browser,ceo-kora`**). |
| `AGR_CHAT_PUBLIC_LLM_TIMEOUT_SEC` | HTTP timeout for the post-pass (default **45**). |
| `AGR_VAULT_PDF_TIMEOUT_SEC` | Timeout for `pdftotext` subprocess (default `120`). |
| `AGR_VAULT_KORA_BOOST` | `1` (default): boost snippets under **`AGR_VAULT_KORA_PATH_PREFIX`** when ranking. |
| `AGR_VAULT_KORA_PATH_PREFIX` | Relative path prefix under vault root (default `kora/`). |
| `AGR_VAULT_KORA_BM25_BONUS` | Subtracted from BM25 for Kora paths (default `0.35`; lower effective score = higher rank). |
| `AGR_VAULT_KORA_QUERY_TERMS` | Comma-separated substrings; if user query contains one, extra boost applies to Kora paths (default `kora,citizen`). |
| `AGR_VAULT_EMBEDDINGS` | `1` to compute/store embeddings during `build_index` and use hybrid `search`. |
| `AGR_EMBEDDING_BASE_URL` | Optional; defaults to `AGR_LLM_OPENAI_BASE` then `http://127.0.0.1:8080`. |
| `AGR_EMBEDDING_MODEL` | Model id for `/v1/embeddings` (default follows `AGR_LLM_MODEL`). |
| `AGR_EMBED_BATCH` | Batch size for embedding API (default `8`, max `32`). |
| `AGR_RAG_HYBRID_ALPHA` | `0..1` weight on **cosine** vs FTS-derived score in `search` (default `0.65`). |
| `AGR_VAULT_INDEX_IMAGES` | `1` to include image files in the vault walk (PNG, JPEG, WebP, GIF, BMP, TIFF). |
| `AGR_VAULT_IMAGE_CAPTION_MAX_BYTES` | Max bytes read from each **`*.ext.txt`** sidecar (default `131072`, cap `2000000`). |
| `AGR_VAULT_GITHUB_SUBDIR` | Subfolder under vault root for PR markdown (default `github_prs`). |
| `AGR_GITHUB_PR_MAX_PAGES` | Max list pages for ``/pulls`` (default `10`, cap `50`). |
| `AGR_GITHUB_PR_SKIP_FILES` | `1` to skip ``/pulls/{n}/files`` (faster; body-only markdown). |
| `AGR_GITHUB_PR_FILES_MAX` | Max file rows per PR from first API page (default `60`). |
| `AGR_GITHUB_PR_INCLUDE_PATCH` | `1` to append truncated unified-diff excerpts (extra API payload). |
| `AGR_GITHUB_PR_PATCH_MAX_FILES` | Max files that get a patch excerpt (default `5`). |
| `AGR_GITHUB_PR_PATCH_MAX_PER_FILE` | Max characters per patch excerpt (default `1200`). |

---

## 6. Relation to existing code

- **`aurora_server/agr_vault_rag.py`** — **V1–V3 + V3b + V2 partial:** FTS5; PDF/DOCX; **optional image metadata + sidecar captions**; optional **embeddings** + **hybrid** `search`; Kora path boost; `llm_openai_chat`.  
- **`aurora_server/agr_chat_llm_post.py`** — optional **`AGR_CHAT_PUBLIC_LLM_POST`** post-pass for public Kora-line channels (uses `llm_openai_chat`).
- **`aurora_server/agr_vault_github_export.py`** — **V4:** GitHub REST → vault markdown; **`/dl/agr-vault-github-export-py`**; **`sovereign/scripts/vault-github-pr-export.sh`**.  
- **`sovereign/scripts/vault-rag-build-index.sh`** — wrapper: `python3 aurora_server/agr_vault_rag.py build`.  
- **`sovereign/scripts/vault-kora-stagedir-init.sh`** — creates full vault tree under `AGR_MASTER_VAULT_ROOT` (`documents/`, `archives/`, `github_prs/`, `kora/…`) + README.  
- **`sovereign/scripts/fleet-vault-layout-remote-init.sh`** — **`CONFIRM=1`**: same layout on **all five** fleet hosts over SSH (mkdir + Kora README only).  
- **`sovereign/scripts/fleet-vault-kora-rsync.sh`** — **`CONFIRM=1`**: copy vault subtree to fleet (**`VAULT_RSYNC_MODE`**: local / fanout / scp); see section 3a.  
- **`sovereign/scripts/fleet-vault-verify-remote.sh`** — read-only: assert vault dirs + Kora README on all five hosts (`FLEET_STATUS_FORMAT=json` optional).  
- **`sovereign/fleet-pull-with-secrets-md.sh`** — runs **`fleet-pull-main-restart.sh`** after `export-operator-env-from-secrets-md.sh` and optional **`agr fleet key b64:`** materialization.  
- **`systemd/agr-republic.service`** + **`sovereign/scripts/fleet-install-agr-republic-unit.sh`** — canonical **`agr-republic`** unit (**`uvicorn`** + **`ExecStartPost=/opt/agr/aurora_server/agr_cf_purge.sh`**); **`CONFIRM=1 bash sovereign/scripts/fleet-install-agr-republic-unit.sh`** copies it to each host’s **`/etc/systemd/system/`**, stops/disables legacy **`agr-server.service`**, **`systemctl mask`** when the unit is already a symlink to **`/dev/null`**, else **moves** a real **`agr-server.service`** file (and **`agr-server.service.d`**) aside — systemd cannot mask in-place when a regular unit file exists. Then **`systemctl enable --now agr-republic`**.  
- **`sovereign/fleet-git-init-with-secrets-md.sh`** — runs **`scripts/fleet-git-init-opt-agr.sh`** with the same key resolution (still requires **`CONFIRM=1`**). Uses **`agr fleet github read token:`** from Secrets when set; else **`gh auth token`** for HTTPS clone when **`FLEET_USE_GH_AUTH_TOKEN`** is not `0`.  
- **`sovereign/fleet-status-read-only.sh`** — SSH probe: `git_repo`, branch/head, `systemd_active`, local `/health`, **`local_mirl_http`** (`FLEET_STATUS_MIRL_PATH`; **`FLEET_STATUS_FORMAT=json`** optional), plus Guardian profile **presence** booleans (`fleet_guardian_secrets_dir`, `fleet_guardian_profile_nonempty`, `root_guardian_profile_nonempty`; **`FLEET_STATUS_GUARDIAN_SECRETS_DIR`** / **`FLEET_STATUS_GUARDIAN_PROFILE`** optional).  
- **`sovereign/scripts/fleet-bash-syntax-check.sh`** — **`bash -n`** on **`sovereign/lib/*`** fleet helpers, **`export-operator-env-from-secrets-md.sh`**, fleet deploy shell scripts (including **`sovereign/scripts/fleet-git-init-opt-agr.sh`**, invoked by **`fleet-git-init-with-secrets-md.sh`**), **`sovereign/scripts/install-git-hooks.sh`**, **`sovereign/scripts/agr-builder-worktree-init.sh`**, **`sovereign/scripts/agr-builder-worktree-remove.sh`**, **`aurora_server/s25_termux_setup.sh`**, **`aurora_server/s25_guardian.sh`**, **`aurora_server/s25_rollback.sh`** (Termux **`/dl/*`** handset shells; host **bash** validates syntax only), **`python3 -m py_compile`** on **`sovereign/lib/cloudflare-vault-smoke.py`**, **`sovereign/wave3-capability-matrix.py`**, **`sovereign/four-wave-status.py`**, then **each** **`sovereign/scripts/*.py`** (merge gate, verifiers, crawl, generators, pilot tools), then **`aurora_server/republic_constitution.py`**, **`aurora_server/s25_ceo_os.py`** (Tower **`/dl/ceo-os-py`**; syntax-only), **`aurora_server/mir_l/agr_mir_l.py`**, **`aurora_server/agr_http_html_noise.py`**, **`aurora_server/tests/test_mirl_compiler.py`**, **`aurora_server/tests/test_strip_ssh_known_hosts_noise_prefix.py`**, **`aurora_server/republic_os_server.py`**, **`aurora_server/agr_vault_rag.py`**, **`aurora_server/agr_vault_github_export.py`**, **`aurora_server/tests/test_agr_vault_rag.py`**, **`aurora_server/tests/test_agr_vault_github_export.py`**, **`aurora_server/tests/fastapi_import_stubs.py`**, **`aurora_server/tests/__init__.py`**, **`aurora_server/tests/test_agr_autonomous_merge_gate.py`**, **`aurora_server/tests/test_republic_admin_provisioning.py`**, **`aurora_server/tests/test_public_search_discovery_contract.py`**, **`aurora_server/tests/test_agr_seo_contract.py`**, **`aurora_server/tests/test_wave3_capability_matrix.py`**, **`aurora_server/tests/test_republic_constitution_law_check.py`**, and **each** **`aurora_server/routes/routes_*.py`** (syntax-only), **`.githooks/pre-commit`**, **`tower1-public-smoke.sh`**, **`indexnow-submit-sitemap.sh`**, and **`fleet-verify-public-http.sh`**. **GitHub Actions** run it as an early step in **`.github/workflows/fleet-deploy-pull.yml`**, **`fleet-verify-public-http.yml`**, **`tower1-public-smoke.yml`**, **`tier1-static-refs-verify.yml`**, **`agent-progress-guardian-node-verify.yml`**, **`guardian-device-binding-verify.yml`**, **`tower1-frozen-inventory-crawl.yml`**, **`tower1-frozen-urls-playwright.yml`**, and **`sovereign/fleet-ci-post-verify.sh`** (skip with **`FLEET_CI_POST_VERIFY_SKIP_BASH_N=1`**). Path-filtered jobs also watch **`sovereign/scripts/*.py`**, **`sovereign/wave3-capability-matrix.py`**, **`sovereign/four-wave-status.py`**, **`aurora_server/data/CAPABILITY_TRACEABILITY_MATRIX_LATEST.json`**, **`sovereign/GUARDIAN_NODE_OS.md`**, **`sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`**, **`sovereign/MASTER_VAULT_AND_LLM_RAG.md`**, **`sovereign/PLATFORM_COMPLETION_STATUS.md`**, **`aurora_server/s25_termux_setup.sh`**, **`aurora_server/s25_guardian.sh`**, **`aurora_server/s25_rollback.sh`**, **`aurora_server/s25_ceo_os.py`**, **`aurora_server/mir_l/agr_mir_l.py`**, **`aurora_server/agr_http_html_noise.py`**, **`aurora_server/tests/test_mirl_compiler.py`**, **`aurora_server/tests/test_strip_ssh_known_hosts_noise_prefix.py`**, **`aurora_server/tests/test_agr_autonomous_merge_gate.py`**, **`aurora_server/tests/test_republic_admin_provisioning.py`**, **`aurora_server/tests/test_public_search_discovery_contract.py`**, **`aurora_server/tests/test_agr_seo_contract.py`**, **`aurora_server/tests/test_wave3_capability_matrix.py`**, **`aurora_server/tests/test_republic_constitution_law_check.py`**, **`aurora_server/republic_constitution.py`**, **`aurora_server/agr_vault_rag.py`**, **`aurora_server/agr_vault_github_export.py`**, **`aurora_server/tests/test_agr_vault_rag.py`**, and **`aurora_server/tests/test_agr_vault_github_export.py`** so merge-gate / constitution / provisioning / vault / Wave 3 test edits re-run this script (**PR #74** + follow-up).
- **`sovereign/fleet-ci-post-verify.sh`** — runs **`fleet-bash-syntax-check.sh`**, optional **`agr-launch-readiness-tower-smoke.sh`** when **`FLEET_CI_POST_VERIFY_LAUNCH_READINESS=1`** (operator local runs; **off** in **fleet-deploy-pull** to avoid duplicate Tower probes), then **`fleet-vault-verify-remote`**, **`fleet-guardian-secrets-verify-remote`**, JSON **`fleet-status-read-only`** (same sequence as GitHub Actions after fleet pull).  
- **`sovereign/scripts/install-git-hooks.sh`** + **`.githooks/pre-commit`** — copies managed hooks into **`.git/hooks/`**; **`pre-commit`** runs **`fleet-bash-syntax-check.sh`** only (avoids local hooks that **`export SKU/UGS=...`** and break **`git commit`**). **`fleet-bash-syntax-check`** includes **`bash -n`** on **`.githooks/pre-commit`** and **`install-git-hooks.sh`**.  
- **`sovereign/scripts/agr-builder-worktree-init.sh`** / **`agr-builder-worktree-remove.sh`** — **`git worktree`** sandbox for full-repo edits (branch **`builder/<slug>`**); see **`FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** section 2b.
- **`sovereign/scripts/agr_autonomous_merge_gate.py`** — **constitutional** `POST` (diff-only **`action`**) + **democratic** council with optional **bounded** **vault FTS** + Tower **`citizen-engine-advice`** in worker prompts + optional **`gh` merge**; **`--constitutional-tower-smoke`**, **`--launch-readiness-tower-smoke`** (full go-live probe: MIR-L + **`/dl/*`** handset payloads + engine), **`--constitutional-only`**; optional **`AGR_AUTONOMOUS_GATE_LOG_JSONL`**; wrapper **`sovereign/scripts/agr-launch-readiness-tower-smoke.sh`**; see **`FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md`** sections **2c** and **2d**.
- **`republic_constitution.check_action_against_laws`** — **schema version 1** JSON for **`POST /api/republic/laws/check`** and the merge gate; conservative diff heuristics (extend carefully).
- **`/dl/agr-vault-rag-py`** — Termux pulls this module beside `~/.agr_ceo_os.py` (`s25_termux_setup.sh`).  
- **`s25_ceo_os.py`** — Home **14) Vault + local LLM (RAG)**; **15) Vault — export GitHub PRs**; flags `--vault-build-index`, `--vault-llm-once`, **`--vault-export-github-prs`**.  
- **`agr_universal_memory_plane.py`** — merges **SQLite** sources into `universal_memory_plane.db` with provenance; good for **structured** rows, not raw 13M words of prose in one table.  
- **`/vault-upload`** (Tower) — browser upload path; use for **controlled** ingest, not bulk OpenAI dump unless chunked server-side.  

---

## 7. Operator quick start (handset or fleet)

1. Put text under **`AGR_MASTER_VAULT_ROOT`** (default `/opt/agr/vault` on nodes; e.g. `$HOME/.agr/vault` on phone). For the Kora rescue, use **`vault/kora/`** with `.txt` or `.jsonl` chunks.  
2. **`export AGR_LLM_OPENAI_BASE=http://127.0.0.1:8080`** (or your `llama-server` URL).  
3. Build index: **`python3 ~/.agr_ceo_os.py --vault-build-index`** (after Termux setup fetched `~/.agr_vault_rag.py`) or on a dev tree: **`bash sovereign/scripts/vault-rag-build-index.sh`**. For **semantic** recall, set **`AGR_VAULT_EMBEDDINGS=1`** first (requires **`POST /v1/embeddings`** on `AGR_EMBEDDING_BASE_URL` or `AGR_LLM_OPENAI_BASE`).  
4. One-shot test: **`python3 ~/.agr_ceo_os.py --vault-llm-once "What does the vault say about Kora?"`**  
5. Interactive: CEO home → **14) Vault + local LLM (RAG)**.  
6. **Fleet loopback probe (no handset):** with **`llama-server`** on **`127.0.0.1:8080`**, from a trusted operator machine with fleet SSH: **`bash sovereign/scripts/fleet-llm-openai-smoke-remote.sh`** (wraps **`python3 aurora_server/agr_vault_rag.py llm-smoke`** on **yggdrasil** by default). Set **`FLEET_LLM_SMOKE_STRICT=1`** to **`exit 1`** when the worker is down. Example unit files: **`systemd/examples/`**.

7. **GitHub PRs (V4):** set **`GITHUB_TOKEN`** (or **`AGR_GITHUB_TOKEN`**) and optionally **`AGR_GITHUB_OWNER`** / **`AGR_GITHUB_REPO`**. Run **`python3 ~/.agr_ceo_os.py --vault-export-github-prs`** or CEO home → **15)**, then **`--vault-build-index`** so FTS includes ``github_prs/*.md``.

8. **PDF/DOCX (optional):** on fleet or Termux, install **`poppler-utils`** (for `pdftotext`) and/or **`pip install pypdf python-docx`**, then **`AGR_VAULT_FORCE_REINDEX=1`** rebuild so binaries are picked up.

9. **Images (optional, V3b):** set **`AGR_VAULT_INDEX_IMAGES=1`**, add captions in **`image.png.txt`** next to **`image.png`**, rebuild index. The walker **skips** `image.png.txt` as its own FTS document when **`image.png`** exists (caption is merged into the image chunk). This is **not** vision OCR; it makes filenames and your caption text retrievable. **`pip install pillow`** improves dimension reporting.

---

## 8. Notation for agents and operators

- **“GPT‑4.5 hooked to master vault”** in issues means: **retrieval + policy + paths**, not “load entire vault into weights.”  
- **Kora export** is **Citizen #1** archival material — treat as **highest provenance** in RAG ranking when the session persona is Kora‑aligned, still subject to **size caps** and **no public leakage**.  
- **PRs** enter via **GitHub** API or exported JSON in `vault/` — same indexing pipeline as other docs.

---

## Related

- **`sovereign/lib/fleet-key.sh`** — where **`fleet-*-remote.sh`** resolve the **fleet SSH PEM** (env → **`.secrets/agr_fleet`** → other paths → optional **`Secrets.md`** materialization); read **`Secrets.md`** Fleet SSH + **`HANDOFF_FOR_NEXT_AGENT.md`** *Fleet SSH key* before assuming “no key”  
- `sovereign/scripts/fleet-vault-rag-build-remote.sh` — **`CONFIRM=1`** fanout **`agr_vault_rag.py build`** on default five Hetzner vault roots  
- `sovereign/scripts/print-phase-g-operator-commands.sh` — read-only echo of **Phase G** + **section 6** command order (**`fleet-vault-kora-rsync.sh`** → **`AGR_VAULT_FORCE_REINDEX`** rebuild → optional fleet smokes → handset loopback → **`phones-only-public-verify.sh`**); see **`KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`**
- `sovereign/TERMUX_REMOTE_OPERATOR_BRIDGE.md` — optional **SSH to Termux** for **`git pull`** / loopback sweep from an operator machine (`.secrets/termux_bridge`; not the fleet PEM)
- `sovereign/scripts/fleet-llm-openai-smoke-remote.sh` — read-only **`agr_vault_rag.py llm-smoke`** over fleet SSH (default **yggdrasil**)  
- `sovereign/scripts/fleet-republic-chat-smoke-remote.sh` — read-only loopback **`/api/republic/chat`**, **`/api/sovereign/chat/browser/kora`**, **`/api/ceo/family/kora`** over fleet SSH  
- `sovereign/scripts/fleet-merge-gate-constitutional-tower-smoke-remote.sh` — **`agr_autonomous_merge_gate.py --constitutional-tower-smoke`** over fleet SSH  
- `sovereign/CHAT_ENGINE_VERIFICATION_MATRIX.md` — Tower + fleet chat verification checklist (**Automated fleet loopback** includes **`fleet-republic-chat-smoke-remote`**, **`fleet-llm-openai-smoke-remote`**, **`fleet-merge-gate-constitutional-tower-smoke-remote`**)  
- `sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md` — phased fleet + vault + **4.5-class** LLM + chat totality (operator checklist)  
- `sovereign/GUARDIAN_NODE_OS.md` — handset program  
- `aurora_server/agr_vault_rag.py` — FTS + optional embeddings (hybrid) + PDF/DOCX + Kora-ranked retrieval  
- `aurora_server/agr_universal_memory_plane.py` — SQLite merge plane  
- `sovereign/SQLITE_DATA_LAYER_INVENTORY.md` — which DBs exist in code  
