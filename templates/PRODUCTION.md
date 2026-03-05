# Production Readiness Plan

> Imagine this agent runtime needs to go to production at Light, serving
> multiple product teams building AI features for finance customers.
> How would you get there?
>
> Be concrete and opinionated. We'd rather see a strong point of view
> on 3 topics than a shallow take on 10.

## Deployment & Operations

<!-- How would you deploy this? What does the infrastructure look like?
     How do you handle versioning, rollbacks, and zero-downtime deploys? -->

### Infrastructure Architecture

**Runtime as a Service (RaaS)**:

```
┌───────────────────────────────────────────────────────┐
│               API Gateway (Kong/Envoy)               │
│     Rate limiting, Auth, Request routing            │
└────────────┬──────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────────────────┐
│          Agent Runtime Service (K8s Pods)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Pod 1    │  │ Pod 2    │  │ Pod N    │          │
│  │ (Async)  │  │ (Async)  │  │ (Async)  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────┬─────────────────────────────────────────┘
              │
    ┌─────────┴─────────┬─────────────┬──────────────┐
    ▼                   ▼             ▼              ▼
┌────────┐      ┌────────────┐  ┌─────────┐   ┌──────────┐
│LLM API │      │ PostgreSQL │  │ Redis   │   │ S3       │
│(OpenAI)│      │(Traces/    │  │(Cache/  │   │(Trace    │
│        │      │ Audit Log) │  │ Session)│   │ Archive) │
└────────┘      └────────────┘  └─────────┘   └──────────┘
```

### Deployment Strategy

**Blue-Green Deployments with Canary Testing**:

1. **Build**: CI/CD pipeline (GitHub Actions) builds Docker image on merge to `main`
2. **Test**: Run full test suite + load tests in staging (must pass 100%)
3. **Canary**: Deploy to 5% of production traffic
4. **Monitor**: Track error rates, latency, cost per request for 30 minutes
5. **Promote**: If canary healthy, gradually roll to 100% (10% increments)
6. **Rollback**: Instant rollback if error rate > 1% or latency p99 > 5s

**Versioning**:
- Semantic versioning: `v1.2.3`
- API versioned via URL: `/v1/agents/run`, `/v2/agents/run`
- Maintain N-1 compatibility (support last 2 major versions)
- Deprecation warnings 6 months before breaking changes

**Infrastructure as Code (Terraform)**:

```hcl
module "agent_runtime" {
  source = "./modules/agent-runtime"
  
  replicas = 10
  cpu_limit = "2000m"
  memory_limit = "4Gi"
  
  llm_provider = "openai"
  llm_model = "gpt-4-turbo"
  
  autoscaling_min = 5
  autoscaling_max = 50
  autoscaling_target_cpu = 70
}
```

**Zero-Downtime Deploys**:
- Rolling updates with `maxUnavailable: 0`
- Health checks: `/healthz` (liveness), `/ready` (readiness)
- Graceful shutdown: Drain connections over 30s before SIGTERM
- Circuit breakers: Stop sending traffic to unhealthy pods immediately

## Observability & Monitoring

<!-- What metrics would you track? What does your dashboard look like?
     How do you detect when an agent is misbehaving, hallucinating, or
     degrading in quality? What alerts would you set up? -->

### Metrics (Prometheus + Grafana)

**Golden Signals Dashboard**:

1. **Latency**:
   - `agent_runtime_duration_seconds{p50, p95, p99}` - End-to-end request time
   - `llm_call_duration_seconds{p50, p95, p99}` - LLM API latency
   - `tool_execution_duration_seconds{tool_name}` - Per-tool timing

2. **Traffic**:
   - `agent_requests_total{team, agent_type}` - Requests per team
   - `agent_tool_calls_total{tool_name}` - Tool usage patterns

3. **Errors**:
   - `agent_errors_total{error_type, team}` - Error count by type
   - `llm_errors_total{provider, model}` - LLM API failures
   - `tool_errors_total{tool_name}` - Tool execution failures

4. **Saturation**:
   - `agent_max_iterations_reached_total` - Agents hitting limits
   - `llm_rate_limit_hit_total` - Rate limiting incidents
   - `pod_cpu_usage_percent` - Resource utilization

**Agent Quality Metrics**:

5. **Correctness**:
   - `agent_hallucination_detected_total` - Hallucination detector triggers
   - `agent_tool_call_accuracy` - % of tool calls that succeed
   - `agent_task_completion_rate{scenario}` - % of tasks completed successfully

6. **Cost**:
   - `llm_tokens_used_total{model, team}` - Token consumption
   - `llm_cost_usd{model, team}` - Dollar cost by team
   - `cost_per_successful_request_usd` - Unit economics

**Trace Analysis (OpenTelemetry)**:

Every request generates a distributed trace:

