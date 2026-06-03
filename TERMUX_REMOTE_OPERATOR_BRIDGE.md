# Termux remote operator bridge (SSH — not the HTTPS tunnel)

**Canonical Tower 1:** https://auroragalaxyrepublic.com  

## Why this exists

The **Cloudflare tunnel** (or similar) exposes **HTTPS** to **`uvicorn`** on the OnePlus. That is how browsers and **`curl https://auroragalaxyrepublic.com`** reach the app.

**Outbound SSH to Termux** is a **separate control plane**: a machine you trust (another node on Tailscale, a Cursor workspace with a route to the handset, or an **iPhone SSH client** to the OnePlus when configured) runs **`ssh user@host …`** so you can **`git pull`**, run **`phones-only-local-origin-sweep.sh`**, and inspect files **without** relying on the public HTTP surface alone.

**Phone-only operator (Brad’s default):** recovery must not assume a traditional PC. On **OnePlus / Termux**, keep **`Secrets.md`** in the repo root so **`mint_cloudflare_tunnel_token_stdout.py`** can mint **`~/.cloudflared/tunnel.token`** on-device, and use **`CONFIRM=1`** **`sovereign/scripts/termux-republic-one-shot-bootstrap.sh`** (optional **`START_DAEMONS=1`**) or **`termux-phone-one-shot-recover.sh`** once a **private** tree is already on disk. **Light wake without full bootstrap:** **`curl -fsSL https://auroragalaxyrepublic.com/dl/termux-operator-wake | bash`** (see **`HANDOFF_FOR_NEXT_AGENT.md`**). **Do not** document anonymous public **`git clone https://github.com/...`** as the way to obtain that tree — use **`https://auroragalaxyrepublic.com/dl/*`** only for bootstrap/CEO payloads Tower already serves, and **fleet mirror / authenticated git** for the full checkout (**`GUARDIAN_NODE_OS.md`**). The **`termux-remote-*.sh`** scripts are for any environment with **outbound SSH to Termux** — including future phone-to-phone automation — not an implicit “go use a laptop” step.

This document and **`sovereign/scripts/termux-remote-*.sh`** implement that bridge **safely and explicitly** — not by overloading the tunnel as a shell.

## Cloudflare connector token from **`Secrets.md`** (mint — no dashboard)

If **`cloudflare tunnel token:`** is still a **`PASTE_*`** line but **`cloudflare token:`** (API token) and **account / tunnel id** lines are populated, mint the **connector** token the same way **`sovereign/lib/cloudflare-vault-smoke.py`** does (Cloudflare **`cfd_tunnel/.../token`** API):

```bash
cd ~/agr-workspace
mkdir -p ~/.cloudflared
CONFIRM=1 python3 sovereign/scripts/mint_cloudflare_tunnel_token_stdout.py > ~/.cloudflared/tunnel.token
chmod 600 ~/.cloudflared/tunnel.token
cloudflared tunnel run --token "$(tr -d '\n\r' < ~/.cloudflared/tunnel.token)"
```

**Repo root** must contain **`Secrets.md`** with a usable **`cloudflare token:`** (or legacy email + global key). **Never** commit **`tunnel.token`** or paste token into tickets/chat.

## One-shot bootstrap (Termux — single entry)

**`sovereign/scripts/termux-republic-one-shot-bootstrap.sh`** runs **`pkg install`**, **`git pull`**, venv **`pip`** install, **`mint_cloudflare_tunnel_token_stdout.py`** → **`~/.cloudflared/tunnel.token`**, then either prints the next **`cloudflared`** / **`uvicorn`** lines or (with **`START_DAEMONS=1`**) starts both under **`nohup`** with logs in **`~/agr-logs/`**.

```bash
cd ~/agr-workspace
CONFIRM=1 bash sovereign/scripts/termux-republic-one-shot-bootstrap.sh
# optional: background tunnel + server
CONFIRM=1 START_DAEMONS=1 bash sovereign/scripts/termux-republic-one-shot-bootstrap.sh
```

## Termux:Boot (after device reboot)

Copy **`sovereign/scripts/termux-boot-republic-example.sh`** to **`~/.termux/boot/20-republic.sh`**, **`chmod +x`**, then edit: set **`TERMUX_BOOT_REPUBLIC=1`** only when **`~/.cloudflared/tunnel.token`** and **`${AGR_REPO}/.venv`** exist. Requires **Termux:Boot** add-on.

