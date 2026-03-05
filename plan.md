Treat this like building a **small infrastructure service**, not a script. The reviewers explicitly want platform thinking: isolation, reproducibility, observability, configurability. Using **pytest + uv + Docker Compose** signals that mindset immediately.

The development strategy becomes:

1. deterministic environment (uv + docker)
2. behaviour-first tests (pytest)
3. independently testable modules
4. integration tests
5. runtime assembly
6. sandbox runner

Think of it like constructing a distributed system in miniature.

---

# 0. Development Environment Strategy

The environment should be reproducible in two ways:

**Local fast dev**

```
uv sync
uv run pytest
```

**Containerized runtime**

```
docker compose up
```

Why both?

Platform teams expect:

• fast iteration locally
• reproducible CI / infra execution

---

# 1. Project Structure (Designed for TDD)

This structure isolates modules for independent testing.

```
light-agent-runtime/

README.md
DESIGN.md
PRODUCTION.md

pyproject.toml
uv.lock

docker-compose.yml
Dockerfile

.env.example

data/
    tools.json
    mock_data.json
    scenarios.json

src/
    light_agent/

        __init__.py

        config/
            runtime_config.py

        models/
            tool.py
            llm.py
            trace.py
            agent_state.py

        tools/
            tool_registry.py
            tool_executor.py
            tool_validator.py

        llm/
            llm_interface.py
            mock_llm_client.py
            openai_llm_client.py

        trace/
            trace_recorder.py

        runtime/
            agent_runtime.py
            runtime_loop.py
            guardrails.py
            retry_policy.py

        sandbox/
            cli_runner.py

tests/

    unit/

        test_tool_registry.py
        test_tool_executor.py
        test_trace_recorder.py
        test_llm_interface.py
        test_agent_state.py
        test_runtime_loop.py

    integration/

        test_agent_runtime.py
        test_scenarios.py

```

Key design decision:

Unit tests validate modules in isolation.
Integration tests validate the full agent behaviour.

---

# 2. pyproject.toml (uv-based)

Use `uv` instead of pip/poetry.

```
[project]
name = "light-agent"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "pydantic",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Then install:

```
uv sync --all-extras
```

Run tests:

```
uv run pytest
```

---

# 3. Docker Setup

The container ensures runtime reproducibility.

Dockerfile:

```
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --system

COPY . .

CMD ["uv", "run", "python", "-m", "light_agent.sandbox.cli_runner"]
```

docker-compose.yml:

```
version: "3.9"

services:
  agent:
    build: .
    volumes:
      - .:/app
    command: uv run pytest
```

This allows:

```
docker compose run agent
```

to run tests in an isolated environment.

---

# 4. TDD Development Plan

We deliberately introduce **failing tests first**.

Modules are implemented one by one.

Order matters.

Build from **pure logic → orchestration → integration**.

---

# Step 1 — Tool Registry

Purpose:

Load tool schemas and expose them to the runtime.

Test first.

`tests/unit/test_tool_registry.py`

```
def test_load_tools():
    registry = ToolRegistry("data/tools.json")

    tools = registry.list_tools()

    assert "list_invoices" in tools
    assert "approve_invoice" in tools
```

Expected failure:

```
ModuleNotFoundError: ToolRegistry
```

Implementation lives in:

```
src/light_agent/tools/tool_registry.py
```

Once implemented, test passes.

---

# Step 2 — Tool Executor

Tools should be executable independently of the agent.

Test:

`tests/unit/test_tool_executor.py`

```
def test_list_pending_invoices():

    registry = ToolRegistry("data/tools.json")
    executor = ToolExecutor(registry, "data/mock_data.json")

    result = executor.execute(
        "list_invoices",
        {"status": "pending"}
    )

    assert isinstance(result, list)
```

Executor logic:

```
tool_name
validate args
load mock data
execute
return result
```

Agent runtime still does not exist.

---

# Step 3 — Execution Trace

The runtime must produce structured logs.

Test first.

`tests/unit/test_trace_recorder.py`

```
def test_trace_add_step():

    trace = TraceRecorder()

    trace.record_step(
        step_type="tool_call",
        tool="list_invoices"
    )

    assert len(trace.steps) == 1
```

Trace model records:

```
step_id
step_type
tool
args
result
duration_ms
timestamp
```

TraceRecorder becomes central observability infrastructure.

---

# Step 4 — LLM Interface

Define a provider abstraction.

Test:

`tests/unit/test_llm_interface.py`

```
def test_mock_llm_returns_action():

    llm = MockLLMClient()

    response = llm.generate(
        messages=[{"role": "user", "content": "show invoices"}],
        tools=[]
    )

    assert "type" in response
```

The response schema must be consistent.

Example:

```
{
  "type": "tool_call",
  "tool": "list_invoices",
  "arguments": {}
}
```

or

```
{
  "type": "final_answer",
  "content": "Here are the invoices"
}
```

---

# Step 5 — Agent State

Runtime state should be separate from runtime logic.

Test:

`tests/unit/test_agent_state.py`

```
def test_agent_state_tracks_messages():

    state = AgentState()

    state.add_user_message("hello")

    assert len(state.messages) == 1
```

State tracks:

```
messages
trace
iteration
status
```

---

# Step 6 — Runtime Loop (Core Engine)

Now implement the **agent loop**.

Test:

`tests/unit/test_runtime_loop.py`

```
def test_runtime_executes_tool():

    runtime = build_runtime()

    result = runtime.run("show pending invoices")

    assert result.success
```

Runtime loop:

```
while not finished

    decision = llm.generate()

    if tool_call
        execute_tool
        append result

    if final_answer
        return
```

Safety features:

```
max_iterations
timeouts
retry_policy
```

These live in `runtime_config`.

---

# Step 7 — Integration Tests

Now validate system behaviour.

`tests/integration/test_agent_runtime.py`

```
def test_agent_handles_tool_error():

    runtime = build_runtime()

    result = runtime.run("Approve invoice INV-9999")

    assert result.success is False
```

The runtime should not crash.

Instead it returns a structured error.

---

# Step 8 — Scenario Tests

Finally run the provided scenarios.

`tests/integration/test_scenarios.py`

Example:

```
def test_simple_query():

    runtime = build_runtime()

    result = runtime.run(
        "Show me unpaid invoices over €5000"
    )

    assert result.success
```

These tests simulate the actual take-home evaluation.

---

# 5. Sandbox Terminal Runner

Once everything works, add the sandbox.

```
uv run python -m light_agent.sandbox.cli_runner
```

CLI behaviour:

```
Light Agent Runtime

>>> show unpaid invoices

Step 1: LLM decision
Step 2: Tool call list_invoices
Step 3: Final answer

Result:
3 invoices found
```

This helps debug the agent loop interactively.

---

# 6. Development Workflow

Daily workflow becomes:

Start environment

```
uv sync
```

Run tests

```
uv run pytest -v
```

Run agent sandbox

```
uv run python -m light_agent.sandbox.cli_runner
```

Run inside container

```
docker compose run agent
```

---

# 7. What This Demonstrates to Reviewers

This structure shows:

Clear runtime architecture
Modular components
Provider abstraction
Observability (trace system)
Safe execution model
Test-driven engineering

In other words: **platform engineering discipline**.

---

One last conceptual insight worth carrying around while building this:
an agent runtime is basically **a deterministic state machine wrapped around a probabilistic planner**. The LLM proposes actions, but your runtime enforces order, safety, and traceability. The entire engineering challenge is making that probabilistic brain behave inside a predictable system.
