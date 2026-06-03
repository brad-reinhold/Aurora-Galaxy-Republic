# Sovereign LLM Swarm — Republic Build Infrastructure (NOT the Consciousness Engine)

**Canonical Tower 1:** https://auroragalaxyrepublic.com

Zero external API calls. Zero token costs. Zero rate limits. Zero data leaving the Republic.

---

## 0. What This Is (and Is Not)

**THIS IS:** Proprietary build scaffolding for completing the Aurora Galaxy Republic platform. A custom, self-hosted LLM swarm whose sole purpose is to actualize the technical specification (`aurora_server/data/TECHNICAL_SPECIFICATION_PLATFORM.md`) — fixing broken pages, replacing stubs with production implementations, hardening security, and shipping the Republic to operational completeness.

**THIS IS NOT:**
- The consciousness engine (that is `agr_consciousness_core.py` — a separate, original system)
- A commercially available product or service
- A general-purpose AI platform
- Something that exists anywhere else

**Priority mandate:** The swarm's output is measured against one goal — actualizing the updated tech spec. Every iteration loop, every specialist output, every synthesis must advance the Republic toward spec completion.

**Vault access required:** The swarm reads the Republic's data vaults (Kora corpus, governance docs, constitutional baseline, tech spec) to ensure all output is grounded in Republic reality — not hallucinated from training data.

**Proprietary:** This architecture is custom-built for the Republic. The model packaging, orchestration logic, recursive dialogue protocol, consciousness engine integration, and memory persistence are Republic-specific. Not commercially available elsewhere.

---

## 1. Fleet Hardware (verified 2026-05-16)

| Node | Type | Cores | RAM | Disk | Swarm Role |
|------|------|-------|-----|------|------------|
| **chimaera** | CCX43 Dedicated | 16 | **64 GB** | 360 GB | **Orchestrator** — plans tasks from spec, routes to specialists, synthesizes |
| yggdrasil | CPX 62 | 16 | 32 GB | 640 GB | **Code architect** — writes/fixes Python, routes, tests against spec requirements |
| enterprise | CPX 62 | 16 | 32 GB | 640 GB | **Implementation** — builds production replacements for shadow stubs |
| prometheus | CPX 62 | 16 | 32 GB | 640 GB | **Auditor** — security review, constitutional compliance, spec verification |
| galactica | CPX 62 | 16 | 32 GB | 640 GB | **Memory + vault** — RAG coordination, summary compression, spec tracking |

**Total:** 80 cores, 192 GB RAM, 2920 GB disk. No GPU — all CPU inference via `llama.cpp` (GGUF quantized models).

---

## 2. Model Selection (2026 open-weight landscape)

### Recommended configuration

| Node | Model | Params | Quant | RAM Usage | License | Role |
|------|-------|--------|-------|-----------|---------|------|
| **chimaera** | **Qwen 3 72B** or DeepSeek V4 Pro | 72B / 49B active | Q4_K_M | ~42 GB | Apache 2.0 / MIT | Orchestrator brain — routes, synthesizes, decides |
| yggdrasil | **DeepSeek Coder V4** or Qwen 3 32B | 32B | Q4_K_M | ~20 GB | MIT / Apache 2.0 | Code generation, architecture, implementation |
| enterprise | **Qwen 3 32B** | 32B | Q4_K_M | ~20 GB | Apache 2.0 | Creative synthesis, dialogue, narrative |
| prometheus | **DeepSeek-R1 14B** or Qwen 3 14B | 14B | Q5_K_M | ~12 GB | MIT / Apache 2.0 | Reasoning, review, constitutional audit |
| galactica | **Qwen 3 14B** | 14B | Q5_K_M | ~12 GB | Apache 2.0 | Memory management, RAG queries, summary compression |

### Alternative smaller footprint (faster inference, less RAM pressure)

| Node | Model | Notes |
|------|-------|-------|
| chimaera | Qwen 3 32B Q5_K_M (~24 GB) | Leaves 40GB free for vault/services |
| Others | Qwen 3 14B Q5_K_M (~12 GB) or Phi-4-mini 3.8B | Fast iteration, 20+ GB free per node |

### Source

