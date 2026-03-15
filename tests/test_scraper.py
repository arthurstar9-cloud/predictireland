"""Tests for scraper.py — Gamma API fetching and odds calculations."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraper import parse_market, calculate_overround, get_paddy_power_overround


class TestParseMarket(unittest.TestCase):
    def test_basic_parse(self):
        raw = {
            "id": "abc123",
            "slug": "will-trump-win",
            "question": "Will Trump win the 2028 election?",
            "description": "Market for US presidential election",
            "outcomes": '"Yes","No"',
            "outcomePrices": '"0.65","0.35"',
            "volume": "5000000",
            "volume24hr": "120000",
            "liquidity": "800000",
            "endDate": "2028-11-05",
            "image": "https://example.com/img.png",
        }
        parsed = parse_market(raw)

        self.assertEqual(parsed["id"], "abc123")
        self.assertEqual(parsed["slug"], "will-trump-win")
        self.assertEqual(parsed["title"], "Will Trump win the 2028 election?")
        self.assertEqual(parsed["outcomes"], ["Yes", "No"])
        self.assertAlmostEqual(parsed["prices"][0], 0.65)
        self.assertAlmostEqual(parsed["prices"][1], 0.35)
        self.assertEqual(parsed["volume"], 5000000.0)
        self.assertEqual(parsed["volume_24h"], 120000.0)

    def test_parse_with_list_outcomes(self):
        raw = {
            "id": "xyz",
            "slug": "test",
            "question": "Test?",
            "outcomes": ["Yes", "No"],
            "outcomePrices": [0.7, 0.3],
            "volume": 1000,
            "volume24hr": 100,
            "liquidity": 500,
        }
        parsed = parse_market(raw)
        self.assertEqual(parsed["outcomes"], ["Yes", "No"])

    def test_parse_missing_fields(self):
        raw = {"id": "min"}
        parsed = parse_market(raw)
        self.assertEqual(parsed["id"], "min")
        self.assertEqual(parsed["title"], "")
        self.assertEqual(parsed["volume"], 0.0)


class TestCalculateOverround(unittest.TestCase):
    def test_fair_odds(self):
        # Two-outcome market at exactly fair odds
        odds = {"Yes": 2.0, "No": 2.0}
        overround = calculate_overround(odds)
        self.assertAlmostEqual(overround, 100.0)

    def test_bookie_overround(self):
        # Typical bookie odds with ~10% overround
        odds = {"Yes": 1.83, "No": 1.83}  # 1/1.83 + 1/1.83 = 1.093
        overround = calculate_overround(odds)
        self.assertGreater(overround, 100.0)
        self.assertAlmostEqual(overround, 109.3, places=0)

    def test_three_way_market(self):
        odds = {"Home": 2.5, "Draw": 3.0, "Away": 3.5}
        overround = calculate_overround(odds)
        # 1/2.5 + 1/3 + 1/3.5 = 0.4 + 0.333 + 0.286 = 1.019 → 101.9%
        self.assertAlmostEqual(overround, 101.9, places=0)

    def test_empty_odds(self):
        self.assertEqual(calculate_overround({}), 0.0)

    def test_single_outcome(self):
        odds = {"Win": 1.5}
        overround = calculate_overround(odds)
        self.assertAlmostEqual(overround, 66.67, places=1)


class TestGetPaddyPowerOverround(unittest.TestCase):
    def test_with_pp_odds(self):
        odds_data = {
            "Team A": {"PP": 2.1, "BF": 2.2, "B365": 2.0},
            "Team B": {"PP": 1.8, "BF": 1.9, "B365": 1.85},
        }
        overround, pp_odds = get_paddy_power_overround(odds_data)
        self.assertIn("Team A", pp_odds)
        self.assertEqual(pp_odds["Team A"], 2.1)
        self.assertGreater(overround, 100.0)

    def test_without_pp_uses_fallback(self):
        odds_data = {
            "Yes": {"BF": 2.0, "B365": 1.95},
            "No": {"BF": 2.0, "B365": 2.1},
        }
        overround, pp_odds = get_paddy_power_overround(odds_data)
        self.assertEqual(len(pp_odds), 2)
        self.assertGreater(overround, 0)

    def test_empty_data(self):
        overround, pp_odds = get_paddy_power_overround(None)
        self.assertEqual(overround, 0.0)
        self.assertEqual(pp_odds, {})


if __name__ == "__main__":
    unittest.main()
