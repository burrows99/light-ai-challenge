"""
Light Agent Runtime — Entry Point

This is the starting point for your implementation. Your task is to build
the agent runtime that orchestrates the loop between a user request, the
LLM, and the available tools.

You are free to:
  - Refactor this file completely
  - Create new modules, classes, and abstractions
  - Change function signatures
  - Add configuration, middleware, etc.

The only hard requirement: running the test scenarios should produce
a structured execution trace showing what happened.
"""

from light_agent.mock_tools import MockToolExecutor
from light_agent.mock_llm import MockLLMClient
from light_agent.types import Message, ExecutionTrace


def run_agent(user_request: str) -> ExecutionTrace:
    """
    Run the agent for a given user request.

    This function should:
      1. Accept a natural-language user request
      2. Use an LLM to decide which tools to call (and with what arguments)
      3. Execute those tools and feed results back to the LLM
      4. Repeat until the LLM produces a final answer
      5. Return a structured ExecutionTrace of everything that happened

    Things to think about as you build this:
      - What's the maximum number of LLM ↔ tool iterations?
      - What happens when a tool call fails?
      - How would you swap the LLM provider (mock → OpenAI → Anthropic)?
      - How would you add per-tool timeouts or retry policies?
      - What information should the execution trace capture for observability?
      - How would you handle a tool that's marked as "mutating"?
    """
    # Provided for convenience — use, extend, or replace as you see fit
    tools = MockToolExecutor()
    llm = MockLLMClient()

    # ----------------------------------------------------------------
    # TODO: Build your agent loop here.
    #
    # A minimal loop looks something like:
    #
    #   1. Create the conversation with the user message
    #   2. Send conversation + tool definitions to the LLM
    #   3. If the LLM returns tool_calls:
    #        a. Execute each tool call
    #        b. Append the results to the conversation
    #        c. Go to step 2
    #   4. If the LLM returns content (no tool_calls):
    #        → That's the final response. Return it.
    #
    # But a *good* runtime handles much more than the happy path...
    # ----------------------------------------------------------------

    raise NotImplementedError("Your agent runtime goes here!")


# Quick manual test
if __name__ == "__main__":
    scenarios = [
        "Show me all unpaid invoices over €5,000",
        "Find the largest pending invoice from Acme Corp and approve it",
        "Approve invoice INV-9999",
    ]

    for request in scenarios:
        print(f"\n{'='*60}")
        print(f"REQUEST: {request}")
        print(f"{'='*60}")
        try:
            trace = run_agent(request)
            print(f"RESPONSE: {trace.final_response}")
            print(f"TOOL CALLS: {trace.tool_calls_made}")
            print(f"DURATION: {trace.total_duration_ms:.0f}ms")
        except NotImplementedError:
            print("⚠  Not yet implemented")
        except Exception as e:
            print(f"ERROR: {e}")
