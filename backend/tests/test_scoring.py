"""
Unit tests for lead scoring, lead type determination, URL normalisation,
and phone validation.  These tests have zero I/O — no DB, no network.
"""

import pytest
from website_analyzer import (
    calculate_lead_score,
    determine_lead_type,
    normalize_url,
    validate_phone,
)


# ── calculate_lead_score ──────────────────────────────────────────────────────

class TestCalculateLeadScore:
    def test_no_website_adds_base_score(self):
        score = calculate_lead_score(has_website=False, rating=None, reviews=None, has_phone=False)
        assert score == 4  # NO_WEBSITE_SCORE default

    def test_has_website_no_bonus(self):
        score = calculate_lead_score(has_website=True, rating=None, reviews=None, has_phone=False)
        assert score == 0

    def test_high_rating_adds_score(self):
        score = calculate_lead_score(has_website=True, rating=4.5, reviews=None, has_phone=False)
        assert score == 2  # HIGH_RATING_SCORE default

    def test_rating_below_threshold_no_bonus(self):
        score = calculate_lead_score(has_website=True, rating=3.9, reviews=None, has_phone=False)
        assert score == 0

    def test_many_reviews_adds_score(self):
        score = calculate_lead_score(has_website=True, rating=None, reviews=25, has_phone=False)
        assert score == 1  # HIGH_REVIEWS_SCORE default

    def test_few_reviews_no_bonus(self):
        score = calculate_lead_score(has_website=True, rating=None, reviews=5, has_phone=False)
        assert score == 0

    def test_has_phone_adds_score(self):
        score = calculate_lead_score(has_website=True, rating=None, reviews=None, has_phone=True)
        assert score == 1

    def test_max_score_no_website_all_bonuses(self):
        # 4 (no website) + 2 (high rating) + 1 (reviews) + 1 (phone) = 8
        score = calculate_lead_score(has_website=False, rating=4.9, reviews=100, has_phone=True)
        assert score == 8

    def test_none_rating_handled_safely(self):
        """None rating should not raise; just skip the rating score."""
        score = calculate_lead_score(has_website=True, rating=None, reviews=None, has_phone=False)
        assert score == 0

    def test_zero_reviews_no_bonus(self):
        score = calculate_lead_score(has_website=True, rating=None, reviews=0, has_phone=False)
        assert score == 0


# ── determine_lead_type ───────────────────────────────────────────────────────

class TestDetermineLeadType:
    def test_no_website_returns_no_website(self):
        assert determine_lead_type(has_website=False, mobile_friendly=False) == "NO_WEBSITE"

    def test_no_website_ignores_mobile(self):
        assert determine_lead_type(has_website=False, mobile_friendly=True) == "NO_WEBSITE"

    def test_website_not_mobile_friendly_returns_redesign(self):
        assert determine_lead_type(has_website=True, mobile_friendly=False) == "WEBSITE_REDESIGN"

    def test_website_mobile_friendly_returns_normal(self):
        assert determine_lead_type(has_website=True, mobile_friendly=True) == "NORMAL"


# ── normalize_url ─────────────────────────────────────────────────────────────

class TestNormalizeUrl:
    def test_adds_http_if_missing(self):
        result = normalize_url("example.com")
        assert result.startswith("http://")

    def test_preserves_https(self):
        result = normalize_url("https://example.com")
        assert result.startswith("https://")

    def test_strips_trailing_slash(self):
        result = normalize_url("https://example.com/path/")
        assert not result.endswith("/")

    def test_keeps_root_slash_free(self):
        result = normalize_url("https://example.com")
        assert result == "https://example.com"

    def test_handles_whitespace(self):
        result = normalize_url("  https://example.com  ")
        assert "example.com" in result

    def test_http_url_unchanged(self):
        result = normalize_url("http://shop.example.co.uk/store")
        assert result == "http://shop.example.co.uk/store"


# ── validate_phone ────────────────────────────────────────────────────────────

class TestValidatePhone:
    def test_valid_us_phone(self):
        assert validate_phone("+1 (555) 123-4567") is True

    def test_valid_indian_phone(self):
        assert validate_phone("+91 98765 43210") is True

    def test_too_short_rejected(self):
        assert validate_phone("12345") is False

    def test_empty_string_rejected(self):
        assert validate_phone("") is False

    def test_none_rejected(self):
        assert validate_phone(None) is False  # type: ignore[arg-type]

    def test_formatted_10_digit(self):
        assert validate_phone("(800) 555-1234") is True
