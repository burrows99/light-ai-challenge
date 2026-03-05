# Design Document

> Explain the key decisions you made while building your agent runtime.
> This doesn't need to be long — 1–2 pages is ideal. We care about
> *clarity of thinking*, not volume.

## Architecture Overview

The runtime is built on **SOLID principles** with dependency injection and protocol-based abstractions. This architecture enables easy testing, extensibility, and maintainability while respecting Light AI's provided infrastructure.

```
┌──────────────────────────────────────────────────────────────────┐
│                        AgentRuntime                              │
│                  (ReAct Loop Orchestrator)                       │
│           Depends on abstractions, not implementations           │
└────┬──────────────┬───────────────┬────────────────┬────────────┘
     │              │               │                │
     ▼              ▼               ▼                ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│LLMProvider  │ │ToolExecutor  │ │Tool         │ │Trace         │
│(Protocol)   │ │(Protocol)    │ │Registry     │ │Recorder      │
└──────┬──────┘ └──────┬───────┘ └─────────────┘ └──────────────┘
       │               │
       ▼               ▼
┌─────────────┐ ┌──────────────┐
│LightAI      │ │LightAI       │
│LLM Adapter  │ │Tool Adapter  │
│             │ │              │
└──────┬──────┘ └──────┬───────┘
       │               │
       ▼               ▼
┌─────────────┐ ┌──────────────┐
│MockLLM      │ │MockTool      │
│Client       │ │Executor      │
│(Light AI)   │ │(Light AI)    │
└─────────────┘ └──────────────┘

┌──────────────────────────────────────┐
│    Strategy Pattern Components       │
├──────────────────────────────────────┤
│ • ConversationManager                │
│   (message state management)         │
│ • ToolOrchestrator                   │
│   (tool execution coordination)      │
└──────────────────────────────────────┘
```

### Core Components

**Protocols (`protocols/`)**: Define abstract interfaces that the runtime depends on
- `LLMProvider`: Single method `chat(messages, tools)` for LLM interactions
- `ToolExecutor`: Single method `execute(tool_name, arguments)` for tool execution

**Adapters (`adapters/`)**: Bridge between protocols and Light AI's implementations
- `LightAILLMAdapter`: Wraps `MockLLMClient` to implement `LLMProvider` protocol
- `LightAIToolExecutorAdapter`: Wraps `MockToolExecutor` to implement `ToolExecutor` protocol
- Thin delegation layer that enables swapping implementations

**Strategies (`strategies/`)**: Extract single-responsibility behaviors
- `ConversationManager`: Handles message state (add user/assistant/tool messages)
- `ToolOrchestrator`: Coordinates tool execution with tracing and error handling

**Core Runtime (`runtime/`)**:
- `AgentRuntime`: Orchestrates the ReAct loop using injected dependencies
- `RuntimeConfig`: Configuration (max iterations, timeouts, etc.)

**Supporting Components**:
- `ToolRegistry`: Loads and validates tool definitions from JSON using Pydantic
- `TraceRecorder`: Records execution steps for observability and debugging
- `Tool` models: Pydantic schemas for type-safe tool definitions

### Data Flow (ReAct Pattern)

1. **User Input** → AgentRuntime receives the request
2. **REASON** → LLM (via `LLMProvider` protocol) analyzes conversation and decides next action
3. **ACT** → `ToolOrchestrator` executes tool calls through `ToolExecutor` protocol
4. **OBSERVE** → Results added to conversation via `ConversationManager`
5. **Loop** → Repeat steps 2-4 until final answer or max iterations
6. **Trace** → All steps recorded by `TraceRecorder` for observability

### SOLID Principles in Practice

**Single Responsibility**: Each class has one clear purpose
- `AgentRuntime`: Orchestrate ReAct loop
- `ConversationManager`: Manage message state
- `ToolOrchestrator`: Execute tools
- `TraceRecorder`: Record execution

**Open/Closed**: Extensible without modification
- Add new LLM providers (OpenAI, Anthropic) without touching `AgentRuntime`
- Add new tool executors (API, sandbox) without changing core logic

**Liskov Substitution**: Any implementation works
- Any `LLMProvider` can replace another
- Any `ToolExecutor` can replace another

**Interface Segregation**: Minimal, focused interfaces
- `LLMProvider`: Just `chat()`
- `ToolExecutor`: Just `execute()`

**Dependency Inversion**: Depend on abstractions
- `AgentRuntime` depends on protocols, not concrete classes
- Light AI's implementations injected via adapters

## Key Design Decisions

### 1. Protocol-Based Architecture with Dependency Injection

**Decision**: Build the runtime around protocol abstractions (`LLMProvider`, `ToolExecutor`) with implementations injected through constructors.

**Alternatives Considered**:
- Direct coupling to Light AI's concrete classes
- Abstract base classes (ABC) instead of protocols
- Inheritance-based extension

