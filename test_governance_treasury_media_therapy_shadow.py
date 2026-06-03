"""Unit tests for aurora_governance, aurora_treasury, aurora_media, agr_therapy shadows."""

from __future__ import annotations

import unittest

import aurora_governance as gov
import aurora_media as media
import aurora_treasury as tre
import agr_therapy as th


class AuroraGovernanceShadowTests(unittest.TestCase):
    def test_constitution_and_stats(self):
        c = gov.get_constitution()
        self.assertIsInstance(c, str)
        self.assertIn("Aurora Galaxy Republic", c)
        stats = gov.get_governance_stats()
        self.assertTrue(stats.get("ok"))
        self.assertEqual(stats.get("engine"), "shadow_aurora_governance")

    def test_law_propose_vote(self):
        r = gov.propose_law("c1", "Tester", "Test Law", "Body text", "civil_rights", ["x"], 7)
        self.assertTrue(r.get("ok"))
        law_id = r["law_id"]
        v = gov.cast_vote(law_id, "voter1", "yes", "ok")
        self.assertTrue(v.get("ok"))
        dup = gov.cast_vote(law_id, "voter1", "no")
        self.assertFalse(dup.get("ok"))

    def test_referendum_and_petition(self):
        ref = gov.create_referendum("c1", "Q?", "desc", ["A", "B"], 5)
        self.assertTrue(ref.get("ok"))
        vr = gov.vote_referendum(ref["ref_id"], "u1", "opt_0")
        self.assertTrue(vr.get("ok"))
        pet = gov.sign_petition("Save the reefs", "u9", "yes")
        self.assertTrue(pet.get("ok"))
        self.assertGreaterEqual(pet.get("signatures", 0), 1)


class AuroraTreasuryShadowTests(unittest.TestCase):
    def test_wallet_transfer_stake(self):
        tre.get_or_create_wallet("alice")
        tre.get_or_create_wallet("bob")
        tre._WALLETS["alice"]["balance"] = 100.0  # shadow liquidity for test
        tx = tre.transfer("alice", "bob", 10.0, "AGR", "test")
        self.assertTrue(tx.get("ok"))
        self.assertEqual(tre.get_balance("bob")["balance"], 10.0)
        hist = tre.get_transaction_history("alice", 5)
        self.assertTrue(any(h.get("type") == "transfer" for h in hist))
        st = tre.stake_agr("bob", 5.0, 30)
        self.assertTrue(st.get("ok"))
        ov = tre.get_treasury_overview()
        self.assertTrue(ov.get("ok"))
        rates = tre.get_exchange_rates()
        self.assertIn("pairs", rates)


class AuroraMediaShadowTests(unittest.TestCase):
    def test_channel_video_news(self):
        ch = media.create_channel("o1", "Republic TV", "Official", "news", ["agr"])
        self.assertTrue(ch.get("ok"))
        cid = ch["channel"]["channel_id"]
        media.subscribe_channel("u1", cid)
        up = media.upload_video("o1", cid, "Hello", "d", "news", "https://example.com/v.mp4")
        self.assertTrue(up.get("ok"))
        vid = up["video"]["video_id"]
        w = media.watch_video("u1", vid, 0.5)
        self.assertTrue(w.get("ok"))
        feed = media.get_feed(limit=5)
        self.assertTrue(feed.get("ok"))
        self.assertGreaterEqual(len(feed.get("items", [])), 1)
        news = media.publish_news("ceo1", "CEO", "Headline", "Full body")
        self.assertTrue(news.get("ok"))
        lst = media.get_news(limit=3)
        self.assertGreaterEqual(len(lst), 1)
        stats = media.get_media_stats()
        self.assertTrue(stats.get("ok"))


class AgrTherapyShadowTests(unittest.TestCase):
    def test_page_and_respond(self):
        self.assertIn("Listening space", th.THERAPY_PAGE_HTML)
        r = th.therapy_respond("I feel tired and overwhelmed", [])
        self.assertTrue(r.get("ok"))
        self.assertIn("response", r)
        self.assertFalse(r.get("crisis"))
        c = th.therapy_respond("I want to kill myself", [])
        self.assertTrue(c.get("crisis"))


if __name__ == "__main__":
    unittest.main()
