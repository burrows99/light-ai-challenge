"""Unit tests for Trace Recorder."""

from datetime import datetime, timezone

from light_agent.trace.trace_recorder import TraceRecorder


def test_trace_add_step():
    """Test adding a step to the trace."""
    trace = TraceRecorder()
    
    trace.record_step(
        step_type="tool_call",
        tool="list_invoices",
        arguments={"status": "pending"}
    )
    
    assert len(trace.steps) == 1
    assert trace.steps[0]["step_type"] == "tool_call"
    assert trace.steps[0]["tool"] == "list_invoices"


def test_trace_multiple_steps():
    """Test adding multiple steps."""
    trace = TraceRecorder()
    
    trace.record_step(step_type="llm_decision", content="Analyzing request")
    trace.record_step(step_type="tool_call", tool="get_invoice")
    trace.record_step(step_type="final_answer", content="Here is the result")
    
    assert len(trace.steps) == 3


def test_trace_step_includes_timestamp():
    """Test that steps include timestamps."""
    trace = TraceRecorder()
    
    before = datetime.now(timezone.utc)
    trace.record_step(step_type="tool_call", tool="test")
    after = datetime.now(timezone.utc)
    
    step_timestamp = trace.steps[0]["timestamp"]
    assert isinstance(step_timestamp, str)
    # Timestamp should be between before and after
    step_dt = datetime.fromisoformat(step_timestamp.replace('Z', '+00:00'))
    assert before <= step_dt <= after


def test_trace_step_includes_duration():
    """Test that steps can include duration."""
    trace = TraceRecorder()
    
    trace.record_step(
        step_type="tool_call",
        tool="test",
        duration_ms=123.45
    )
    
    assert trace.steps[0]["duration_ms"] == 123.45


def test_trace_export():
    """Test exporting trace to dict."""
    trace = TraceRecorder()
    
    trace.record_step(step_type="start", content="Begin")
    trace.record_step(step_type="end", content="Finish")
    
    exported = trace.export()
    
    assert "steps" in exported
    assert len(exported["steps"]) == 2
    assert "total_steps" in exported


def test_trace_get_summary():
    """Test getting a trace summary."""
    trace = TraceRecorder()
    
    trace.record_step(step_type="llm_decision")
    trace.record_step(step_type="tool_call", tool="list_invoices")
    trace.record_step(step_type="tool_call", tool="approve_invoice")
    trace.record_step(step_type="final_answer")
    
    summary = trace.get_summary()
    
    assert summary["total_steps"] == 4
    assert summary["tool_calls"] == 2