**Why This Approach**:
- **Testability**: Mock dependencies easily without Light AI's infrastructure
- **Flexibility**: Swap LLM providers (OpenAI, Anthropic, local models) without modifying core logic
- **Type Safety**: Protocols provide clear contracts with better mypy support than ABCs
- **Production Ready**: Can run mock and real implementations side-by-side
- **Clean Architecture**: High-level policy (AgentRuntime) doesn't depend on low-level details

### 2. Adapter Pattern for Light AI Integration

**Decision**: Wrap Light AI's `MockLLMClient` and `MockToolExecutor` in thin adapters that implement our protocols.

**Alternatives Considered**:
- Modify Light AI's classes directly (breaks their encapsulation)
- Inherit from Light AI's classes (tight coupling)
- Bypass Light AI entirely (defeats the challenge's purpose)

**Why This Approach**:
- **Respects Light AI**: Uses their tooling without modification
- **Decoupling**: AgentRuntime never sees Light AI's specific classes
- **Single Integration Point**: Adapter changes don't ripple through the codebase
- **Future-Proof**: Easy to add `OpenAIAdapter`, `AnthropicAdapter` later
- **Standard Pattern**: Classic Gang of Four adapter pattern

### 3. Strategy Pattern for Specialized Behaviors

**Decision**: Extract `ConversationManager` (message handling) and `ToolOrchestrator` (tool execution) as separate strategy classes.

**Alternatives Considered**:
- Keep all logic in AgentRuntime (god object antipattern)
- Use standalone functions (loses encapsulation)
- Single "ExecutionContext" class (violates single responsibility)

**Why This Approach**:
- **Single Responsibility**: Each class has one clear job
- **Reduced Complexity**: AgentRuntime focuses purely on orchestration (~70 lines)
- **Independent Testing**: Test conversation logic separately from tool logic
- **Extensibility**: Easy to add parallel execution, conversation pruning, caching
- **Composability**: Can mix and match different strategies

### 4. Pydantic Models for Type-Safe Tool Definitions

**Decision**: Use Pydantic `BaseModel` for `Tool`, `ToolParameter`, and `ToolMetadata` validation.

**Alternatives Considered**:
- Plain dictionaries (no validation, no type safety)
- TypedDict (no runtime validation)
- JSON Schema only (separate from Python types)

**Why This Approach**:
- **Development-Time Safety**: IDE autocomplete, mypy catches errors
- **Runtime Validation**: Clear error messages when tools.json is malformed
- **API Boundaries**: Clean serialization/deserialization
- **Industry Standard**: Pydantic is ubiquitous in Python APIs
- **Documentation**: Models serve as self-documenting schemas

### 5. Comprehensive Tracing from Day One

**Decision**: Build `TraceRecorder` as a first-class component, not an afterthought.

**Alternatives Considered**:
- Standard logging only (unstructured, hard to query)
- Add tracing later when "needed" (expensive to retrofit)
- External observability tools (overkill for MVP)

**Why This Approach**:
- **Agent Debugging**: Impossible to debug agent behavior without structured traces
- **Test Validation**: Scenarios verify what the agent actually did, not just final output
- **Compliance**: Financial systems need audit trails
- **Performance Analysis**: Trace data enables optimization
- **Low Cost**: ~50 lines of code, zero external dependencies

### 6. Simple ReAct Loop Over Complex Orchestration

**Decision**: Implement a straightforward ReAct pattern (Reason → Act → Observe) without graph-based orchestration.

**Alternatives Considered**:
- LangGraph-style DAG orchestration
- State machine with explicit transitions
- Multi-agent architecture with handoffs

**Why This Approach**:
- **Sufficient**: Handles all 5 scenarios (35/35 tests pass)
- **Understandable**: New developers grasp the logic quickly
- **Debuggable**: Linear flow easier to trace than graphs
- **YAGNI**: Don't build complexity we don't need yet
- **Evolvable**: SOLID design makes migration to graphs straightforward when needed

### 7. Test-Driven Development with Behavior Verification

**Decision**: Write tests first, verify behavior (not implementation), maintain 100% pass rate.

**Why This Approach**:
- **Scenarios as Specs**: Challenge scenarios define acceptance criteria
- **Refactor Confidence**: SOLID architecture changes didn't break any tests
- **Living Documentation**: Tests show how to use the runtime
- **Behavior Focus**: Tests verify outcomes, allowing implementation flexibility

## Trade-offs & Limitations

### Deliberate Simplifications

**1. Synchronous Execution Only**
- Current: All operations block until complete
- Production needs: Async/await for concurrent I/O operations
- Impact: Can't handle thousands of concurrent requests

**2. No Response Streaming**
- Current: LLM responses arrive all at once
- Production needs: Stream tokens as they're generated
- Impact: Poor perceived performance for long responses

**3. Single-Attempt Tool Execution**
- Current: Tools execute once with no retry logic
- Production needs: Exponential backoff, circuit breakers
- Impact: Transient network errors fail the entire request

**4. Serial Tool Execution**
- Current: Tools run one at a time
- Production needs: Parallel execution of independent calls
- Impact: Slower when multiple tools can run concurrently

**5. In-Memory State Only**
- Current: No persistence between runs
- Production needs: Database for history, audit logs
- Impact: No conversation context across sessions

**6. Single-Tenant Design**
- Current: No isolation between users
- Production needs: Multi-tenant with access controls
- Impact: Can't serve multiple customers safely

**7. No Rate Limiting**
- Current: Unlimited LLM API calls
- Production needs: Quota management, cost controls
- Impact: Runaway costs from misbehaving agents

**8. Static Tool Loading**
- Current: Tools loaded from filesystem at startup
- Production needs: Dynamic registration, hot reload
- Impact: Requires restart to add/update tools

### Production Blockers

**Security**:
- No authentication/authorization (anyone can approve invoices)
- No input sanitization (prompt injection vulnerabilities)
- No secrets management (API keys in environment variables)

**Reliability**:
- No timeout handling (agents can run indefinitely)
- No graceful degradation (LLM API down = complete failure)
- No health checks or readiness probes

**Observability**:
- No metrics collection (can't monitor performance)
- No cost tracking (can't budget LLM usage)
- No alerting (failures go unnoticed)

**Operations**:
- No versioning (can't deploy without breaking clients)
- No feature flags (all-or-nothing deployments)
- No rollback strategy (failed deployments are permanent)

## Future Enhancements

### 1. Graph-Based Orchestration (4 hours)

**Current Limitation**: Linear ReAct loop can't handle complex workflows.

**Proposed Solution**: Declarative graph builder inspired by LangGraph:

```python
from light_agent.graph import GraphBuilder

graph = (GraphBuilder()
    .add_node("classifier", classify_user_intent)
    .add_node("query_handler", handle_invoice_queries)
    .add_node("approval_handler", handle_approvals)
    .add_edge("classifier", "query_handler", when=lambda x: x.intent == "query")
    .add_edge("classifier", "approval_handler", when=lambda x: x.intent == "approve")
    .compile())

result = graph.run(user_input)
```

**Benefits**:
- Multi-agent orchestration (specialized agents per domain)
- Conditional routing based on classification
- Parallel branch execution
- Visual debugging (render graph as Mermaid/DOT)
- Better separation: classification ≠ execution

### 2. Async/Await with Streaming (3 hours)

**Current Limitation**: Synchronous blocking prevents scaling and poor UX.

**Proposed Solution**: Refactor to async with streaming support:

```python
async def run(self, query: str) -> AsyncIterator[StreamChunk]:
    """Stream results in real-time."""
    async for chunk in self.llm.stream_chat(messages):
        yield StreamChunk(type="llm_token", data=chunk)
        
    async for result in self.orchestrator.execute_parallel(tool_calls):
        yield StreamChunk(type="tool_result", data=result)
```

**Benefits**:
- Handle thousands of concurrent requests
- Real-time UI updates (show thinking process)
- Better perceived performance
- Enables WebSocket/SSE for live updates

### 3. Tool Execution Sandboxing (3 hours)

**Current Limitation**: Tools run in-process; malicious code can crash the runtime.

**Proposed Solution**: Execute tools in isolated containers:

```python
class SandboxedToolExecutor(ToolExecutor):
    async def execute(self, tool: str, args: dict, timeout: float = 30):
        # Run in isolated Docker container with resource limits
        result = await asyncio.create_subprocess_exec(
            "docker", "run", "--rm", "--network=none",
            "--memory=512m", "--cpus=0.5",
            f"tool-runner-{tool}",
            input=json.dumps(args),
            timeout=timeout
        )
        return json.loads(await result.stdout.read())
```

**Benefits**:
- Security: Tools can't access runtime memory/secrets
- Reliability: Tool crashes don't crash the agent
- Resource limits: Prevent runaway CPU/memory
- Multi-language: Tools in any language (Python, JS, Go, Rust)

### 4. Prompt Engineering Framework (2 hours)

**Current Limitation**: Prompts hard-coded in Light AI's client.

**Proposed Solution**: Prompt versioning and optimization system:

```python
class PromptManager:
    def get_prompt(self, variant: str = "default") -> str:
        """Get prompt with A/B testing support."""
        return self.store.get(f"prompts/react/{variant}")
    
    def optimize(self, metric: str = "cost"):
        """Find shortest prompt that maintains quality."""
        candidates = self.generate_variations()
        return self.evaluate(candidates, metric)
```

**Benefits**:
- A/B testing different prompts
- Cost optimization (shorter = cheaper)
- Version control and rollback
- Few-shot example management

### 5. Observability Stack (2 hours)

**Current Limitation**: Basic tracing insufficient for production monitoring.

**Proposed Solution**: OpenTelemetry integration with metrics:

```python
from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

tool_calls = meter.create_counter("agent.tool_calls")
llm_tokens = meter.create_counter("agent.llm_tokens")
latency = meter.create_histogram("agent.latency_ms")

with tracer.start_as_current_span("agent_run") as span:
    span.set_attribute("user_query", query)
    # ... execution ...
    latency.record(duration_ms)
```

**Benefits**:
- Real-time dashboards (Grafana/Datadog)
- Cost tracking per request/user
- Performance profiling
- Alerting on anomalies
