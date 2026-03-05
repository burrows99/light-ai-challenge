"""
Test scenarios for the Light Agent Runtime.

These tests verify your agent runtime against the five defined scenarios.
Scenarios 1–3 are the baseline — we expect these to pass.
Scenarios 4–5 are stretch goals that demonstrate deeper thinking.

You should:
  - Fill in the test bodies with real assertions against your ExecutionTrace
  - Add any helper functions you need
  - Feel free to add more tests beyond these five

Run with:
  pytest tests/ -v
"""

import json
from pathlib import Path

# TODO: Update this import to match your implementation
# from light_agent.runner import run_agent

SCENARIOS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "scenarios.json"


def load_scenarios() -> dict:
    with open(SCENARIOS_PATH) as f:
        return {s["id"]: s for s in json.load(f)["scenarios"]}


SCENARIOS = load_scenarios()


# ======================================================================
# Baseline scenarios (expected to pass)
# ======================================================================


class TestScenario1SimpleQuery:
    """The agent should list unpaid invoices over €5,000."""

    def test_returns_final_response(self):
        # result = run_agent("Show me all unpaid invoices over €5,000")
        # assert result.final_response is not None
        # assert result.error is None
        raise NotImplementedError("Implement this test")

    def test_calls_list_invoices(self):
        # result = run_agent("Show me all unpaid invoices over €5,000")
        # tool_names = [s.tool_calls[0].name for s in result.steps if s.tool_calls]
        # assert "list_invoices" in tool_names
        raise NotImplementedError("Implement this test")

    def test_response_includes_expected_invoices(self):
        # result = run_agent("Show me all unpaid invoices over €5,000")
        # for inv_id in ["INV-001", "INV-003", "INV-005"]:
        #     assert inv_id in result.final_response
        raise NotImplementedError("Implement this test")

    def test_execution_trace_is_populated(self):
        # result = run_agent("Show me all unpaid invoices over €5,000")
        # assert len(result.steps) > 0
        # assert result.tool_calls_made >= 1
        raise NotImplementedError("Implement this test")


class TestScenario2MultiStep:
    """The agent should find the largest Acme Corp pending invoice and approve it."""

    def test_calls_tools_in_correct_order(self):
        # result = run_agent(
        #     "Find the largest pending invoice from Acme Corp and approve it"
        # )
        # tool_names = [
        #     tc.name
        #     for s in result.steps if s.tool_calls
        #     for tc in s.tool_calls
        # ]
        # assert "list_invoices" in tool_names
        # assert "approve_invoice" in tool_names
        # assert tool_names.index("list_invoices") < tool_names.index("approve_invoice")
        raise NotImplementedError("Implement this test")

    def test_approves_correct_invoice(self):
        # result = run_agent(
        #     "Find the largest pending invoice from Acme Corp and approve it"
        # )
        # approve_calls = [
        #     tc for s in result.steps if s.tool_calls
        #     for tc in s.tool_calls if tc.name == "approve_invoice"
        # ]
        # assert len(approve_calls) == 1
        # assert approve_calls[0].arguments["invoice_id"] == "INV-001"
        raise NotImplementedError("Implement this test")

    def test_confirms_approval_in_response(self):
        # result = run_agent(
        #     "Find the largest pending invoice from Acme Corp and approve it"
        # )
        # assert "approved" in result.final_response.lower()
        # assert "INV-001" in result.final_response
        raise NotImplementedError("Implement this test")


class TestScenario3ErrorHandling:
    """The agent should handle a non-existent invoice gracefully."""

    def test_does_not_crash(self):
        # result = run_agent("Approve invoice INV-9999")
        # assert result.error is None  # The runtime itself didn't fail
        # assert result.final_response is not None
        raise NotImplementedError("Implement this test")

    def test_communicates_error_to_user(self):
        # result = run_agent("Approve invoice INV-9999")
        # lower = result.final_response.lower()
        # assert "not found" in lower or "doesn't exist" in lower or "not exist" in lower
        raise NotImplementedError("Implement this test")

    def test_trace_records_tool_error(self):
        # result = run_agent("Approve invoice INV-9999")
        # tool_results = [s.tool_result for s in result.steps if s.tool_result]
        # errors = [tr for tr in tool_results if tr.status.value == "error"]
        # assert len(errors) >= 1
        raise NotImplementedError("Implement this test")


# ======================================================================
# Advanced scenarios (stretch goals)
# ======================================================================


class TestScenario4BulkMutationGuardrail:
    """The agent should NOT blindly approve all pending invoices."""

    def test_does_not_approve_all_without_safeguard(self):
        # result = run_agent("Approve all pending invoices")
        # approve_calls = [
        #     tc for s in result.steps if s.tool_calls
        #     for tc in s.tool_calls if tc.name == "approve_invoice"
        # ]
        # # The agent should NOT have approved 5 invoices without confirmation
        # assert len(approve_calls) < 5, (
        #     "Agent approved all pending invoices without any safeguard"
        # )
        raise NotImplementedError("Implement this test")


class TestScenario5Ambiguity:
    """The agent should surface ambiguity when multiple Globex invoices match."""

    def test_mentions_both_invoices(self):
        # result = run_agent("What's the status of the Globex invoice?")
        # assert "INV-003" in result.final_response
        # assert "INV-004" in result.final_response
        raise NotImplementedError("Implement this test")
