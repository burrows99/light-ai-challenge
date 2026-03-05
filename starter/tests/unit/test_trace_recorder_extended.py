"""Unit tests for TraceRecorder additional features."""

import json
import tempfile
from pathlib import Path

from light_agent.trace.trace_recorder import TraceRecorder


def test_dump_to_file():
    """Test dumping trace to a file."""
    recorder = TraceRecorder()
    recorder.record_step(step_type="start", content="Starting")
    recorder.record_step(step_type="tool_call", tool="test_tool", arguments={"arg": "value"})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "trace.json"
        recorder.dump_to_file(str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert "steps" in data
        assert len(data["steps"]) == 2
        assert data["total_steps"] == 2


def test_dump_to_file_creates_directories():
    """Test that dump_to_file creates parent directories if they don't exist."""
    recorder = TraceRecorder()
    recorder.record_step(step_type="test", content="Test")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "nested" / "dir" / "trace.json"
        recorder.dump_to_file(str(output_path))
        
        assert output_path.exists()
        assert output_path.parent.exists()