## Prerequisites on the OnePlus (Termux)

1. **OpenSSH server:** `pkg install openssh` then `sshd` (Termux default **`sshd`** listen port is **8022**, not 22 — see **`GUARDIAN_NODE_OS.md`** / **`PHONES_ONLY_PUBLIC_SURFACE.md`** for keepalive notes).
2. **Reachable address:** LAN IP, **Tailscale** IP, **reverse SSH** to a fleet node (this doc), or a **forwarded** port — something the **operator machine** can open TCP to (often **8022** on Termux).
3. **Repo checkout:** clone lives at **`TERMUX_REPO_DIR`** (default **`~/agr-workspace`** in helpers) with **`sovereign/`** inside it.
4. **`uvicorn`** for loopback sweeps: listening on **`127.0.0.1:5000`** (or set **`AGR_PHONES_LOCAL_BASE`** when running sweep locally).

## Key material (dedicated — never reuse the Hetzner fleet PEM)

1. On the **operator machine**, generate a **dedicated** key pair for the bridge (example):

   ```bash
   ssh-keygen -t ed25519 -f ./termux_bridge -C "termux-bridge" -N ""
   ```

2. Install **public** key on Termux:

   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   cat termux_bridge.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. Place **private** key on the operator checkout:

   ```bash
   install -m 600 termux_bridge /path/to/repo/.secrets/termux_bridge
   ```

   **`.secrets/`** is gitignored — **never** commit the private key.

4. Optional: **`AGR_TERMUX_BRIDGE_KEY_PATH`** points at the PEM if you keep it outside `.secrets/`.

## Fleet reverse tunnel — **phone-only** key (no PC)

You do **not** need a laptop to create the **`termux_fleet_tunnel`** key: **Termux includes `ssh-keygen`** with the **`openssh`** package.

### Three things you type in Termux (short list)

```text
pkg install -y openssh
cd ~/agr-workspace && git pull origin main
CONFIRM=1 bash sovereign/scripts/termux-fleet-tunnel-keygen.sh
```

The script prints **one** line starting with **`termux fleet tunnel pubkey:`**. Add that **whole line** to your private **`Secrets.md`** on **`main`** (same file the repo already uses for Cloudflare / fleet hints). Also ensure **`termux fleet jump host: ubuntu@…`** (public fleet host) is set there.

**You never SSH into the fleet server by hand.** From **Cursor** (or any checkout with **`.secrets/agr_fleet`**), an agent runs:

```bash
CONFIRM=1 bash sovereign/scripts/fleet-append-termux-tunnel-pubkey.sh
```

That appends the **public** key to the jump host’s **`~/.ssh/authorized_keys`** (idempotent). Then on the phone keep the tunnel open:

```bash
export TERMUX_FLEET_JUMP_HOST='ubuntu@YOUR_FLEET_PUBLIC_HOST'
export TERMUX_FLEET_TUNNEL_KEY="$HOME/.ssh/termux_fleet_tunnel"
bash sovereign/scripts/termux-reverse-ssh-to-fleet.sh
```

After that, **`termux-remote-ssh-via-fleet-jump.sh`** (and the **`*-via-fleet-jump`** wrappers) work from the workspace — see the **Scripts** table below.

## Secrets.md (optional lines)

In **`Secrets.md`** (private `main`), add **plain** lines (same style as other vault lines; helpers grep the whole file):

```text
termux ssh host: u0_aNNN@100.x.x.x
termux ssh repo dir: /data/data/com.termux/files/home/agr-workspace
termux fleet jump host: ubuntu@YOUR_FLEET_PUBLIC_IP_OR_DNS
termux reverse tunnel port: 18022
termux fleet tunnel pubkey: ssh-ed25519 AAAA…your-key… termux-fleet-tunnel
```

The **`termux fleet tunnel pubkey:`** line is printed by **`termux-fleet-tunnel-keygen.sh`** — it is **public** material (safe to store in **`Secrets.md`** on private **`main`**; never commit the **private** `~/.ssh/termux_fleet_tunnel` file).

Replace **`termux ssh host:`** with your real Termux **`whoami`** + a reachable host **or** add **`termux ssh user:`** instead when you only use the fleet-jump path:

```text
termux ssh user: u0_aNNN
```

Alternatively set environment only (no vault lines):

