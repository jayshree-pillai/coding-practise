# Context Management Coding Exercise

Implement `build_context()` so that it constructs an LLM context safely within a token budget.

## Requirements

1. The system message must always be included.
2. The current user question must always be included.
3. History should contain only complete user/assistant turns.
4. Prefer the most recent conversation history.
5. The final messages must remain in chronological order.
6. Never exceed the token budget unless the mandatory system message and current question alone exceed it.
7. Assume one word equals one token.