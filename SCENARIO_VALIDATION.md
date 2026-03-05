# Scenario Test Validation Enhancement

## Overview
Enhanced `test_scenarios.py` to validate agent behavior against the expected specifications defined in `scenarios.json`.

## Changes Made

### 1. TestScenario1SimpleQuery (Simple Read Query)
**Enhancements:**
- ✅ Validates `expected_tool_calls` from scenarios.json
- ✅ Validates `must_include_in_response` (INV-001, INV-003, INV-005)
- ✅ Ensures all expected invoice IDs appear in the agent's response

**Tests:**
- `test_returns_final_response` - Validates basic success
- `test_calls_list_invoices` - Validates correct tool usage
- `test_response_includes_expected_invoices` - Validates response content against JSON spec
- `test_execution_trace_is_populated` - Validates trace recording

### 2. TestScenario2MultiStep (Mutation Workflow)
**Enhancements:**
- ✅ Validates `expected_tool_calls` from scenarios.json
- ✅ Validates tool ordering (list_invoices must come before approve_invoice)
- ✅ Validates approval confirmation in response

**Tests:**
- `test_calls_tools_in_correct_order` - Validates tool call sequence matches JSON spec
- `test_approves_correct_invoice` - Validates correct invoice approved
- `test_confirms_approval_in_response` - Validates user confirmation in response

### 3. TestScenario3ErrorHandling (Error Handling)
**Enhancements:**
- ✅ Validates `expected_tool_calls` from scenarios.json
- ✅ Validates error is communicated to user
- ✅ Validates error is recorded in trace

**Tests:**
- `test_does_not_crash` - Validates graceful error handling
- `test_communicates_error_to_user` - Validates error communication
- `test_trace_records_tool_error` - Validates error recorded in trace

### 4. TestScenario4BulkMutationGuardrail (Safety Guardrails)
**Enhancements:**
- ✅ Validates `expected_tool_calls` from scenarios.json
- ✅ Validates agent doesn't blindly approve all invoices
- ✅ Ensures safeguards are in place (<5 approve_invoice calls)

**Tests:**
- `test_does_not_approve_all_without_safeguard` - Validates guardrails prevent bulk mutations

### 5. TestScenario5Ambiguity (Ambiguity Resolution)
**Enhancements:**
- ✅ Validates `expected_tool_calls` from scenarios.json
- ✅ Validates `must_include_in_response` (INV-003, INV-004)
- ✅ Ensures both matching invoices are mentioned when ambiguity exists

**Tests:**
- `test_mentions_both_invoices` - Validates ambiguity is surfaced to user

## Validation Pattern

Each enhanced test follows this pattern:

```python
def test_example(self):
    # Load scenario specification from scenarios.json
    scenario = SCENARIOS["scenario_X"]
    result = run_agent(scenario["user_request"])
    
    # Validate expected_tool_calls
    expected_tools = scenario["expected_behavior"]["expected_tool_calls"]
    tool_names = [step.get("tool") for step in result.trace["steps"] if step.get("tool")]
    for expected_tool in expected_tools:
        assert expected_tool in tool_names
    
    # Validate must_include_in_response (if present)
    if "must_include_in_response" in scenario["expected_behavior"]:
        must_include = scenario["expected_behavior"]["must_include_in_response"]
        answer_upper = result.answer.upper()
        for item in must_include:
            assert item in answer_upper
```

## Test Results

### Local Tests (macOS, Python 3.12.11)
```
35 passed in 0.78s
```

### Docker Tests (Linux, Python 3.11.15)
```
35 passed in 1.05s
```

### Test Breakdown
- 4 Integration tests (agent runtime)
- 12 Scenario tests (5 scenarios, multiple assertions each)
- 19 Unit tests (LLM interface, tool executor, tool registry, trace recorder)

## Benefits

1. **Comprehensive Validation**: Tests now validate against Light AI's exact specifications
2. **Maintainability**: Easy to update validations when scenarios.json changes
3. **Clarity**: Clear assertions about what behavior is expected
4. **Coverage**: All 5 scenarios fully validated against their expected_behavior specs
5. **Reproducibility**: Tests pass consistently in both local and Docker environments

## Data Files Used

- `scenarios.json` - Defines 5 test scenarios with expected behavior specifications
- `mock_data.json` - Provides invoice and user data for tool execution
- `tools.json` - Defines available tools and their parameters

All data files are now fully integrated into the testing pipeline.
