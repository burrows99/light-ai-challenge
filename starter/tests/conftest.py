"""Pytest configuration and fixtures."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest


# Store traces during test execution
_test_traces = {}


@pytest.fixture
def trace_output_dir():
    """Get the trace output directory from environment or use default."""
    trace_dir = os.getenv("TRACE_OUTPUT_DIR", "traces")
    output_path = Path(trace_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results and dump traces."""
    outcome = yield
    rep = outcome.get_result()
    
    # Only dump traces after test call phase (not setup/teardown)
    if rep.when == "call":
        test_name = item.nodeid.replace("::", "_").replace("/", "_")
        
        # Check if any trace data was captured in the test
        if hasattr(item, 'test_trace_data'):
            trace_output_dir = os.getenv("TRACE_OUTPUT_DIR", "traces")
            output_path = Path(trace_output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            trace_file = output_path / f"{test_name}_{timestamp}.json"
            
            with open(trace_file, 'w') as f:
                json.dump(item.test_trace_data, f, indent=2)