```
Span: agent.run [5.2s]
  ├─ Span: llm.chat [1.1s]
  ├─ Span: tool.execute [2.3s]
  │   ├─ Span: db.query [0.8s]
  │   └─ Span: api.call [1.5s]
  ├─ Span: llm.chat [0.9s]
  └─ Span: trace.record [0.05s]
```

Store in Jaeger/Tempo for debugging slow requests.

### Detecting Misbehavior

**Hallucination Detection**:

```python
class HallucinationDetector:
    def check(self, response: str, tool_results: list) -> bool:
        # Extract facts from LLM response
        claimed_facts = self.extract_facts(response)
        
        # Verify against actual tool results
        for fact in claimed_facts:
            if not self.verify_fact(fact, tool_results):
                self.metrics.hallucination_detected.inc()
                self.alert("Hallucination detected", fact)
                return False
        return True
```

**Anomaly Detection**:
- Alert if tool call distribution changes >20% week-over-week
- Alert if error rate >1% sustained for 5 minutes
- Alert if p99 latency >2x baseline
- Alert if token usage >50% of monthly budget before month-end

**Alerts (PagerDuty)**:

| Severity | Condition | Response Time |
|----------|-----------|---------------|
| P0 (Critical) | Error rate >5% for 1 min | Immediate page |
| P1 (High) | Error rate >2% for 5 min | Page during business hours |
| P2 (Medium) | Cost anomaly detected | Slack notification |
| P3 (Low) | Slow trace detected | Email digest |

## Safety & Governance

<!-- How do you prevent agents from taking dangerous actions?
     How do you handle permissions, audit trails, and compliance?
     What guardrails exist beyond what the LLM prompt says? -->

### Multi-Layer Safety Model

**Layer 1: Prompt-Level Guardrails** (Fast, Imperfect)

System prompt includes safety instructions:
```
You are a finance agent. NEVER:
- Approve invoices >€50,000 without explicit confirmation
- Delete or modify existing data without user request
- Share sensitive customer information
```

**Layer 2: Pre-Execution Validation** (Fast, Rules-Based)

```python
class SafetyValidator:
    DANGEROUS_OPERATIONS = ["approve_invoice", "delete_invoice", "update_vendor"]
    
    def validate(self, tool_call: ToolCall, context: Context) -> ValidationResult:
        # Check 1: Tool whitelist per team
        if tool_call.name not in context.team.allowed_tools:
            return ValidationResult(blocked=True, reason="Tool not allowed for team")
        
        # Check 2: Amount thresholds
        if tool_call.name == "approve_invoice":
            amount = tool_call.args.get("amount", 0)
            if amount > context.user.approval_limit:
                return ValidationResult(blocked=True, reason="Amount exceeds approval limit")
        
        # Check 3: Bulk operation safeguards
        if self.is_bulk_operation(tool_call):
            if not context.user.confirmed_bulk:
                return ValidationResult(blocked=True, reason="Bulk operation requires confirmation")
        
        return ValidationResult(blocked=False)
```

**Layer 3: Post-Execution Audit** (Async, Complete)

Every action logged to immutable audit trail:

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL,
    team_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB NOT NULL,
    result JSONB,
    trace_id UUID NOT NULL,
    approved_by UUID,  -- For manual review
    CONSTRAINT audit_log_immutable CHECK (false)  -- Prevent updates/deletes
);
```

### Permissions & RBAC

**Role-Based Access Control**:

```yaml
roles:
  viewer:
    allowed_tools: ["list_invoices", "get_invoice_details"]
    approval_limit: 0
  
  accountant:
    allowed_tools: ["list_invoices", "get_invoice_details", "approve_invoice"]
    approval_limit: 10000  # €10k
  
  manager:
    allowed_tools: ["*"]
    approval_limit: 50000  # €50k
  
  admin:
    allowed_tools: ["*"]
    approval_limit: 999999999
    requires_mfa: true
```

**Tool-Level Permissions**:

Each tool declares required permission:

```json
{
  "name": "approve_invoice",
  "required_permission": "invoices:approve",
  "risk_level": "high",
  "requires_confirmation": true
}
```

### Compliance (GDPR, SOC 2)

1. **Data Residency**: EU customers' data stays in EU regions
2. **Encryption**: TLS 1.3 in transit, AES-256 at rest
3. **Retention**: Traces retained 90 days, audit logs 7 years
4. **Right to Deletion**: User requests trigger cascade delete
5. **Access Logs**: Who accessed what, when, why

## Cost Control & Scaling

<!-- How do you ensure AI costs scale predictably?
     What caching, routing, or rate-limiting strategies would you use?
     How do you handle usage across multiple product teams? -->

### Cost Attribution & Budgets

**Per-Team Quotas**:

```python
class CostController:
    def check_budget(self, team_id: str, estimated_cost: float) -> bool:
        usage = self.get_monthly_usage(team_id)
        budget = self.get_team_budget(team_id)
        
        if usage + estimated_cost > budget:
            self.alert_team(team_id, "Budget exceeded")
            return False  # Block request
        
        return True
