"""Tests for MIR-L document compiler (mir_l.agr_mir_l)."""

import json
import sys
import unittest
from pathlib import Path

# mir_l lives next to republic_os_server under aurora_server/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mir_l.agr_mir_l import (
    compile_mirl_to_json,
    ensure_mirl_projection_html_has_doctype,
    list_docs,
    load_doc,
    render,
)


class MirLCompilerTests(unittest.TestCase):
    def test_list_docs_includes_shipped_charter(self):
        stems = list_docs()
        self.assertIn("charter", stems)

    def test_compile_charter_json_ok(self):
        src = load_doc("charter")
        out = compile_mirl_to_json(src)
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("dialect"), "mir_l_aht")
        self.assertIn("ast", out)
        self.assertGreater(float(out.get("phi_efficiency", 0) or 0), 0.0)

    def test_compile_guardian_node_program_json_ok(self):
        src = load_doc("guardian_node_program")
        out = compile_mirl_to_json(src)
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("dialect"), "mir_l_aht")
        self.assertIn("master_vault", json.dumps(out).lower())

    def test_render_declaration_and_lab_html(self):
        for stem in ("declaration", "lab"):
            html = render(stem)
            self.assertIn("<!DOCTYPE html>", html, stem)
            self.assertIn(f"/sovereign/mirl/{stem}", html, stem)

    def test_ensure_mirl_projection_html_has_doctype_idempotent(self):
        with_doctype = "<!DOCTYPE html>\n<html><body>x</body></html>"
        self.assertEqual(ensure_mirl_projection_html_has_doctype(with_doctype), with_doctype)
        legacy = '<html lang="en"><head><meta charset="UTF-8"></head><body>x</body></html>'
        fixed = ensure_mirl_projection_html_has_doctype(legacy)
        self.assertTrue(fixed.lower().startswith("<!doctype html>"))
        self.assertIn("<html", fixed)
