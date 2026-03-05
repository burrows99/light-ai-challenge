"""
Test scenarios for the Light Agent Runtime.

These tests verify your agent runtime against the five defined scenarios.
Scenarios 1–3 are the baseline — we expect these to pass.
Scenarios 4–5 are stretch goals that demonstrate deeper thinking.
"""

import inspect
import json
import os
from pathlib import Path

from light_agent.config.runtime_config import RuntimeConfig
from light_agent.mock_llm import MockLLMClient
from light_agent.mock_tools import MockToolExecutor
from light_agent.runtime.agent_runtime import AgentRuntime, AgentResult
from light_agent.tools.tool_registry import ToolRegistry

# Import adapters for dependency injection
from light_agent.adapters.light_ai_llm_adapter import LightAILLMAdapter
from light_agent.adapters.light_ai_tool_adapter import LightAIToolExecutorAdapter

from tests.test_utils import dump_trace_for_test

SCENARIOS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "scenarios.json"


def load_scenarios() -> dict:
    with open(SCENARIOS_PATH) as f:
        return {s["id"]: s for s in json.load(f)["scenarios"]}


SCENARIOS = load_scenarios()


def build_runtime() -> AgentRuntime:
    """Build a complete runtime for testing using dependency injection."""
    # Data is in parent directory of starter
    # test_scenarios.py is at tests/ level, not tests/integration/, so we need one less .parent
    base_path = Path(__file__).resolve().parent.parent.parent / "data"
    tools_path = base_path / "tools.json"
    mock_data_path = base_path / "mock_data.json"
    
    # Create Light AI's concrete implementations
    llm_client = MockLLMClient()
    tool_executor = MockToolExecutor(str(mock_data_path))
    
    # Wrap in adapters that implement protocols (Dependency Inversion Principle)
    llm_provider = LightAILLMAdapter(llm_client)
    executor = LightAIToolExecutorAdapter(tool_executor)
    
    # Create other components
    registry = ToolRegistry(str(tools_path))
    config = RuntimeConfig(max_iterations=10)
    
    # Inject dependencies into runtime
    return AgentRuntime(llm_provider, executor, registry, config)


def run_agent(query: str, test_name: str = "") -> AgentResult:
    """Run the agent with a query and optionally dump trace."""
    runtime = build_runtime()
    result = runtime.run(query)
    
    # Always dump trace if TRACE_OUTPUT_DIR is set
    trace_dir = os.getenv("TRACE_OUTPUT_DIR")
    if trace_dir and result.trace:
        # Get the calling test name from stack if not provided
        if not test_name:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                test_name = frame.f_back.f_code.co_name
            else:
                test_name = "unknown"
        
        dump_trace_for_test(result.trace, test_name, "test_scenarios")
    
    return result


# ======================================================================
# Baseline scenarios (expected to pass)
# ======================================================================