- **`TERMUX_SSH_HOST`** — `user@host`
- **`TERMUX_REPO_DIR`** — remote path to repo root
- **`TERMUX_FLEET_JUMP_HOST`** — `ubuntu@fleet-node-public`
- **`TERMUX_REVERSE_TUNNEL_PORT`** — remote loopback port on the jump host (default **18022**)
- **`TERMUX_FLEET_TUNNEL_PUBKEY`** — full **`ssh-ed25519 …`** line (optional if the line exists in **`Secrets.md`**)

## Scripts (repo root)

| Script | Purpose |
|--------|---------|
| **`CONFIRM=1 bash sovereign/scripts/termux-fleet-tunnel-keygen.sh`** | On **Termux**: create **`~/.ssh/termux_fleet_tunnel`** and print **`termux fleet tunnel pubkey:`** for **`Secrets.md`** |
| **`CONFIRM=1 bash sovereign/scripts/termux-operator-return-one-paste.sh`** | On **Termux**: **`git pull`**, fleet tunnel keygen, optional **`START_FLEET_TUNNEL_BG=1`**, prints next-step box |
| **Tower one-liner (light wake)** | **`curl -fsSL https://auroragalaxyrepublic.com/dl/termux-operator-wake | bash`** — downloads **`termux-operator-return-one-paste.sh`** from Tower, then runs it (**no** full **`termux-republic-recover`** / **`uvicorn`** reinstall) |
| **`CONFIRM=1 bash sovereign/scripts/fleet-append-termux-tunnel-pubkey.sh`** | From **Cursor** / fleet checkout: install that pubkey on the jump host **`authorized_keys`** |
| **`bash sovereign/scripts/termux-reverse-ssh-to-fleet.sh`** | On **Termux**: keep **`ssh -R`** to the fleet node (needs **`TERMUX_FLEET_*`** env) |
| **`bash sovereign/scripts/termux-remote-ssh.sh '…'`** | Direct SSH to Termux when you already have a route |
| **`CONFIRM=1 bash sovereign/scripts/termux-remote-git-pull.sh`** | **`git pull origin main`** on Termux (direct SSH) |
| **`CONFIRM=1 bash sovereign/scripts/termux-remote-origin-sweep.sh`** | Loopback sweep on Termux (direct SSH) |
| **`bash sovereign/scripts/termux-remote-ssh-via-fleet-jump.sh '…'`** | Same as **`termux-remote-ssh.sh`** via **ProxyJump** + reverse tunnel |
| **`CONFIRM=1 bash sovereign/scripts/termux-remote-git-pull-via-fleet-jump.sh`** | **`git pull`** over fleet jump |
| **`CONFIRM=1 bash sovereign/scripts/termux-remote-origin-sweep-via-fleet-jump.sh`** | Loopback sweep over fleet jump |

Helpers under **`sovereign/lib/`**: **`termux-ssh-host-from-secrets-md.sh`**, **`termux-ssh-repo-dir-from-secrets-md.sh`**, **`termux-bridge-key-path.sh`**, **`termux-fleet-jump-host-from-secrets-md.sh`**, **`termux-fleet-tunnel-pubkey-from-secrets-md.sh`**, **`termux-reverse-tunnel-port-from-secrets-md.sh`**, **`termux-ssh-user-from-secrets-md.sh`**.

## What Cursor Cloud can and cannot assume

- **If** the sandbox has **no route** to your Termux **`sshd`** **and** no **fleet SSH key** / no **reverse tunnel** running, remote Termux scripts **fail at SSH connect** — that is an environment or posture limit.
- **If** you add **Tailscale** (or similar) to both the agent environment and the phone, **`termux-remote-ssh.sh`** works without a fleet hop.
- **If** you use **fleet reverse SSH** (this doc): Cursor needs outbound SSH to the **public** fleet host (**`.secrets/agr_fleet`**) plus **`.secrets/termux_bridge`**, and the phone must run **`termux-reverse-ssh-to-fleet.sh`** in a live session.

## Related

- **`sovereign/GUARDIAN_NODE_OS.md`** — Termux checklist, **`sshd`**, mirror targets (**`FLEET_MIRROR_HANDSET_TARGETS`**).
- **`sovereign/PHONES_ONLY_PUBLIC_SURFACE.md`** — tunnel + loopback + public verify.
- **`sovereign/KORA_REPUBLIC_SOVEREIGN_OS_AND_LLM_TOT_PLAN.md`** — Phase **F** / **G** ordering.
- **`HANDOFF_FOR_NEXT_AGENT.md`** — safety + fleet SSH vs handset bridge.