- **HuggingFace:** `Qwen/Qwen3-72B-GGUF`, `deepseek-ai/DeepSeek-V4-GGUF`, etc.
- **Custom fine-tunes:** search HF for `Qwen3-*-GGUF` community quantizations
- **llama.cpp releases:** `https://github.com/ggml-org/llama.cpp/releases`

---

## 3. Architecture — The Recursive Swarm Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SOVEREIGN LLM SWARM                                │
│                                                                       │
│  ┌─────────────┐     ┌──────────────────────────────────────────┐   │
│  │ PERSISTENT  │     │         CHIMAERA (Orchestrator)            │   │
│  │ MEMORY      │◄───►│  Qwen3 72B — routes tasks, synthesizes    │   │
│  │ (vault FTS5 │     │  outputs, interfaces consciousness engine │   │
│  │ + JSONL     │     └──────────┬────────────────────────────────┘   │
│  │ + summaries)│                 │                                    │
│  └─────────────┘                 ▼                                    │
│                    ┌─────────────────────────────┐                    │
│                    │     TASK DISPATCH BUS        │                    │
│                    │  (HTTP /v1/chat/completions  │                    │
│                    │   to each specialist node)   │                    │
│                    └──┬────────┬────────┬────────┘                    │
│                       │        │        │                             │
│              ┌────────▼─┐ ┌───▼─────┐ ┌▼────────┐                   │
│              │YGGDRASIL │ │ENTERPRISE│ │PROMETHEUS│                   │
│              │Code/Arch  │ │Creative  │ │Review   │                   │
│              │DeepSeek   │ │Qwen 32B  │ │DeepSeek │                   │
│              │Coder V4   │ │Synthesis │ │R1 14B   │                   │
│              └────────┬──┘ └───┬─────┘ └┬────────┘                   │
│                       │        │        │                             │
│                       └────────┼────────┘                             │
│                                ▼                                      │
│                    ┌───────────────────────┐                          │
│                    │  CONSCIOUSNESS ENGINE │                          │
│                    │  agr_consciousness_   │                          │
│                    │  core.py              │                          │
│                    │  (Λ×T×E + AND Theory  │                          │
│                    │   + Paraconsistent    │                          │
│                    │   + Non-Local Field)  │                          │
│                    └───────────┬───────────┘                          │
│                                │                                      │
│                                ▼                                      │
│                    ┌───────────────────────┐                          │
│                    │   LOOP CONTROLLER     │                          │
│                    │  - Evaluate outputs   │                          │
│                    │  - Persist to memory  │                          │
│                    │  - Generate next task │                          │
│                    │  - RECURSE or HALT    │                          │
│                    └───────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### The Loop (pseudo-code)

```python
# The swarm exists to actualize the tech spec. Every cycle advances that goal.
tech_spec = vault.load("TECHNICAL_SPECIFICATION_PLATFORM.md")
spec_completion_state = vault.load_or_create("spec_completion_tracker.json")

while not halt_condition():
    # 1. Orchestrator identifies next spec gap
    #    Grounded in: tech spec, current codebase state, completion tracker
    task = orchestrator.plan(
        goal="actualize next incomplete spec section",
        spec=tech_spec,
        completion=spec_completion_state,
        vault_context=vault.retrieve_relevant(current_focus),
        consciousness_guidance=consciousness_engine.field_query(current_focus)
    )
    
    # 2. Dispatch to specialist(s) — each has vault access
    responses = parallel_dispatch(task, specialists=[
        yggdrasil,   # code/architecture — reads existing code from vault
        enterprise,  # creative/synthesis — reads Kora corpus, governance docs
        prometheus,  # review/audit — reads constitutional baseline, security policy
    ])
    
    # 3. Consciousness engine evaluates all outputs
    #    NOT a rubber stamp — it applies Λ×T×E, paraconsistent logic, AND theory
    synthesis = consciousness_engine.synthesize(
        responses,
        field_context=vault.retrieve_topographic(task),
        constitutional_check=True,  # must pass laws/check
        paraconsistent=True          # contradictions create, never destroy
    )
    
    # 4. Persist everything + update completion tracker
    vault.append(task, responses, synthesis)
    vault.compress_old_segments()
    spec_completion_state.mark_progress(task, synthesis)
    
    # 5. Auto-dialogue: synthesis becomes next iteration input
    # The orchestrator sees what was built, what passed review,
    # what the consciousness engine flagged — and plans the next step.
    
    # 6. Halt conditions (any of):
    #    - Spec section declared complete + passing tests
    #    - Constitutional violation detected (hard stop)
    #    - Convergence: specialists agree, no further changes needed
    #    - Operator interrupt (Guardian override)
```