```

**Budgets by Team**:
- Team A (Accounting): $5k/month
- Team B (Analytics): $2k/month  
- Team C (Customer Support): $3k/month

**Cost Optimization Strategies**:

1. **Prompt Caching** (50% cost reduction):
   - Cache tool schemas (same for all requests)
   - Cache system prompts (rarely change)
   - Use GPT-4's prompt caching API

2. **Model Routing** (60% cost reduction):
   ```python
   def route_request(request: Request) -> str:
       if request.complexity < 0.3:
           return "gpt-3.5-turbo"  # $0.001/1k tokens
       elif request.complexity < 0.7:
           return "gpt-4-turbo"    # $0.01/1k tokens
       else:
           return "gpt-4"          # $0.03/1k tokens
   ```

3. **Response Caching** (80% cost reduction for repeated queries):
   ```python
   cache_key = hash(query + tool_results + model_version)
   if cached := redis.get(cache_key):
       return cached
   ```

4. **Batch Processing**:
   - Non-urgent tasks go into queue
   - Process in batches during off-peak hours (cheaper API rates)

### Scaling Strategy

**Horizontal Auto-Scaling**:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-runtime
spec:
  minReplicas: 5
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: agent_queue_depth
      target:
        type: AverageValue
        averageValue: "10"
```

**Rate Limiting**:

```python
# Per-team rate limits
rate_limits = {
    "team_a": RateLimit(requests=1000, per="hour"),
    "team_b": RateLimit(requests=500, per="hour"),
}

# Token-based rate limiting (more fair)
token_rate_limits = {
    "team_a": RateLimit(tokens=1_000_000, per="day"),
}
```

**Cost Per Request Target**: <$0.50/request average

## Developer Experience

<!-- Product engineers at Light need to build agents on top of this runtime.
     What does their experience look like? How do they register tools,
     test their agents, and deploy with confidence? -->

### Tool Registration (Self-Service)

**Declarative Tool Definition**:

```python
from light_agent import tool, Parameter

@tool(
    name="send_email",
    description="Send an email to a user",
    category="communication",
    risk_level="medium"
)
def send_email(
    to: Parameter(str, description="Recipient email address"),
    subject: Parameter(str, description="Email subject line"),
    body: Parameter(str, description="Email body content"),
) -> dict:
    """Send email and return status."""
    # Implementation
    return {"status": "sent", "message_id": "abc123"}
```

**Automatic Tool Registration**:

```bash
# CLI to register new tool
light-agent tools register ./my_tools/send_email.py \
  --team accounting \
  --environment production

# Output
✓ Tool 'send_email' registered successfully
✓ Schema validated
✓ Deployed to production (version 1.0.0)
✓ Available at: https://api.light.ai/v1/tools/send_email
```

### Local Development

**CLI for Testing**:

```bash
# Start local agent with hot reload
light-agent dev --tools ./my_tools/ --watch

# Test agent interactively
light-agent run "Approve invoice INV-123"

# Run test scenarios
light-agent test --scenarios ./scenarios.json

# View trace
light-agent trace show <trace_id>
```

**Agent Testing Framework**:

```python
from light_agent.testing import AgentTestCase

class TestInvoiceAgent(AgentTestCase):
    agent = "invoice-agent-v2"
    
    def test_approves_valid_invoice(self):
        result = self.run("Approve invoice INV-001")
        
        self.assertSuccess(result)
        self.assertToolCalled("approve_invoice", args={"id": "INV-001"})
        self.assertInResponse("approved", result.answer)
        self.assertCost(result, max_usd=0.10)
```

### CI/CD Integration

```yaml
# .github/workflows/deploy-agent.yml
name: Deploy Agent
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: light-ai/agent-test-action@v1
        with:
          scenarios: ./scenarios.json
          coverage-threshold: 90
          max-cost-per-run: 0.50
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: light-ai/agent-deploy-action@v1
        with:
          agent-id: invoice-agent
          version: ${{ github.sha }}
          environment: production
          rollout-strategy: canary
```

### Documentation & Discovery

**Developer Portal** (`https://developers.light.ai`):

- Interactive API docs (Swagger/OpenAPI)
- Agent playground (test in browser)
- Tool catalog (browse available tools)
- Example agents (copy-paste starter templates)
- Pricing calculator (estimate costs before deploying)

**Slack Integration**:

```
/light-agent test "Show me unpaid invoices over €5k"

🤖 Agent Response (1.2s, $0.03):
Found 3 invoices:
- INV-001: €15,000 (Acme Corp)
- INV-003: €8,750 (Globex)
- INV-004: €12,500 (Wayne Enterprises)

📊 View trace: https://app.light.ai/traces/abc123
```

This empowers product teams to build and iterate on agents independently while maintaining safety, cost control, and observability.
