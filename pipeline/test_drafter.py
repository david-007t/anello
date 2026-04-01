"""
test_drafter.py — Minimal test for draft_message().

NOTE: This test mocks the Anthropic API call so no real ANTHROPIC_API_KEY
is needed. To run against the real API instead, remove the mock patch and
set ANTHROPIC_API_KEY in your environment before running:

    ANTHROPIC_API_KEY=sk-... python pipeline/test_drafter.py
"""

import json
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Fake job and resume fixtures
# ---------------------------------------------------------------------------

FAKE_JOB = {
    "title": "Senior Product Manager",
    "company": "Acme Corp",
    "description": (
        "We need a PM with 3+ years experience in B2B SaaS. "
        "You will own the product roadmap, work closely with engineering, "
        "and drive customer discovery interviews. Experience with Jira, "
        "Figma, and Mixpanel preferred."
    ),
}

FAKE_RESUME = """\
Jane Doe | jane@example.com | linkedin.com/in/janedoe

EXPERIENCE
Product Manager, Widgets Inc (2021–present)
  - Led B2B SaaS product from 0 to 10k customers
  - Partnered with 8-person engineering team on quarterly roadmap

Associate PM, Beta Corp (2019–2021)
  - Ran weekly customer interviews; reduced churn 18%

EDUCATION
B.S. Computer Science, State University, 2019
"""

# ---------------------------------------------------------------------------
# Canned Claude response (what the mock will return)
# ---------------------------------------------------------------------------

MOCK_MESSAGE_TEXT = (
    "Acme's B2B SaaS roadmap work caught my eye. "
    "I've shipped 0-to-10k products and led customer discovery at Widgets. "
    "Open to a quick call? — Jane"
)

MOCK_RESPONSE_JSON = json.dumps(
    {
        "message": MOCK_MESSAGE_TEXT,
        "subject": "",
        "message_type": "linkedin_connection",
    }
)


def _make_mock_client_response(text: str):
    """Build a fake anthropic Messages response object."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDraftMessage(unittest.TestCase):

    @patch("pipeline.drafter.client")
    def test_linkedin_connection_char_limit(self, mock_client):
        """draft_message returns char_count <= 300 for linkedin_connection."""
        mock_client.messages.create.return_value = _make_mock_client_response(
            MOCK_RESPONSE_JSON
        )

        from pipeline.drafter import draft_message

        result = draft_message(FAKE_RESUME, FAKE_JOB, "linkedin_connection")

        print("\n--- draft_message result ---")
        print(f"message    : {result['message']}")
        print(f"subject    : {result['subject']!r}")
        print(f"char_count : {result['char_count']}")
        print(f"message_type: {result['message_type']}")
        print(f"warnings   : {result['warnings']}")
        print("----------------------------")

        assert result["char_count"] <= 300, (
            f"Expected char_count <= 300 but got {result['char_count']}"
        )
        assert result["message_type"] == "linkedin_connection"
        assert isinstance(result["warnings"], list)
        assert result["message"] == MOCK_MESSAGE_TEXT

        print(f"PASS: char_count={result['char_count']} <= 300")

    @patch("pipeline.drafter.client")
    def test_over_limit_triggers_warning(self, mock_client):
        """A message that exceeds 300 chars should populate warnings."""
        long_message = "A" * 301
        over_limit_json = json.dumps(
            {"message": long_message, "subject": "", "message_type": "linkedin_connection"}
        )
        mock_client.messages.create.return_value = _make_mock_client_response(
            over_limit_json
        )

        from pipeline.drafter import draft_message

        result = draft_message(FAKE_RESUME, FAKE_JOB, "linkedin_connection")

        assert result["char_count"] == 301
        assert len(result["warnings"]) == 1
        assert "300-char limit" in result["warnings"][0]

        print(f"PASS: over-limit warning present: {result['warnings'][0]}")

    @patch("pipeline.drafter.client")
    def test_returns_required_keys(self, mock_client):
        """Result dict always contains the five expected keys."""
        mock_client.messages.create.return_value = _make_mock_client_response(
            MOCK_RESPONSE_JSON
        )

        from pipeline.drafter import draft_message

        result = draft_message(FAKE_RESUME, FAKE_JOB, "linkedin_connection")

        for key in ("message", "subject", "char_count", "message_type", "warnings"):
            assert key in result, f"Missing key: {key}"

        print("PASS: all required keys present")


# ---------------------------------------------------------------------------
# Main — also print a quick standalone smoke-run summary
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running test_drafter.py …\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDraftMessage)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
