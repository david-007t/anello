#!/usr/bin/env python3
"""Unit tests for digest.py — salary parsing and experience filter."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from digest import _parse_salary_from_description, _experience_filter, _filter_reason, MAX_YEARS_EXPERIENCE


# ── Salary parsing tests ───────────────────────────────────────────────────────

def test_salary_k_range():
    """$120K-$150K range."""
    mn, mx = _parse_salary_from_description("Pay: $120K-$150K per year")
    assert mn == 120_000, f"Expected 120000, got {mn}"
    assert mx == 150_000, f"Expected 150000, got {mx}"

def test_salary_k_range_with_yr():
    """$120K/yr – $150K/yr — Bug 1 regression test."""
    mn, mx = _parse_salary_from_description("Base pay: $120K/yr – $150K/yr")
    assert mn == 120_000, f"Expected 120000, got {mn}"
    assert mx == 150_000, f"Expected 150000, got {mx}"

def test_salary_comma_range():
    """$120,000 – $150,000."""
    mn, mx = _parse_salary_from_description("Salary: $120,000 – $150,000")
    assert mn == 120_000, f"Expected 120000, got {mn}"
    assert mx == 150_000, f"Expected 150000, got {mx}"

def test_salary_comma_range_with_yr():
    """$120,000/yr – $150,000/yr — Bug 1 regression test (primary format LinkedIn uses)."""
    mn, mx = _parse_salary_from_description("$120,000/yr – $150,000/yr")
    assert mn == 120_000, f"Expected 120000, got {mn}"
    assert mx == 150_000, f"Expected 150000, got {mx}"

def test_salary_comma_range_with_year():
    """$120,000/year – $150,000/year."""
    mn, mx = _parse_salary_from_description("Compensation: $120,000/year – $150,000/year")
    assert mn == 120_000, f"Expected 120000, got {mn}"
    assert mx == 150_000, f"Expected 150000, got {mx}"

def test_salary_single_k():
    """Single $180K value."""
    mn, mx = _parse_salary_from_description("Salary up to $180K/yr")
    assert mn == 180_000, f"Expected 180000, got {mn}"
    assert mx == 180_000, f"Expected 180000, got {mx}"

def test_salary_single_comma():
    """Single $180,000 value."""
    mn, mx = _parse_salary_from_description("Offering $180,000/yr")
    assert mn == 180_000, f"Expected 180000, got {mn}"
    assert mx == 180_000, f"Expected 180000, got {mx}"

def test_salary_hourly():
    """$55/hr converts to annual."""
    mn, mx = _parse_salary_from_description("Rate: $55/hr")
    assert mn == 55 * 2080, f"Expected {55*2080}, got {mn}"

def test_salary_not_listed():
    """No salary in text returns (None, None)."""
    mn, mx = _parse_salary_from_description("Great opportunity at a growing startup!")
    assert mn is None
    assert mx is None

def test_salary_insights_section_ignored():
    """Salary insights section (market average) should not be parsed as job salary."""
    text = "Join our team!\n\nSalary Insights\nBase salary range: $200K – $300K (market average)"
    mn, mx = _parse_salary_from_description(text)
    # The section after "salary insights" is stripped, so no salary should be found
    assert mn is None, f"Expected None (insights stripped), got {mn}"

def test_salary_range_not_split_as_single():
    """$118K-$148K should not match as single $118K."""
    mn, mx = _parse_salary_from_description("Pay range: $118K-$148K")
    assert mn == 118_000
    assert mx == 148_000


# ── Experience filter tests ────────────────────────────────────────────────────

def test_exp_filter_passes_within_limit():
    """2 years experience — within MAX_YEARS_EXPERIENCE (3), should pass."""
    result = _experience_filter("We require 2 years of experience in data engineering.")
    assert result is None, f"Expected None, got {result}"

def test_exp_filter_passes_at_limit():
    """3 years experience — within MAX_YEARS_EXPERIENCE (5), should pass."""
    result = _experience_filter("Minimum 3 years of experience required.")
    assert result is None, f"Expected None, got {result}"

def test_exp_filter_passes_four_years():
    """4 years — under MAX_YEARS_EXPERIENCE (5), should pass per user preference."""
    result = _experience_filter("We require 4 years of experience in product management.")
    assert result is None, f"Expected None (4 yrs should pass with threshold=5), got {result}"

def test_exp_filter_passes_five_years():
    """5 years — at new MAX_YEARS_EXPERIENCE (5), should pass per user preference."""
    result = _experience_filter("We require 5 years of experience in data engineering.")
    assert result is None, f"Expected None (5 yrs should pass with threshold=5), got {result}"

def test_exp_filter_rejects_over_limit():
    """6 years experience — over limit, should reject."""
    result = _experience_filter("6+ years of data engineering experience required.")
    assert result is not None, "Expected rejection for 6+ years"
    assert "6" in result

def test_exp_filter_rejects_range_max():
    """3-6 years — max is 6, over limit (MAX=5), should reject."""
    result = _experience_filter("Looking for 3-6 years of experience in Python.")
    assert result is not None, "Expected rejection for 3-6 years (max=6)"
    assert "6" in result

def test_exp_filter_rejects_at_least():
    """At least 7 years experience."""
    result = _experience_filter("At least 7 years of relevant experience.")
    assert result is not None
    assert "7" in result

def test_exp_filter_rejects_or_more():
    """8 or more years."""
    result = _experience_filter("8 or more years of product management experience.")
    assert result is not None
    assert "8" in result

def test_exp_filter_no_mention():
    """No experience requirement in text."""
    result = _experience_filter("Looking for a passionate engineer to join our team.")
    assert result is None

def test_exp_filter_takes_max_of_multiple():
    """Multiple mentions — takes the highest."""
    result = _experience_filter(
        "2 years of Python experience required. 7 years of data experience preferred."
    )
    assert result is not None, "Expected rejection (max 7)"
    assert "7" in result


# ── Title filter tests ────────────────────────────────────────────────────────

def test_title_filter_senior_pm_blocked():
    """Senior Product Manager — senior+manager combo, must be filtered."""
    assert _filter_reason("Senior Product Manager", None) is not None

def test_title_filter_sr_pm_blocked():
    """Sr. Product Manager — filtered."""
    assert _filter_reason("Sr. Product Manager", None) is not None

def test_title_filter_staff_pm_blocked():
    """Staff Product Manager — filtered."""
    assert _filter_reason("Staff Product Manager", None) is not None

def test_title_filter_principal_pm_blocked():
    """Principal Product Manager — filtered."""
    assert _filter_reason("Principal Product Manager", None) is not None

def test_title_filter_senior_eng_manager_blocked():
    """Senior Engineering Manager — filtered."""
    assert _filter_reason("Senior Engineering Manager", None) is not None

def test_title_filter_tpm_passes():
    """Technical Product Manager — must pass."""
    assert _filter_reason("Technical Product Manager", None) is None

def test_title_filter_pm_passes():
    """Product Manager — must pass."""
    assert _filter_reason("Product Manager", None) is None

def test_title_filter_senior_de_passes():
    """Senior Data Engineer — senior without manager, must pass."""
    assert _filter_reason("Senior Data Engineer", None) is None

def test_title_filter_de_manager_passes():
    """Data Engineering Manager — manager without senior/staff/principal, must pass."""
    assert _filter_reason("Data Engineering Manager", None) is None

def test_title_filter_remote_senior_pm_blocked():
    """REMOTE: Senior Product Manager — blocked regardless of prefix."""
    assert _filter_reason("REMOTE: Senior Product Manager", None) is not None


# ── Positive title filter tests ───────────────────────────────────────────────

def test_title_filter_mortgage_broker_blocked():
    """Mortgage Broker — not in target roles, must be filtered."""
    assert _filter_reason("Mortgage Broker", None) is not None

def test_title_filter_environmental_manager_blocked():
    """Environmental Manager — not in target roles, must be filtered."""
    assert _filter_reason("Environmental Manager", None) is not None

def test_title_filter_technical_product_manager_passes():
    """Technical Product Manager — contains 'product manager', must pass."""
    assert _filter_reason("Technical Product Manager", None) is None

def test_title_filter_data_engineer_passes():
    """Data Engineer — in target roles, must pass."""
    assert _filter_reason("Data Engineer", None) is None

def test_title_filter_senior_data_engineer_passes():
    """Senior Data Engineer — contains 'data engineer', must pass."""
    assert _filter_reason("Senior Data Engineer", None) is None

def test_title_filter_software_engineer_passes():
    """Software Engineer — in target roles, must pass."""
    assert _filter_reason("Software Engineer", None) is None


# ── Runner ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  \033[92mPASS\033[0m  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  \033[91mFAIL\033[0m  {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*44}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*44)
    sys.exit(1 if failed else 0)
