"""Tests for market_selector.py — Irish relevance scoring and pillar assignment."""

import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from market_selector import score_market, assign_pillar, select_markets_for_pillar


class TestScoreMarket(unittest.TestCase):
    def test_high_relevance_irish(self):
        market = {
            "title": "Will Sinn Féin lead the next Irish coalition?",
            "description": "Market on the next Taoiseach and Dáil formation",
        }
        score = score_market(market)
        # Should match: sinn féin (9), irish (10), coalition (6), taoiseach (10), dáil (10)
        self.assertGreaterEqual(score, 30)

    def test_moderate_relevance_eu(self):
        market = {
            "title": "Will the ECB cut interest rates in Q2 2026?",
            "description": "European Central Bank monetary policy decision",
        }
        score = score_market(market)
        # Should match: ecb (6), interest rate (5), european central bank (6)
        self.assertGreaterEqual(score, 10)

    def test_low_relevance_us(self):
        market = {
            "title": "Will a specific US state bill pass?",
            "description": "State-level legislation in Wyoming",
        }
        score = score_market(market)
        self.assertLess(score, 3)

    def test_sport_relevance(self):
        market = {
            "title": "Six Nations 2026 winner",
            "description": "Rugby championship including Ireland",
        }
        score = score_market(market)
        # six nations (9), ireland (10), rugby (7)
        self.assertGreaterEqual(score, 20)

    def test_trump_relevance(self):
        market = {
            "title": "Will Trump impose tariffs on the EU?",
            "description": "Trade war and tariff policy",
        }
        score = score_market(market)
        # trump (5), tariff (4), eu (5), trade war (3)
        self.assertGreaterEqual(score, 10)

    def test_empty_market(self):
        market = {"title": "", "description": ""}
        score = score_market(market)
        self.assertEqual(score, 0)


class TestAssignPillar(unittest.TestCase):
    def test_election_market_pillar1(self):
        market = {
            "title": "Who will win the next US election?",
            "description": "Presidential election market",
        }
        self.assertEqual(assign_pillar(market), 1)

    def test_sport_market_pillar1(self):
        market = {
            "title": "Six Nations 2026 champion",
            "description": "Rugby championship winner market",
        }
        self.assertEqual(assign_pillar(market), 1)

    def test_general_market_pillar2(self):
        market = {
            "title": "Will the ECB raise rates?",
            "description": "Monetary policy market",
        }
        self.assertEqual(assign_pillar(market), 2)

    def test_crypto_market_pillar2(self):
        market = {
            "title": "Will Bitcoin hit 200k by end of 2026?",
            "description": "Cryptocurrency price prediction",
        }
        self.assertEqual(assign_pillar(market), 2)


class TestSelectMarkets(unittest.TestCase):
    @patch("market_selector.was_market_used", return_value=False)
    def test_selects_top_relevant(self, mock_used):
        markets = [
            {"id": "1", "title": "Will Ireland win the Six Nations?",
             "description": "Rugby", "prices": [0.3], "volume": 500000,
             "slug": "ireland-six-nations", "outcomes": ["Yes", "No"]},
            {"id": "2", "title": "Some random US state market",
             "description": "Wyoming legislation", "prices": [0.5], "volume": 1000,
             "slug": "wyoming", "outcomes": ["Yes", "No"]},
            {"id": "3", "title": "Will Trump impose EU tariffs?",
             "description": "Trade war", "prices": [0.6], "volume": 2000000,
             "slug": "trump-tariffs", "outcomes": ["Yes", "No"]},
        ]
        selected = select_markets_for_pillar(markets, pillar=1, count=2)
        # Ireland Six Nations should rank highest
        self.assertGreaterEqual(len(selected), 1)
        self.assertEqual(selected[0]["id"], "1")

    @patch("market_selector.was_market_used", return_value=True)
    def test_dedup_filters_used(self, mock_used):
        markets = [
            {"id": "1", "title": "Will Ireland win?",
             "description": "Important market", "prices": [0.5], "volume": 100000,
             "slug": "test", "outcomes": ["Yes"]},
        ]
        selected = select_markets_for_pillar(markets, pillar=1, count=1)
        self.assertEqual(len(selected), 0)

    @patch("market_selector.was_market_used", return_value=True)
    def test_allow_reuse(self, mock_used):
        markets = [
            {"id": "1", "title": "Ireland election winner",
             "description": "Taoiseach market", "prices": [0.5], "volume": 100000,
             "slug": "test", "outcomes": ["Yes"]},
        ]
        selected = select_markets_for_pillar(markets, pillar=1, count=1, allow_reuse=True)
        self.assertEqual(len(selected), 1)


if __name__ == "__main__":
    unittest.main()