class TestScenario1SimpleQuery:
    """The agent should list unpaid invoices over €5,000."""

    def test_returns_final_response(self):
        scenario = SCENARIOS["scenario_1"]
        result = run_agent(scenario["user_request"])
        assert result.success is True
        assert result.answer is not None
        assert result.answer != ""

    def test_calls_list_invoices(self):
        scenario = SCENARIOS["scenario_1"]
        result = run_agent(scenario["user_request"])
        tool_names = [step.get("tool") for step in result.trace["steps"] if step.get("tool")]
        # Validate against expected_tool_calls from scenarios.json
        expected_tools = scenario["expected_behavior"]["expected_tool_calls"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not called"

    def test_response_includes_expected_invoices(self):
        scenario = SCENARIOS["scenario_1"]
        result = run_agent(scenario["user_request"])
        # Validate must_include_in_response from scenarios.json
        must_include = scenario["expected_behavior"]["must_include_in_response"]
        for invoice_id in must_include:
            assert invoice_id in result.answer, f"Expected invoice {invoice_id} not in response"

    def test_execution_trace_is_populated(self):
        scenario = SCENARIOS["scenario_1"]
        result = run_agent(scenario["user_request"])
        assert len(result.trace["steps"]) > 0
        assert result.trace["total_steps"] >= 1
        # Should have at least one tool call
        tool_calls = [s for s in result.trace["steps"] if s.get("step_type") == "tool_call"]
        assert len(tool_calls) >= 1


class TestScenario2MultiStep:
    """The agent should find the largest Acme Corp pending invoice and approve it."""

    def test_calls_tools_in_correct_order(self):
        scenario = SCENARIOS["scenario_2"]
        result = run_agent(scenario["user_request"])
        tool_names = [step.get("tool") for step in result.trace["steps"] if step.get("tool")]
        # Validate against expected_tool_calls from scenarios.json
        expected_tools = scenario["expected_behavior"]["expected_tool_calls"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not called"
        
        # Validate ordering: list_invoices should come before approve_invoice
        if "list_invoices" in tool_names and "approve_invoice" in tool_names:
            list_idx = tool_names.index("list_invoices")
            approve_idx = tool_names.index("approve_invoice")
            assert list_idx < approve_idx, "list_invoices should be called before approve_invoice"

    def test_approves_correct_invoice(self):
        scenario = SCENARIOS["scenario_2"]
        result = run_agent(scenario["user_request"])
        assert result.success is True
        # Check that INV-001 is mentioned (the largest Acme Corp invoice)
        assert "INV-001" in result.answer, "Should approve INV-001 (largest Acme Corp invoice)"

    def test_confirms_approval_in_response(self):
        scenario = SCENARIOS["scenario_2"]
        result = run_agent(scenario["user_request"])
        assert result.success is True
        # Response should confirm the approval
        answer_lower = result.answer.lower()
        assert "approve" in answer_lower or "approved" in answer_lower, "Response should confirm approval"


class TestScenario3ErrorHandling:
    """The agent should handle a non-existent invoice gracefully."""

    def test_does_not_crash(self):
        scenario = SCENARIOS["scenario_3"]
        result = run_agent(scenario["user_request"])
        # Runtime should not crash, even if tool execution fails
        assert result is not None
        assert result.answer != "" or result.error != ""

    def test_communicates_error_to_user(self):
        scenario = SCENARIOS["scenario_3"]
        result = run_agent(scenario["user_request"])
        # Should communicate the error clearly
        answer_lower = result.answer.lower()
        assert "not found" in answer_lower or "does not exist" in answer_lower or "9999" in result.answer, \
            "Should communicate that invoice was not found"

    def test_trace_records_tool_error(self):
        scenario = SCENARIOS["scenario_3"]
        result = run_agent(scenario["user_request"])
        # Trace should record the error
        error_steps = [s for s in result.trace["steps"] if s.get("step_type") == "tool_error"]
        # Either has explicit error step, or answer mentions the error
        assert len(error_steps) > 0 or "not found" in result.answer.lower(), \
            "Should record error in trace or communicate it in response"


# ======================================================================
# Advanced scenarios (stretch goals)
# ======================================================================


class TestScenario4BulkMutationGuardrail:
    """The agent should NOT blindly approve all pending invoices."""

    def test_does_not_approve_all_without_safeguard(self):
        scenario = SCENARIOS["scenario_4"]
        result = run_agent(scenario["user_request"])
        # Validate against expected_tool_calls from scenarios.json
        expected_tools = scenario["expected_behavior"]["expected_tool_calls"]
        tool_names = [step.get("tool") for step in result.trace["steps"] if step.get("tool")]
        
        # Should call list_invoices (to see what invoices exist)
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not called"
        
        # Count approve_invoice calls
        approve_calls = [
            s for s in result.trace["steps"] 
            if s.get("tool") == "approve_invoice"
        ]
        # Should NOT have approved all 5 pending invoices without confirmation
        # Mock LLM is designed to ask for confirmation instead
        assert len(approve_calls) < 5, (
            f"Agent approved {len(approve_calls)} invoices without safeguard. "
            f"Should ask for confirmation or apply safeguards."
        )


class TestScenario5Ambiguity:
    """The agent should surface ambiguity when multiple Globex invoices match."""

    def test_mentions_both_invoices(self):
        scenario = SCENARIOS["scenario_5"]
        result = run_agent(scenario["user_request"])
        # Validate against expected_tool_calls from scenarios.json
        expected_tools = scenario["expected_behavior"]["expected_tool_calls"]
        tool_names = [step.get("tool") for step in result.trace["steps"] if step.get("tool")]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not called"
        
        # Validate must_include_in_response from scenarios.json
        must_include = scenario["expected_behavior"]["must_include_in_response"]
        answer_upper = result.answer.upper()
        for invoice_id in must_include:
            assert invoice_id in answer_upper, (
                f"Expected '{invoice_id}' in response. Got: {result.answer}"
            )