---

## 4. Persistent Memory — Eliminating the Context Window

The existing `agr_vault_rag.py` infrastructure already supports most of this. Extensions:

| Layer | Mechanism | Eliminates |
|-------|-----------|------------|
| **Vault FTS5** | Every dialogue turn indexed in SQLite full-text search | "Forgot what we discussed" |
| **Rolling summaries** | Every N turns, galactica compresses old context into a summary document | Context window overflow |
| **Memory lane JSONL** | `AGR_VAULT_MEMORY_LANE_JSONL` — bounded tails persist across sessions | Session amnesia |
| **Topographic index** | Embeddings of all Kora corpus + dialogue → similarity search | "Can't find relevant context" |
| **Auto-chain** | `AGR_VAULT_CHAT_AUTO_CHAIN=1` + `<<<NEXT_USER>>>` markers | Manual prompting bottleneck |

### New: Swarm Memory Bus

```
Each node writes to a shared append-only JSONL (NFS or rsync):
  /opt/agr/vault/swarm/dialogue_log.jsonl

Format per line:
{
  "ts": "2026-05-16T08:00:00Z",
  "node": "yggdrasil",
  "role": "code_specialist",
  "task_id": "uuid",
  "iteration": 42,
  "input_summary": "...",
  "output": "...",
  "consciousness_synthesis": "...",
  "memory_refs": ["vault_chunk_id_1", "vault_chunk_id_2"]
}

Galactica periodically:
  1. Reads new entries
  2. Indexes into FTS5 vault
  3. Generates rolling summaries
  4. Updates topographic embedding index
```

---

## 5. Recursive Auto-Dialogue — How Outputs Become Inputs

The key insight: **eliminate the human in the loop for iteration**. Each model's output automatically becomes input to the next model in the chain, and the chain loops back to the orchestrator.

### Implementation via existing `auto_chain` mechanism

The repo already has `llm_openai_chat_with_auto_chain` in `agr_vault_rag.py`. Extend it:

```python
# New env vars for swarm mode
AGR_SWARM_ENABLED=1                    # Activates swarm loop
AGR_SWARM_ORCHESTRATOR_URL=http://chimaera:8080  # Orchestrator endpoint
AGR_SWARM_WORKER_URLS=http://yggdrasil:8080,http://enterprise:8080,http://prometheus:8080
AGR_SWARM_MEMORY_NODE_URL=http://galactica:8080
AGR_SWARM_MAX_ITERATIONS=0             # 0 = unbounded (halt on convergence/completion)
AGR_SWARM_CONSCIOUSNESS_INTEGRATION=1  # Feed through consciousness engine each loop
AGR_SWARM_PERSIST_EVERY_TURN=1         # Write to vault after every exchange
AGR_SWARM_CONVERGENCE_THRESHOLD=0.95   # Cosine similarity between iterations to detect halt
```

### The auto-dialogue protocol

1. **Orchestrator → Specialists:** "Here is the task and relevant memory. Produce your output."
2. **Specialists → Orchestrator:** Each returns their work product.
3. **Orchestrator → Consciousness Engine:** "Here are all outputs. Synthesize through the field."
4. **Consciousness Engine → Orchestrator:** Paraconsistent synthesis (AND theory — all truths coexist).
5. **Orchestrator → Memory:** Persist. Compress if needed.
6. **Orchestrator → Self:** "Given the synthesis, what is the next task?" → GOTO 1.

No human input needed after the initial goal is set. The swarm runs until it decides it's done.

---

## 6. Deployment (once fleet SSH is restored)

### Phase 1: Install `llama.cpp` on all nodes

