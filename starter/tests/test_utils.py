"""Test utilities for trace dumping."""

import os
from datetime import datetime
from pathlib import Path


def dump_trace_for_test(trace_dict: dict, test_name: str, test_file: str = "test") -> str:
    """Dump a trace dictionary to a file in the traces directory.
    
    Args:
        trace_dict: The trace dictionary to dump
        test_name: Name of the test
        test_file: Name of the test file (without .py extension)
        
    Returns:
        Path to the dumped trace file
    """
    # Get trace output directory from environment or use default
    trace_dir = os.getenv("TRACE_OUTPUT_DIR", "traces")
    output_path = Path(trace_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create a timestamp for the trace file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    # Create trace file path
    trace_file = output_path / f"{test_file}_{test_name}_{timestamp}.json"
    
    # Write trace to file
    import json
    with open(trace_file, 'w') as f:
        json.dump(trace_dict, f, indent=2)
    
    return str(trace_file)
