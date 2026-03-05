"""Runtime configuration."""

from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    """Configuration for agent runtime."""
    
    max_iterations: int = 10
    timeout_seconds: int = 60
    max_retries: int = 3
    enable_trace: bool = True
