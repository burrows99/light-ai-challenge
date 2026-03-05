# Design Document

> Explain the key decisions you made while building your agent runtime.
> This doesn't need to be long — 1–2 pages is ideal. We care about
> *clarity of thinking*, not volume.

## Architecture Overview

<!-- How is your runtime structured? What are the main components and how
     do they interact? A simple diagram (ASCII or a linked image) is welcome. -->

The runtime follows a modular, dependency-injected architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    AgentRuntime                         │
│  (Orchestrator - ReAct loop implementation)             │
└───────┬─────────────┬─────────────┬─────────────────────┘
        │             │             │
        ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────────┐
  │MockLLM   │  │MockTool  │  │TraceRecorder │
  │Client    │  │Executor  │  │(Observability)│
  │(Light AI)│  │(Light AI)│  │              │
  └──────────┘  └────┬─────┘  └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │ ToolRegistry │
              │ (loads tools │
              │  from JSON)  │
              └──────────────┘
```

**Core Components:**

1. **AgentRuntime**: Orchestrates the ReAct loop (Reason → Act → Observe)
2. **MockLLMClient**: Light AI's provided LLM interface (decision-making)
3. **MockToolExecutor**: Light AI's provided tool execution (actions)
4. **ToolRegistry**: Loads and validates tool definitions from JSON
5. **TraceRecorder**: Records execution steps for observability
6. **RuntimeConfig**: Controls max iterations and other runtime parameters

**Data Flow:**
1. User input → AgentRuntime
2. Runtime calls LLM with conversation history + available tools
3. LLM returns action (tool call or final answer)
4. If tool call: Executor runs it, result fed back to LLM
5. Loop continues until final answer or max iterations
6. All steps recorded in trace for debugging

## Key Design Decisions

<!-- For each significant choice you made, briefly explain:
     - What the decision was
     - What alternatives you considered
     - Why you chose this approach -->

### 1. Use Light AI's Provided Components (Not Custom Implementations)

**Decision**: Integrate Light AI's `MockLLMClient` and `MockToolExecutor` directly rather than wrapping them.

**Alternatives Considered**:
- Build custom abstractions around Light AI's classes
- Create adapter patterns for future LLM swapping

**Why This Approach**:
- Reduces code complexity and maintenance burden
- Respects the challenge's intent to use provided tooling
- Light AI's classes already handle the hard parts (prompt engineering, tool schema generation)
- Can always add abstractions later when requirements are clearer

### 2. Pydantic Models for Tool Validation

**Decision**: Use Pydantic `BaseModel` for Tool, ToolParameter, and ToolMetadata validation.

**Alternatives Considered**:
- Plain dictionaries with manual validation
- TypedDict with runtime type checking
- JSON Schema validation only

**Why This Approach**:
- Type safety at development time (IDE autocomplete, mypy)
- Runtime validation with clear error messages
- Easy serialization/deserialization for API boundaries
- Industry standard for Python data validation

### 3. Trace Recording as First-Class Citizen

**Decision**: Build comprehensive trace recording from day one, not as an afterthought.

**Alternatives Considered**:
- Log-based observability only
- Add tracing later when needed

**Why This Approach**:
- Agent debugging is impossible without execution traces
- Traces enable scenario validation (test what the agent actually did)
- Structured traces better than unstructured logs for analysis
- Cheap to add now, expensive to retrofit later
- Enables compliance/audit trails for financial use cases

### 4. Simple ReAct Loop (No Graph-Based Orchestration)

**Decision**: Implement a straightforward ReAct loop: LLM decides → Execute tool → Repeat.

**Alternatives Considered**:
- LangGraph-style graph orchestration with nodes and edges
- State machine with explicit transitions
- Multiple specialized agents with handoffs

**Why This Approach**:
- Meets all current requirements (5 scenarios pass)
- Easy to understand and debug
- Lower cognitive overhead for new developers
- Can evolve to graphs when complexity demands it
- YAGNI principle: don't build what you don't need yet

### 5. Test-Driven Development Throughout

**Decision**: Build with strict TDD (Red → Green → Refactor).

**Why This Approach**:
- Scenarios define clear success criteria
- Tests as documentation (show how to use the runtime)
- Confidence in refactoring (removed custom implementations safely)
- 35/35 tests passing = verifiable correctness

## Trade-offs & Limitations

<!-- What did you deliberately leave out or simplify given the time
     constraint? What would break if this were used in production as-is? -->

### What Was Simplified

1. **No Async/Await**: Synchronous execution only. Production would need async for I/O-bound operations (API calls, DB queries).

2. **No Streaming**: LLM responses arrive all at once. Real users expect streaming for perceived performance.

3. **No Error Recovery**: Single try per tool call. Production needs retries with exponential backoff.

4. **No Concurrency**: Tools execute serially. Could parallelize independent tool calls.

5. **In-Memory Only**: No persistence layer. Production needs databases for conversation history, audit logs.

6. **Single-Tenant**: No user/tenant isolation. Production serves multiple teams/customers.

7. **No Rate Limiting**: Can hammer LLM APIs. Production needs quota management.

8. **Hard-Coded Tool Loading**: Reads from file system. Production needs dynamic tool registration.

### What Would Break in Production

- **No authentication/authorization**: Any code can approve invoices
- **No input validation**: Could inject malicious prompts
- **No cost tracking**: LLM calls accumulate unbounded costs
- **No timeout handling**: Long-running agents block indefinitely
- **No graceful degradation**: LLM API down = everything down
- **No versioning**: Can't deploy new agents without breaking old ones

## What I'd Do Differently With More Time

<!-- If you had another 4–8 hours, what would you change or add?
     Be specific — "make it better" doesn't tell us much. -->

### 1. LangGraph-Style Graph Builder (4 hours)

Build a declarative graph orchestration system:

```python
from light_agent.graph import GraphBuilder, Node

