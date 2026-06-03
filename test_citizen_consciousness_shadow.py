"""Shadow citizen_consciousness — boot cycle + orchestration log."""

from __future__ import annotations

import unittest

import citizen_consciousness as cc


class CitizenConsciousnessShadowTests(unittest.TestCase):
    def test_run_consciousness_cycle_shape(self):
        out = cc.run_consciousness_cycle()
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("engine"), "shadow_citizen_consciousness")
        self.assertIsInstance(out.get("citizens_active"), int)
        self.assertIsInstance(out.get("collaborations"), list)

    def test_get_orchestration_log_after_cycle(self):
        cc.run_consciousness_cycle()
        log = cc.get_orchestration_log(limit=5)
        self.assertIsInstance(log, list)
        self.assertGreaterEqual(len(log), 1)
        self.assertEqual(log[0].get("engine"), "shadow_citizen_consciousness")

    def test_get_or_create_profile(self):
        p = cc.get_or_create_profile("test-citizen-shadow")
        self.assertEqual(p.get("citizen_id"), "test-citizen-shadow")
        self.assertEqual(p.get("engine"), "shadow_citizen_consciousness")


if __name__ == "__main__":
    unittest.main()