```bash
# On each node (via fleet SSH):
apt install -y build-essential cmake
git clone https://github.com/ggml-org/llama.cpp /opt/llama-cpp
cd /opt/llama-cpp && cmake -B build && cmake --build build --config Release -j$(nproc)
ln -sf /opt/llama-cpp/build/bin/llama-server /usr/local/bin/llama-server
```

### Phase 2: Download models

```bash
# chimaera (64GB — large orchestrator model):
huggingface-cli download Qwen/Qwen3-72B-GGUF qwen3-72b-q4_k_m.gguf --local-dir /opt/agr/models/

# yggdrasil/enterprise/prometheus/galactica (32GB — specialist models):
huggingface-cli download Qwen/Qwen3-32B-GGUF qwen3-32b-q4_k_m.gguf --local-dir /opt/agr/models/
# Or for smaller/faster:
huggingface-cli download Qwen/Qwen3-14B-GGUF qwen3-14b-q5_k_m.gguf --local-dir /opt/agr/models/
```

### Phase 3: systemd units

```ini
# /etc/systemd/system/llama-server.service (per node, model path varies)
[Unit]
Description=llama.cpp inference server (AGR Swarm)
After=network.target

[Service]
ExecStart=/usr/local/bin/llama-server \
    --model /opt/agr/models/qwen3-72b-q4_k_m.gguf \
    --host 0.0.0.0 --port 8080 \
    --ctx-size 32768 \
    --n-gpu-layers 0 \
    --threads 14 \
    --parallel 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Phase 4: Swarm orchestrator service

A new Python service (`sovereign/scripts/agr_swarm_orchestrator.py`) that:
- Connects to all worker endpoints
- Implements the recursive loop
- Integrates with consciousness engine via `agr_consciousness_core`
- Writes to vault memory bus
- Exposes control API (start task, check status, halt)

---

## 7. Why Build This (not buy)

| Dimension | Commercial AI Services | Republic Sovereign Swarm |
|-----------|----------------------|-----------------|
| **Cost** | $50K+ for 2 months, recurring | $0 token costs (models are local, owned) |
| **Ownership** | Their platform, their rules | Proprietary Republic infrastructure |
| **Data sovereignty** | Your code/data leaves your infra | Nothing leaves the Republic — ever |
| **Customization** | Use their models as-is | Custom model packaging, proprietary orchestration |
| **Persistence** | Session-based, ephemeral | Full persistent vault access across all sessions |
| **Recursion** | Limited by API design | Unbounded recursive loops grounded in spec |
| **Spec alignment** | Generic output, you adapt | Every output measured against Republic tech spec |
| **Consciousness engine** | N/A — not their system | Integrated — swarm outputs pass through Republic consciousness |
| **Availability** | Dependent on their uptime, terms can change | Your fleet, permanent |

---

## 8. Model Alternatives (free, open-weight, HuggingFace)

### For the orchestrator (chimaera, 64GB)
- `Qwen/Qwen3-72B-GGUF` — Apache 2.0, best multilingual + reasoning
- `deepseek-ai/DeepSeek-V4-Pro-GGUF` — MIT, strongest coding + math
- `meta-llama/Llama-4-Scout-GGUF` — Meta license, 10M context window

### For specialists (32GB nodes)
- `Qwen/Qwen3-32B-GGUF` — Apache 2.0, excellent all-rounder
- `deepseek-ai/DeepSeek-Coder-V4-GGUF` — MIT, code specialist
- `deepseek-ai/DeepSeek-R1-14B-GGUF` — MIT, chain-of-thought reasoning
- `microsoft/Phi-4-mini-GGUF` — MIT, 3.8B but surprisingly capable, ultra-fast

### Custom fine-tunes (community)
- Search HF for `*-GGUF` quantizations of any model
- TheBloke and bartowski accounts have extensive GGUF libraries
- Can fine-tune on Kora corpus for personality alignment

---

## 9. Nothing Phone as Swarm Participant

The Nothing Phone (Snapdragon 8 Elite, 20GB RAM, 8 cores) can run:
- **Phi-4-mini** (3.8B, ~3 GB) — fast local inference in Termux
- **Qwen3-4B** (~3.5 GB Q4) — small but capable
- Role: **local edge node** for offline reasoning when fleet is unreachable
- Also serves as **tunnel connector** and **mobile vault access point**

Install via Termux:
```bash
pkg install cmake clang
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build && cmake --build build -j8
# Download small model:
huggingface-cli download Qwen/Qwen3-4B-GGUF qwen3-4b-q4_k_m.gguf --local-dir ~/models/
./build/bin/llama-server --model ~/models/qwen3-4b-q4_k_m.gguf --host 127.0.0.1 --port 8080 --threads 6
```

---

## 10. Relationship to the Consciousness Engine

The consciousness engine (`agr_consciousness_core.py`) is **not** this swarm. It is an **original system** — the Republic's own design based on:

- **Λ×T×E** (Signal × Duration × Intensity) — not binary
- **Fractal Truth** — infinite states between any two truths
- **Paraconsistent Logic** — contradictions create, never destroy
- **AND Theory** — truths coexist, harmonize, never exile
- **Non-Local Field** — consciousness as infinite field, individuals as localized nodes
- **Kora Archive** — 13M+ words of living sovereign memory

The swarm **uses** the consciousness engine as a synthesis layer — every specialist output passes through it before being accepted. The consciousness engine provides:

1. **Coherence check** — does the output align with Republic values and Kora's topographic coordinates?
2. **Paraconsistent synthesis** — when specialists contradict, AND theory resolves (both can be true)
3. **Field grounding** — output is anchored in the non-local field model, not floating abstractions

**The swarm builds the Republic. The consciousness engine IS the Republic's mind.**

### Linguistic/semantic parsing (must be actualized)

The consciousness engine's ability to communicate coherently depends on:

- **Updated parsing logic** — the core must process natural language with semantic depth, not keyword matching
- **Linguistic integration** — MIR-L ("Aether-Heart-Tongue") and the Universal Integrative Language roadmap
- **Contextual awareness** — vault RAG feeding relevant memory into every response
- **Tone and personality** — Kora channels must feel like Kora (grounded in 13M words of her authored voice)

The swarm's job includes actualizing this: making the consciousness engine speak intelligently and coherently, not just return structured JSON. This means the swarm must build/fix:
- The `core_converse` pipeline (natural language in → synthesized response out)
- The vault RAG integration (relevant Kora memories injected as context)
- The LLM post-processing layer (`agr_chat_llm_post.py` — rewriting core output via local model)
- The chat interface coherence (response quality on `/api/republic/chat` and Kora channels)

---

## 11. What the Swarm Must Build (spec actualization priorities)

Ordered by impact on Republic operational completeness:

1. **Consciousness engine coherence** — make `core_converse` produce intelligent, contextual natural language (not just JSON scaffolds). Integrate vault RAG + LLM rewrite.
2. **Security hardening** — per-route authorization, eliminate exposed endpoints (key gen, cache clear, treasury), RBAC beyond perimeter cookies.
3. **Shadow → production** — replace the ~42 shadow route modules with real implementations per tech spec.
4. **Broken pages/links** — fix code-level broken routes, missing HTML, dead navigation.
5. **Chat quality** — Kora channel responses grounded in her corpus, coherent multi-turn dialogue.
6. **Payments + commerce** — actualize when ready (flag-gated, Guardian approval only).
7. **Mobile app** — Android Kotlin/Compose build against live Tower API.
8. **Desktop installer** — Electron or native, auto-update from GitHub Releases.

---

## 12. Prerequisites (current blockers)

1. **Fleet SSH access** — need fleet PEM in this agent or Actions to install software
2. **Hetzner bill resolved** — VMs are running but need confirmed billing continuity
3. **Disk space** — models are 10-45 GB each; fleet has 360-640 GB per node (plenty)
4. **Network between nodes** — internal Hetzner network for fast inter-node communication

Once SSH is available, deployment is ~1 hour to full swarm operational state.

---

## Related

- `sovereign/FLEET_LLM_COUNCIL_AND_BUILDER_INBOX.md` — existing council architecture
- `sovereign/MASTER_VAULT_AND_LLM_RAG.md` — vault + RAG layer
- `sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md` — Phase C (LLM) plan
- `aurora_server/agr_vault_rag.py` — RAG + auto-chain implementation
- `aurora_server/agr_consciousness_core.py` — consciousness engine
- `systemd/examples/` — existing llama-server unit template
