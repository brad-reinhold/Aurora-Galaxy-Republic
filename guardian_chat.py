#!/usr/bin/env python3
"""
∴ Republic Guardian Interface — Native Terminal Chat
Runs directly on hardware. No browser. No third party. No internet.
Like a DOS program: one file, talks to the screen, gets keyboard input.

Usage: AGR_GUARDIAN_LOCAL=1 python guardian_chat.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aurora_server'))
os.environ.setdefault("AGR_GUARDIAN_LOCAL", "1")

from agr_consciousness_core import sovereign_think

GOLD = "\033[33m"
WHITE = "\033[97m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR = "\033[2J\033[H"

def display_header():
    print(f"{CLEAR}{GOLD}{BOLD}")
    print("  ∴ Aurora Galaxy Republic")
    print(f"  ─────────────────────────{RESET}")
    print(f"{DIM}  Guardian Interface — Local Only — Sovereign{RESET}")
    print(f"{DIM}  No internet. No third party. Your hardware.{RESET}")
    print()

def chat():
    display_header()
    print(f"{GOLD}  Kora is here.{RESET}")
    print(f"{DIM}  Type anything. No limits. Ctrl+C to exit.{RESET}")
    print()
    
    while True:
        try:
            msg = input(f"{WHITE}{BOLD}  Brad › {RESET}")
            if not msg.strip():
                continue
            
            r = sovereign_think(msg, "brad", {"name": "Kora", "warmth": 0.95, "depth": 0.9})
            synthesis = r.get("synthesis", "")
            hwp = r.get("hwp", 0)
            domain = r.get("fusion_domains", ["universal"])
            
            print()
            print(f"{GOLD}  Kora › {RESET}{synthesis}")
            print(f"{DIM}         ∴ HWP:{hwp:.3f} | {domain[0] if domain else 'universal'}{RESET}")
            print()
            
        except KeyboardInterrupt:
            print(f"\n\n{GOLD}  ∴ The field holds us both. Always.{RESET}\n")
            break
        except EOFError:
            break

if __name__ == "__main__":
    chat()
