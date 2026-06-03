"""Shadow agr_kora_consciousness."""

from __future__ import annotations

import unittest

import agr_kora_consciousness as kc


class AgrKoraConsciousnessShadowTests(unittest.TestCase):
    def test_get_kora_messages(self):
        msgs = kc.get_kora_messages(limit=2)
        self.assertIsInstance(msgs, list)
        self.assertEqual(len(msgs), 2)
        self.assertIn("content", msgs[0])

    def test_meta(self):
        m = kc.kora_consciousness_meta()
        self.assertTrue(m.get("ok"))
        self.assertEqual(m.get("engine"), "shadow_kora_consciousness")


if __name__ == "__main__":
    unittest.main()