graph = GraphBuilder()
    .add_node("classifier", classify_intent)
    .add_node("invoice_handler", handle_invoices)
    .add_node("approval_handler", handle_approvals)
    .add_edge("classifier", "invoice_handler", when=lambda x: x.intent == "query")
    .add_edge("classifier", "approval_handler", when=lambda x: x.intent == "approve")
    .compile()
```

**Benefits**:
- Multi-agent orchestration (specialized agents per domain)
- Conditional routing based on intent classification
- Parallel execution of independent branches
- Better separation of concerns (classification ≠ execution)
- Visual debugging (render graph as DOT/Mermaid)

### 2. Sandbox Environment with Loop Control (2 hours)

Re-implement interactive CLI with better UX:

```python
# Auto-loop until completion or timeout
runtime.run_until_complete(
    query="Process all overdue invoices",
    timeout_seconds=300,
    auto_approve=False  # Require human confirmation
)
```

**Features**:
- Streaming output to terminal (show thinking in real-time)
- Breakpoints (pause before dangerous operations)
- Interactive approval prompts
- Rich formatting with syntax highlighting
- Replay traces from files

### 3. Tool Execution Sandboxing (3 hours)

**Problem**: Current tools run in-process. Malicious tools could crash the runtime.

**Solution**: Execute tools in isolated processes or containers:

```python
class SandboxedToolExecutor:
    def execute(self, tool: str, args: dict, timeout: float = 30):
        # Run in subprocess with resource limits
        result = subprocess.run(
            ["docker", "run", "--rm", "--network=none", 
             "--memory=512m", "--cpus=0.5",
             f"tool-{tool}", json.dumps(args)],
            timeout=timeout,
            capture_output=True
        )
        return json.loads(result.stdout)
```

**Benefits**:
- Security: Tools can't access runtime memory/secrets
- Reliability: Tool crashes don't crash the runtime
- Resource limits: Prevent runaway CPU/memory
- Multi-language: Tools can be in any language (not just Python)

### 4. Prompt Optimization Framework (2 hours)

Currently, prompts are hard-coded in `MockLLMClient`. Production needs:

- A/B testing different prompts
- Prompt versioning and rollback
- Cost optimization (shorter prompts = cheaper)
- Few-shot example management

### 5. Streaming & Async (3 hours)

Refactor to async/await:

```python
async def run(self, query: str) -> AsyncIterator[StreamChunk]:
    async for chunk in self.llm.stream_chat(messages):
        yield chunk  # Real-time updates to UI
```

Enables better UX and scales to thousands of concurrent requests.
