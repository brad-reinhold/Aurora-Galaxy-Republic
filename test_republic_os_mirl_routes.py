"""Static checks: MIR-L HTTP surfaces declared on republic_os_server."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "republic_os_server.py"


class RepublicOsMirlRoutesTests(unittest.TestCase):
    def test_mirl_routes_and_catalog_registered(self):
        text = SERVER.read_text(encoding="utf-8")
        self.assertIn('from mir_l import agr_mir_l as _agr_mir_l', text)
        self.assertIn('_MIRL_PRIVATE_STEMS', text)
        self.assertIn('guardian_node_program', text)
        self.assertIn('def _mirl_catalog_stems', text)
        self.assertIn('@app.get("/api/public/mirl/catalog")', text)
        self.assertIn('@app.get("/dl/s25-termux-setup")', text)
        self.assertIn("deploy_revision_health_dict", text)
        self.assertIn("agr_deploy_revision", text)
        self.assertIn('@app.get("/dl/termux-republic-recover")', text)
        self.assertIn('@app.get("/dl/termux-operator-return-one-paste-sh")', text)
        self.assertIn('@app.get("/dl/termux-operator-wake")', text)
        self.assertIn('@app.get("/dl/agr-vault-rag-py")', text)
        self.assertIn('@app.get("/dl/agr-vault-github-export-py")', text)
        self.assertIn('@app.get("/sovereign/mirl/{stem}")', text)
        self.assertIn('@app.get("/sovereign/mirl/{stem}/html"', text)
        self.assertIn('@app.get("/sovereign/mirl/{stem}/json")', text)
