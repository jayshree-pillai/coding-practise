# GenAI Interview Preparation — Running Answers

## Section 1: RAG and information retrieval

### 1.1. What is RAG, and how is it different from fine-tuning?



### 1.2. What are embeddings, and how do they capture semantic similarity?



### 1.3. What is chunking, and why do chunk size and overlap matter?



### 1.4. What is parent–child chunking, and why would you use it?



### 1.5. What is the difference between keyword search and vector search?

**Keyword search matches terms; vector search finds similarity in learned representations of meaning.**

| Aspect | Keyword search | Vector search |
|---|---|---|
| **How it works** | Uses an inverted index and scoring such as BM25 | Compares query and document embeddings using a similarity measure |
| **Strengths** | Specific terminology, names, identifiers and phrases | Paraphrases and conceptually related wording |
| **Limitations** | Can miss relevant content expressed differently | Can confuse similar topics or miss important numbers, negation and identifiers |

**Example:** Searching “car repair” can retrieve “automobile maintenance” through vector similarity even without shared words.

**Key nuance:** Keyword search can also support stemming and configured synonyms. For identifiers that must match exactly, use an exact-match field or query.


### 1.6. What is hybrid search, and how does it combine keyword and vector results?

**Hybrid search combines keyword and vector retrieval to capture both specific terms and semantic matches.**

A typical flow:

1. Run BM25 and vector search for the same query, usually in parallel.
2. Merge candidates by document or chunk ID and combine their rankings.
3. Return the top K results, optionally passing them through a reranker first.

| Combination method | How it works |
|---|---|
| **Reciprocal Rank Fusion (RRF)** | Combines each candidate’s rank positions across result lists, without comparing raw scores |
| **Weighted score fusion** | Normalizes scores to a comparable scale, then combines them using configurable weights |

**Example:** For “NVIDIA revenue growth,” keyword search captures the company and financial terms, while vector search can find passages discussing “sales increased.”

**Key nuance:** BM25 and vector scores have different scales; directly adding their raw scores can produce misleading rankings.


### 1.7. What is reranking, and how is it different from the initial retrieval step?

**Reranking rescoring and reorders retrieved candidates to put the most relevant results first.**

| Stage | What it does | Priority |
|---|---|---|
| **Initial retrieval** | Searches a large index using BM25, vector search or hybrid search to collect candidate chunks | Speed and high recall |
| **Reranking** | Applies a more detailed relevance model to those candidates, often a cross-encoder that reads the query and chunk together | Better relevance and ordering |

**Example:** Retrieve 100 candidate chunks, rerank them, then send the best 5 to the LLM.

**Why two stages?** Detailed scoring across millions of chunks would be expensive. Applying it to a small candidate set makes it practical, though it adds latency.

**Key nuance:** A reranker cannot recover evidence that initial retrieval missed. Candidate recall sets the ceiling on what reranking can achieve.

### 1.8. What is cosine similarity, and how does it differ from dot product and Euclidean distance?


### 1.9. What is approximate nearest-neighbor (ANN) search, and why is it used in vector retrieval?

**ANN finds vectors close to a query efficiently, while allowing some true nearest neighbors to be missed.**

| Approach | How it works |
|---|---|
| **Exact brute-force search** | Compares the query with every stored vector and returns the exact top K under the chosen similarity metric |
| **ANN search** | Uses structures such as HNSW graphs or IVF clusters to explore promising candidates and reduce search work |

**Why use it?** Comparing millions of high-dimensional embeddings for every query can be expensive. ANN makes large-scale vector retrieval practical at lower latency.

**Tradeoff:** Search speed versus nearest-neighbor recall, with memory and indexing costs depending on the index.

**Tuning example:** Increasing HNSW’s `efSearch` explores more candidates, usually improving recall while increasing latency.

**Key nuance:** ANN recall measures agreement with exact nearest neighbors. Whether those neighbors answer the question requires separate relevance evaluation.


### 1.10. What do Recall@K, hit rate, Reciprocal Rank (RR), Mean Reciprocal Rank (MRR) and nDCG measure, and how do they differ?

**K** means the top K retrieved results.

| Metric | What it measures |
|---|---|
| **Recall@K** | **Coverage:** relevant items retrieved in the top K divided by all known relevant items for that query. |
| **Hit rate@K** | **Success rate:** fraction of queries with at least one relevant item in the top K. One relevant result is enough to count as a hit. |
| **RR** | **How early the first relevant result appears:** `1 / rank`. Rank 1 → `1`; rank 4 → `0.25`; no relevant result → `0`. |
| **MRR** | **Mean RR across all evaluated queries**, including zeros for misses. |
| **nDCG@K** | **Overall ranking quality:** rewards highly relevant results appearing earlier. Supports graded relevance. Calculated as `DCG@K / ideal DCG@K`, where the ideal is the best possible ranking. |

**Example:** Four items are relevant; two appear in the top five, first at rank 2. Recall@5 = `0.5`, the query is a hit, and RR = `0.5`.

**Key nuance:** Recall and hit rate ignore ordering within K. RR/MRR consider only the first relevant result; nDCG considers relevance and positions throughout the top K. For RR@K, a relevant result beyond K earns zero.


### 1.11. Write a pseducode to highlight BM25 implementation?

### 1.12. What are the most efficient rerankers that works with latest LLM

## Section 2: Agent orchestration with LangGraph

### 2.1. What is an AI agent, and how is it different from a predefined workflow?
An LLM-based agent uses the model to decide its next action—such as choosing a tool, inspecting the result and deciding whether more information is needed—to accomplish a goal within defined limits.

A predefined workflow follows steps and routing rules written by the developer. It can include LLM calls, branches and parallel execution, but the developer determines the available paths.

### 2.2. What is the model → tool call → tool result loop, and which responsibilities belong to the LLM versus the runtime?
The **LLM** decides whether to answer or request a tool, returning the tool’s name and arguments. After receiving the result, it decides whether more information or another action is needed.

The **runtime** validates the request, checks permissions, executes the tool and calls the model again with the result. It manages errors and execution limits, repeating the loop until the model finishes or a limit is reached.

### 2.3. What are nodes, edges and conditional edges in a LangGraph workflow?
**Nodes** are units of work, usually functions that read graph state and return updates—for example, calling an LLM or executing a tool. 

**Edges** connect nodes and determine execution order; a normal edge defines a fixed route to the next node.

**Conditional edges** use a routing function to choose the next node or nodes based on the current state—for example, routing to a tool node when the model requests a tool, or ending when it produces a final answer.

### 2.4. What is graph state, and how do nodes read and update it?
**Graph state** is the shared, structured data carried through a workflow—such as messages, retrieved evidence, intermediate results and status. Its schema defines the fields the workflow uses.

Each **node** receives the current state and returns updates only to the fields it changes. 

A **reducer** is a function attached to a field that determines how its existing value combines with an incoming update. Without a custom reducer, an update replaces the existing value.
Reducers are defined in the state schema using `Annotated`:
```python
from typing import Annotated, TypedDict
from operator import add

class State(TypedDict):
    results: Annotated[list[str], add]
    status: str
```
Here, `add` concatenates lists. If `results` contains `["A"]` and a node returns `{"results": ["B"]}`, LangGraph stores `["A", "B"]`. The `status` field uses default replacement. Fields omitted from a node’s update remain unchanged by that update.

### 2.5. What is a reducer, and why is it important when parallel nodes update state?
A **reducer** defines how a state field’s existing value combines with updates—for example, appending results to a list or adding values to a counter.

When **parallel nodes update the same field in the same execution step**, the reducer tells LangGraph how to combine their outputs. Without a reducer that supports those updates, LangGraph raises a concurrent-update error. For example, two workers can each return a list of findings, and an append reducer collects both lists.

**Example 1 — Add token counts (integer reducer)**
```python
from typing import Annotated, TypedDict
from operator import add
class UsageState(TypedDict):
    total_tokens: Annotated[int, add]
```
If the current total is `100`, and two workers return `{"total_tokens": 30}` and `{"total_tokens": 20}`, the merged total becomes `150`. Each worker returns its own increment, not the running total.

**Clarification — where is the total stored?**
`UsageState` defines the schema; the actual state passed to a worker is a Python dictionary. The LangGraph runtime manages the accumulated state for the graph execution. A worker’s input state and its returned update are different things:

| Worker | Total it reads | New tokens used | Update it returns |
|---|---:|---:|---|
| A | 100 | 30 | `{"total_tokens": 30}` |
| B | 100 | 20 | `{"total_tokens": 20}` |
The workers return their contributions without directly changing the input dictionary. LangGraph applies the addition reducer: **100 + 30 + 20 = 150**.
**The graph’s resulting state for this run contains `total_tokens = 150`.** This is a value in the state managed by the runtime, not a `graph.total_tokens` attribute on the compiled graph object.
For a graph configured with this schema and these two workers, each running once:
```python
final_state = graph.invoke({"total_tokens": 100})
print(final_state["total_tokens"])  # 150
```
**Example 2 — Collect unique source IDs (set reducer)**
```python
from typing import Annotated, TypedDict
def merge_sources(current: set[str], incoming: set[str]) -> set[str]:
    return current | incoming
class SourceState(TypedDict):
    source_ids: Annotated[set[str], merge_sources]
```

Starting with an empty set, if two workers return `{"source_ids": {"doc1", "doc2"}}` and `{"source_ids": {"doc2", "doc3"}}`, the merged set contains `{"doc1", "doc2", "doc3"}`. Set union removes duplicates; set order is not meaningful.

In both examples, workers return partial state updates and LangGraph invokes the declared reducer to combine them.

**A reducer is a function—built-in or custom**

`operator.add` is already a Python function. `merge_sources` is a custom function we defined ourselves. Both act as reducers because they are attached to state fields using `Annotated`.A reducer receives two inputs: the field’s existing value and one incoming update. It returns the combined value for that field. It does not receive the entire state dictionary or all workers’ outputs at once; LangGraph applies it as updates are merged.

For example, the token reducer could be written explicitly instead of importing `add`:

```python
def add_tokens(current: int, incoming: int) -> int:
    return current + incoming

class UsageState(TypedDict):
    total_tokens: Annotated[int, add_tokens]
```

This uses the `Annotated` and `TypedDict` imports shown above. Conceptually, combining the updates gives `add_tokens(100, 30) = 130`, followed by `add_tokens(130, 20) = 150`. The `130` is an intermediate value in the runtime’s reduction, not a total returned by either worker. Addition also gives the same final total if the updates are combined in the opposite order.

The workers still return only `{"total_tokens": 30}` and `{"total_tokens": 20}`. **LangGraph calls `add_tokens` automatically** when applying those updates. A custom reducer similarly lets you define other combining rules, such as the set union used by `merge_sources`.

### 2.6. What is the orchestrator–worker pattern, and how does it use fan-out and fan-in?
The **orchestrator–worker pattern** uses a coordinating component to break a goal into subtasks, delegate them to workers and combine their results. The subtasks can be determined dynamically based on the request.

**Fan-out** dispatches independent subtasks to workers, often in parallel. **Fan-in** waits for the required worker results and combines them into a final output—for example, merging financial, industry and risk sections into one credit report.

### 2.7. What is checkpointing, and how does it support recovery and pause/resume?
**Checkpointing** saves snapshots of a graph’s state and execution progress through a configured checkpointer. Checkpoints are grouped under a `thread_id`; durable storage such as PostgreSQL lets them survive process restarts.

For **recovery**, LangGraph restores saved progress so the entire workflow need not restart. For **pause/resume**, an interrupt pauses execution, and a resume command with the same `thread_id` supplies the input needed to continue. The interrupted node restarts from its beginning, so code before the interrupt can run again.

**Example — interrupt and resume**
```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
class ReviewState(TypedDict):
    approved: bool | None
def review(state: ReviewState):
    decision = interrupt("Approve this report?")
    return {"approved": decision}

builder = StateGraph(ReviewState)
builder.add_node("review", review)
builder.add_edge(START, "review")
builder.add_edge("review", END)
graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "report-123"}}
# Start: pauses at interrupt() and returns the review question.
paused = graph.invoke({"approved": None}, config)
print(paused["__interrupt__"][0].value)  # Approve this report?
# Later: the application supplies the human's approval.
resumed = graph.invoke(Command(resume=True), config)
print(resumed["approved"])  # True
```

The first call pauses at `interrupt()` and returns the question to the caller. The application presents it to the human. After approval, the second call uses the same `thread_id` and supplies `True`; that value becomes the result of `interrupt()`, so the node returns `{"approved": True}`.

**Pass a dictionary as the resume value, then explicitly return updates for each state field.**
```python
class ReviewState(TypedDict):
    approved: bool | None
    reviewer_comment: str | None
def review(state: ReviewState):
    response = interrupt("Approve this report and add a comment?")

    return {
        "approved": response["approved"],
        "reviewer_comment": response["reviewer_comment"],
    }
```
Start the graph:
```python
paused = graph.invoke(
    {"approved": None, "reviewer_comment": None},
    config,
)
```
Later, supply both answers:
```python
resumed = graph.invoke(
    Command(resume={
        "approved": True,
        "reviewer_comment": "Looks good.",
    }),
    config,
)
```

Inside `review()`, **`response` receives that entire dictionary**. The node’s `return` updates both fields.

The resulting state is:

```python
{
    "approved": True,
    "reviewer_comment": "Looks good.",
}
```

**One interrupt can collect multiple values.** Fields omitted from the node’s returned dictionary keep their existing values.
`InMemorySaver` keeps checkpoints only while this process is alive. Use a durable checkpointer, such as one backed by PostgreSQL, to resume after process restarts. On resume, the interrupted node starts again from its beginning; code before `interrupt()` can execute again.

### 2.8. What is the difference between short-term and long-term memory in an agent system?
**Short-term memory** is the context maintained within one conversation or execution thread, such as messages and intermediate results. In LangGraph, it lives in graph state and can be persisted using a checkpointer.

**Long-term memory** is information reused across conversations or threads, such as user preferences, facts and prior learnings. It is typically stored separately and retrieved when relevant. **Short-term refers to scope, not storage:** it can survive application restarts if persisted durably.

### 2.9. What is a bounded agent, and how do you prevent endless tool calls or execution loops?
A **bounded agent** can choose its next actions within developer-defined limits on its task, permitted tools and resource usage.

To prevent endless loops, the **runtime enforces** maximum steps or tool calls, timeouts, retry limits and token or cost budgets. It checks for completion or repeated actions without progress, then stops or requests human help. In LangGraph, `recursion_limit` caps graph execution steps; reaching it raises `GraphRecursionError`, so define a graceful exit before that limit.

### 2.10. What is human-in-the-loop execution, and how do interrupts support human review?
**Human-in-the-loop execution** pauses a workflow so a person can approve, reject or edit a proposed action or result before execution continues.
In LangGraph, `interrupt(payload)` exposes the review request and pauses execution with state saved through a checkpointer. The application collects the human’s decision and resumes the same `thread_id` using `Command(resume=decision)`. That decision becomes the return value of `interrupt()`, and your code determines what happens next. The interrupted node restarts from its beginning, so place actions requiring approval after the interrupt.

See the interrupt/resume code example under Q2.7.

## Section 3A: Python fundamentals

### 3A.1. What are the differences between a list, tuple, set and dictionary, and when would you use each?
| Type | Main properties | When to use it |
|---|---|---|
| **List** | Ordered, mutable sequence; allows duplicates. | A collection that changes, such as retrieved chunks. |
| **Tuple** | Ordered, immutable sequence; allows duplicates. | A fixed grouping, such as `(document_id, score)`. |
| **Set** | Mutable collection of unique, hashable elements; no guaranteed iteration order. | Deduplication and membership checks, such as seen document IDs. |
| **Dictionary** | Mutable mapping of unique, hashable keys to values; preserves insertion order. | Looking up information by key, such as document metadata. |

**Hashable** means an object has a stable hash and compatible equality behavior, allowing it to serve as a dictionary key or set element. A tuple is hashable only if all its elements are hashable.

### 3A.2. What does mutable versus immutable mean, and why are mutable default arguments risky?
A **mutable** object can change in place, such as a list or dictionary. An **immutable** object cannot, such as an integer, string or tuple; assigning a different value rebinds the variable. A tuple can still contain a mutable object whose contents change.

**Example — a tuple containing a list**

```python
items = ([1, 2, 3], "hello")

items[0].append(4)  # Allowed: modify the existing list.
print(items)       # ([1, 2, 3, 4], 'hello')
```

Replacing the list stored in the tuple is not allowed:

```python
items[0] = [4, 5]  # TypeError: tuples do not support item assignment.
```

The tuple still holds the **same list object** in its first position. Appending changes that list's contents; assigning to `items[0]` would change which object the tuple holds. **The tuple itself remains immutable even when an object inside it changes.** You also cannot add or remove positions from the existing tuple.

**Mutable default arguments**

Default argument values are evaluated **once when the function is defined**. With `items=[]`, calls that omit `items` reuse the same list, so changes can leak between calls. Use `None` and create a fresh list inside:

```python
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

Each call that omits `items` gets a new list; an explicitly supplied list is still modified.

Sources: [Python glossary](https://docs.python.org/3/glossary.html#term-mutable) and [default argument values](https://docs.python.org/3/tutorial/controlflow.html#default-argument-values).

### 3A.3. What is the difference between assignment, a shallow copy and a deep copy?
**Assignment** creates another reference to the same object. A **shallow copy** creates a new outer container but keeps references to its nested objects. A **deep copy** recursively copies nested objects, so ordinary nested mutable containers can be changed independently.

```python
from copy import deepcopy

original = {"scores": [90]}
alias = original
shallow = original.copy()
deep = deepcopy(original)

original["scores"].append(95)
# original, alias and shallow: {"scores": [90, 95]}
# deep:                       {"scores": [90]}
```

Adding a new top-level key to `original` would affect `alias`, but neither copy. Deep copying costs more time and memory; use it when you need independent nested data.

### 3A.4. What is a decorator, and how does it wrap or extend a function’s behavior?
A **decorator** is a callable that receives a function and returns the object that replaces it—commonly a wrapper adding logging, timing, retries or authorization without changing the original function’s body.

Writing `@logged` above `def process(...)` is equivalent to `process = logged(process)` after defining the function. The decorator is applied when the definition executes; the wrapper runs when the decorated function is called. A typical wrapper forwards `*args, **kwargs`, calls the original function and returns its result. Use `functools.wraps` to preserve metadata such as its name and docstring.

### 3A.5. What is the difference between an iterable, an iterator and a generator, and what does `yield` do?
An **iterable** can provide an iterator through `iter()`, such as a list. An **iterator** tracks traversal state and returns successive values through `next()`, raising `StopIteration` when exhausted. Every iterator is iterable, but an iterable such as a list is not itself an iterator.

A **generator** is an iterator created by a generator function or expression. In a generator function, `yield` produces a value and pauses execution, preserving local variables and the current position until the next request. This supports lazy processing without building the entire output list upfront. An exhausted generator must be recreated to iterate again.
### 3A.6. How do `try`, `except`, `else` and `finally` work in exception handling?
- **`try`** contains the operation that might raise an exception.
- **`except`** handles a matching exception; execution skips the remaining statements in `try`.
- **`else`** runs if `try` completes normally, without an exception or an early exit such as `return`.
- **`finally`** runs when leaving the construct, whether through success, an exception or a return, and is used for cleanup.

Catch specific exceptions you can handle. An unmatched exception propagates after `finally`; exceptions raised in `else` are not caught by the preceding `except` clauses. Avoid returning from `finally`, because that can override an earlier return or suppress an exception.

### 3A.7. What is a context manager, and how does the `with` statement manage resources?
A **context manager** defines setup and cleanup around a block of code. The `with` statement calls `__enter__()` on entry and, if entry succeeds, calls `__exit__()` when the block exits—even if it raises an exception.

For example, `with open("report.txt") as file:` closes the file when the block ends. Context managers also manage locks and transactions. Exceptions normally propagate after cleanup, but a context manager can deliberately suppress one by returning a truthy value from `__exit__()`.

### 3A.8. What is the difference between an instance method, a class method and a static method?
| Method | Receives automatically | Typical use |
|---|---|---|
| **Instance method** | `self`: the instance. | Read or change that object’s state. |
| **Class method** — `@classmethod` | `cls`: the class used to call it. | Alternative constructors or class-level behavior. |
| **Static method** — `@staticmethod` | Neither instance nor class. | A related utility that only needs its explicit arguments. |

For example, `report.render()` uses an instance’s data, `Report.from_dict(data)` can construct an object using `cls(...)`, and `Report.is_valid_id(value)` can be a static utility. Using `cls` also lets an inherited class method construct the calling subclass.

### 3A.9. What are coroutines, `async` and `await`, and how does the event loop execute them?
A **coroutine** is a computation that can suspend and resume. Calling a coroutine function defined with `async def` returns a coroutine object; its body runs when awaited or scheduled as a task. **`await`** waits for an awaitable’s result and can suspend the current coroutine.

An **asyncio event loop** runs one task at a time in its thread. When an awaited operation suspends, the loop can run other ready tasks and later resume the waiting one. Use `create_task()` or `gather()` to run independent operations concurrently; sequential awaits remain sequential. Blocking calls such as `time.sleep()` still block the loop inside `async def`; use async libraries or offload blocking work.
### 3A.10. How do threading, multiprocessing and asyncio differ, and where does the GIL matter?
| Approach | How it runs | Typical use |
|---|---|---|
| **Threading** | Multiple OS threads in one process, sharing memory. | Concurrent blocking I/O, such as calls through a synchronous SDK. |
| **Multiprocessing** | Separate processes with separate memory; communication adds overhead. | CPU-heavy Python work that should use multiple cores. |
| **Asyncio** | Tasks cooperate on an event loop, usually within one thread. | Many concurrent I/O operations using async libraries. |

In **GIL-enabled CPython**, the Global Interpreter Lock allows only one thread per interpreter to execute Python bytecode at a time, limiting CPU parallelism from threads. I/O and some native libraries release the GIL; optional free-threaded builds can run without it. **The GIL does not make application logic thread-safe**—shared mutable state can still require locks.

## Section 3B: FastAPI and REST APIs

### 3B.1. What is a REST API, and what does “stateless” mean?
A **REST API** follows **Representational State Transfer**, an architectural style that exposes resources through a uniform interface. In an HTTP API, resources have URLs such as `/reports/123`; clients use methods such as `GET` and `POST` and exchange representations of those resources, often as JSON.

**Stateless** means each request carries the context needed to understand it, including the target resource, relevant parameters and required credentials. The server does not rely on remembered client session context from earlier requests. It can still store resources in a database; statelessness concerns how requests are handled.

**REST, RPC and FastAPI — how they relate**

| Term | What it describes | Example |
|---|---|---|
| **REST** | An architectural style centered on resources and a uniform interface. | `GET /users/123` retrieves a representation of a user. |
| **RPC — Remote Procedure Call** | A model centered on invoking a remote operation with arguments and receiving its result. | Calling `calculate_total(items)` on a server. |
| **FastAPI** | A Python framework used to implement API endpoints. | It can implement REST-style routes, RPC-style routes or both. |

**Restaurant analogy:** REST presents resources such as menus and reservations: “Get the menu” or “Create a reservation.” RPC exposes operations: “Reserve table 5” or “Calculate my bill.” FastAPI is like the kitchen and staff—the implementation that receives requests and produces responses.

**Both styles implemented with FastAPI**

```python
from fastapi import FastAPI

app = FastAPI()

# REST-style: retrieve a user resource.
@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}  # Minimal demonstration response.

# RPC-style: invoke a calculation.
@app.post("/calculate-total")
def calculate_total(items: list[int]):
    return {"total": sum(items)}
```

`GET /users/123` returns `{"id": 123}`. Sending the JSON body `[10, 20, 12]` to `POST /calculate-total` returns `{"total": 42}`.

**REST and RPC describe the API’s interaction style; FastAPI is a tool for implementing it.** The second endpoint illustrates an RPC-style operation over HTTP; it does not implement the specific JSON-RPC message format. These small examples illustrate route design; using a resource URL alone does not establish compliance with all REST constraints.

### 3B.2. What are GET, POST, PUT, PATCH and DELETE, and which are idempotent?
**Idempotent** means repeating an identical request has the same intended effect on the server as making it once. The response or status code can still differ.

| Method | Purpose | Idempotent? |
|---|---|---|
| **GET** | Retrieve a resource’s representation. | Yes. |
| **POST** | Submit data for processing, often to create a new resource. | Not guaranteed. |
| **PUT** | Create or replace the resource’s state at a specified URL. | Yes. |
| **PATCH** | Apply partial changes to a resource. | Not guaranteed; depends on the changes. |
| **DELETE** | Remove the resource at the specified URL. | Yes. |

For example, a PATCH that **sets a status to “approved”** can be idempotent; one that **increments a counter** is not. Repeating DELETE can return `204` first and `404` later while remaining idempotent—the resource stays absent.

### 3B.3. What do the main HTTP status codes mean, particularly 200, 201, 202, 401, 403, 422 and 500?
| Code | Name |
|---|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted |
| 204 | No Content |
| 304 | Not Modified |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Unprocessable Content |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### 3B.4. What are FastAPI, ASGI and Uvicorn, and how do they work together?

- **FastAPI** is the Python web framework where you define API routes, input validation, dependencies and application logic.
- **ASGI — Asynchronous Server Gateway Interface** is the standard communication interface between a Python web server and an application, supporting asynchronous handling of HTTP and WebSocket connections.
- **Uvicorn** Uvicorn receives the HTTP request.

Intuitvely : 
- ASGI defines the agreed format and rules for how:
- Uvicorn (waiter) passes requests to FastAPI (kitchen).
- FastAPI (kitchen) passes responses back to Uvicorn (waiter).

### 3B.5. What is the difference between path parameters, query parameters and a request body?

| Input | Where it goes and what it does | Example |
|---|---|---|
| **Path parameter** | Part of the URL path; typically identifies a specific resource. | `/reports/123` — `123` is the report ID. |
| **Query parameter** | After `?` in the URL; commonly used for filtering, sorting or pagination. | `/reports?status=approved&limit=10` |
| **Request body** | Data sent separately from the URL, commonly as JSON; often used when creating or updating resources. | `{"title": "Credit Report", "company": "NVIDIA"}` |

In **FastAPI**, parameter names matching route placeholders such as `{report_id}` are path parameters. Other scalar parameters default to query parameters, and Pydantic model parameters default to the request body. **Query parameters can be required or optional**, depending on their declaration.

### 3B.6. How does FastAPI use Pydantic for request validation, response models and serialization?

FastAPI uses Pydantic models as **typed API contracts**:

- **Request validation:** Checks required fields, types and constraints, then gives the endpoint a validated Python object. Invalid input normally returns **422**.
- **Response models:** `response_model` validates returned data and filters it to the declared public fields. Invalid output normally causes **500**, because the service broke its contract.
- **Serialization:** Converts supported Python values, such as `datetime` and `UUID`, into JSON representations.

The models also generate schemas for **OpenAPI documentation**. Pydantic can coerce values such as `"5"` into `5`; strict validation prevents that conversion.

In agentic systems, **valid structure does not guarantee factual accuracy or authorized tool use**—those require separate checks.


### 3B.7. What is the difference between `def` and `async def` endpoints in FastAPI, and what happens if you put blocking code inside an async endpoint?

Yes—**a FastAPI endpoint is a Python function registered to handle requests for a specific HTTP method and URL path.**

```python
@app.get("/reports/{report_id}")
def get_report(report_id: int):
    return {"report_id": report_id}
```

When a client sends **`GET /reports/123`**, FastAPI validates the parameter, calls `get_report(report_id=123)` and turns its return value into an HTTP response.

**The decorator registers the route; the function handles the request.**

- **`def` endpoints:** FastAPI runs them in a **thread pool**, making them suitable for blocking I/O through synchronous libraries.
- **`async def` endpoints:** Run on the **event loop**. Awaiting nonblocking I/O lets other tasks run while the endpoint waits—for example, during an async LLM or database call.
- **Blocking code inside `async def`:** Calls such as `time.sleep()`, `requests.get()` or a synchronous LLM SDK block that event loop, delaying other requests handled by it.

Use **async clients**, or explicitly offload blocking I/O to a thread pool. Move substantial CPU-heavy work to processes or separate workers.

**Key nuance:** A regular `def` helper called directly inside an async endpoint is **not automatically offloaded**. Declaring the endpoint async does not make its contents nonblocking.

**Calling a helper normally means it runs on the same thread as the function calling it.**

```python
import time

def slow_helper():
    time.sleep(5)  # Blocks the calling thread.

@app.get("/test")
async def test():
    slow_helper()  # Runs here, on the event-loop thread.
    return {"done": True}
```

During those five seconds, **that event loop cannot run other requests**.

The distinction is **who calls the function**:

- **FastAPI calls a `def` endpoint:** FastAPI puts it in a thread pool automatically.
- **Your async endpoint calls a `def` helper:** It is an ordinary Python call. You must explicitly offload it to a thread pool if it blocks.
**Offload means: run the blocking helper on a worker thread, leaving the event-loop thread free.**

Using our previous `slow_helper`, change the endpoint to:

```python
import asyncio
@app.get("/test")
async def test():
    await asyncio.to_thread(slow_helper)
    return {"done": True}
```

Here is what happens:

1. **`to_thread`** sends `slow_helper` to a thread pool. Its five-second sleep blocks that worker thread.
2. **`await`** pauses this endpoint until the helper finishes, while allowing the event loop to handle other requests.
3. When the helper finishes, the endpoint resumes and returns its response.
**This request still waits five seconds; other requests can continue.**
Pass `slow_helper` **without parentheses**—you are handing Python the function to run elsewhere.

### 3B.8. What is dependency injection, and how does FastAPI’s `Depends` work?

**Dependency injection** means an endpoint receives the resources it needs—such as an authenticated user, database session or retrieval client—instead of creating them itself.

**`Depends(provider)`** tells FastAPI to:

- Resolve the provider’s inputs and any dependencies it needs.
- Run the provider before calling the endpoint.
- Pass its returned value into the endpoint parameter.

For an existing authentication function called `get_current_user`:

```python
from typing import Annotated
from fastapi import Depends

@app.get("/reports")
async def get_reports(
    user: Annotated[dict, Depends(get_current_user)],
):
    return {"user_id": user["id"]}
```

FastAPI calls `get_current_user` and supplies its result as `user`. An authentication exception can stop the request before the endpoint runs.

**Why it matters:** Dependencies centralize reusable logic and can be replaced in tests through `app.dependency_overrides`. Shared dependency results are normally cached **within one request**, not across requests.

Read this line as:

**“The parameter `user` is a dictionary, and FastAPI gets its value by calling `get_current_user`.”**

```python
user: Annotated[dict, Depends(get_current_user)]
```

- **`user`** — the endpoint’s parameter name.
- **`dict`** — its type.
- **`Depends(get_current_user)`** — tells FastAPI which function supplies the value.
- **`Annotated`** — combines the type with that extra instruction.

For example, if `get_current_user` returns:

```python
{"id": "u123", "name": "Jay"}
```

then inside the endpoint, **`user` contains that dictionary**, and `user["id"]` is `"u123"`.

The simpler equivalent syntax is:

```python
user: dict = Depends(get_current_user)
```

Yes—**`typing.Annotated` attaches extra information, called metadata, to a type.**

In `Annotated[dict, Depends(get_current_user)]`:

- **`dict`** tells type checkers the expected type.
- **`Depends(get_current_user)`** provides metadata that FastAPI interprets as “get this value from that function.”

**`Annotated` carries the information; FastAPI reads it and performs the dependency injection.** `Annotated` itself does not call the function.

### 3B.9. What is middleware, and how is it different from a dependency or an exception handler?
**Middleware** wraps the application’s request/response processing. It can inspect a request before routing, modify the response afterward or return a response early.

| Mechanism | Main responsibility | Examples |
|---|---|---|
| **Middleware** | Apply general request/response behavior across the configured application. | Logging, timing, trace IDs, CORS. |
| **Dependency — `Depends`** | Supply values or enforce checks wherever declared. | Authenticated user, database session, document-access checks. |
| **Exception handler** | Convert a matching raised exception into an HTTP response. | Map `DocumentNotFound` to 404 or customize validation errors. |

For a research API: **middleware records the trace ID**, a **dependency checks document access**, and an **exception handler formats failures consistently**.

**Key distinction:** Dependencies participate in endpoint execution; middleware wraps the request/response flow; exception handlers respond to failures.

### 3B.10. What is the difference between authentication and authorization, and where do OAuth 2.0 and JWT fit?

- **Authentication:** Verifies **who the caller is**—a user or service. Missing or invalid credentials normally result in **401**.
- **Authorization:** Checks **what that caller may do**—such as reading a document or executing a tool. Insufficient permission normally results in **403**.

| Concept | Where it fits |
|---|---|
| **OAuth 2.0** | An authorization framework that lets clients obtain access tokens for limited API access. |
| **OpenID Connect — OIDC** | Adds an authentication layer to OAuth 2.0, supporting login and identity information. |
| **JWT — JSON Web Token** | A token format carrying claims, such as subject, expiry and scope. OAuth access tokens can be JWTs or opaque tokens. |

**Key nuance:** OAuth defines the access framework; JWT defines a token format. A signed JWT is not automatically encrypted.

Before trusting JWT claims, verify the signature, issuer, audience and expiry. Then separately enforce permissions and resource access—**a valid token does not grant access to every document or tool**.
## Section 4: MCP and LLM tool integration

### 4.1. What is MCP, and what problem does it solve?

**MCP — Model Context Protocol** is an open protocol that standardizes how AI applications connect to external tools and data sources.

Without a shared protocol, each AI application may need custom integration code for every external system. MCP provides a common interface for **discovering capabilities, describing tool inputs, making calls and receiving results**, reducing duplicated integration work.

An MCP server can expose:

- **Tools:** Executable operations, such as searching filings or querying a database.
- **Resources:** Contextual data, such as document contents or database schemas.
- **Prompts:** Reusable prompt templates.

For example, a filing service can expose `search_filings` through an MCP server, allowing compatible AI applications to discover and invoke it.

**Key distinction:** MCP standardizes integration. The application still manages the agent loop, permissions and execution limits.
### 4.2. How is MCP different from LLM function calling and a REST API?

They address different parts of the interaction:

| Concept | What it does |
|---|---|
| **LLM function calling** | Lets the model produce a structured request containing a tool name and arguments. The application executes it and supplies the result back to the model. |
| **MCP** | Standardizes communication between an AI application and tool/data servers, including discovery, schemas, tool calls and results. |
| **REST API** | Exposes resources through a uniform interface, typically using URLs and HTTP methods such as GET and POST. |

**They can work together.** For example:

1. The LLM requests `search_filings` through function calling.
2. The application validates the request and invokes the tool through its MCP client.
3. The MCP server queries an underlying REST API and returns the result.
4. The application gives that result back to the LLM.
**Key nuance:** MCP uses JSON-RPC messages. Using HTTP as its transport does not make it a REST API.
- **REST:** The HTTP method and URL express the operation.`GET /filings/123` — retrieve filing 123.
- **JSON-RPC:** A JSON message contains the operation’s name and arguments, such as `"method": "tools/call"`.
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "add",
  "params": {
    "a": 2,
    "b": 3
  }
}
```
- **`jsonrpc`** — protocol version.
- **`id`** — identifies the request so its response can be matched.
- **`method`** — operation to execute.
- **`params`** — arguments for that operation.

**Response**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": 5
}
```
### 4.3. What are the roles of the MCP host, client and server?
| Component | Role |
|---|---|
| **Host** | The AI application that coordinates the LLM, context and tool access. It creates and manages MCP clients. |
| **Client** | A protocol component inside the host that connects to a particular MCP server, discovers its capabilities, sends requests and receives results. |
| **Server** | A program that exposes tools, resources and prompts, and handles requests using underlying data or services. It can run locally or remotely. |

**Example:** A research assistant is the **host**. Its filings connector is an **MCP client**. The service exposing `search_filings` is the **MCP server**.

A host can manage multiple clients, typically one per server.

**Key nuance:** The LLM requests a tool; the host’s runtime uses the MCP client to invoke it. The LLM itself is not the MCP client.

### 4.4. What is the difference between MCP tools, resources and prompts?

| Capability | What it provides | Example |
|---|---|---|
| **Tools** | Executable operations with defined inputs. They can retrieve information or change external state. | `search_filings` or `create_report`. |
| **Resources** | Readable data identified by a URI, which the application can supply as context. | A filing’s contents or a database schema. |
| **Prompts** | Reusable, parameterized templates that produce messages or instructions for the model. | A company-analysis template taking a company name. |

The typical control pattern is:
- **Tools:** The model requests an operation; the runtime executes it.
- **Resources:** The application selects context to include.
- **Prompts:** The user selects a predefined task template.
**Key nuance:** Tools can be read-only too. Fetching a prompt supplies instructions; it does not itself execute an agent workflow. Permissions remain enforced by the application and server.
### 4.5. What is tool discovery, and how do `tools/list` and `tools/call` differ?
**Tool discovery** lets an MCP client ask a server which tools it exposes and how to invoke them.
| Method | Purpose | What it returns |
|---|---|---|
| **`tools/list`** | Discover available tools without executing them. | Tool definitions: names, descriptions, input schemas and optional output schemas. |
| **`tools/call`** | Invoke a named tool with arguments. | The execution result or an error. |
**Example:**
1. `tools/list` reveals a `search_filings` tool that requires a company name.
2. The application makes that tool definition available to the LLM.
3. When the LLM requests it, the runtime sends `tools/call` with the tool name and arguments.
**Key nuance:** Discovering a tool does not grant permission to use it. The runtime and server must still validate arguments and enforce access controls.
### 4.6. What is a tool schema, and how does JSON Schema support argument validation?
A **tool schema** is a machine-readable contract describing a tool’s name, purpose and expected arguments, plus optionally its output structure.
**JSON Schema** defines validation rules such as types, required fields, allowed values, length limits and numeric bounds.
Example `inputSchema` for a retrieval tool:
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string", "minLength": 1},
    "top_k": {"type": "integer", "minimum": 1, "maximum": 20}
  },
  "required": ["query", "top_k"],
  "additionalProperties": false
}
```
A validator rejects:
- Missing `query` or `top_k`.
- An empty query or `top_k: "5"`—a string.
- `top_k: 100` or unexpected fields.
**Key nuance:** The schema describes the rules; the runtime/server must enforce them before execution. Valid arguments still require separate authorization and business-rule checks.

### 4.7. What is JSON-RPC, and how do MCP’s stdio and Streamable HTTP transports differ?

**JSON-RPC 2.0** is a remote procedure call protocol using JSON messages. A request specifies a method, optional arguments and an ID; the response carries the same ID with a result or error. Notifications omit the ID and receive no JSON-RPC response.

**JSON-RPC defines the message structure; the transport defines how messages travel.**

| Transport | How it works | Typical use |
|---|---|---|
| **stdio** | The client launches a local server subprocess. Messages travel through its stdin/stdout, one JSON message per line. | Locally managed tools. |
| **Streamable HTTP** | The client sends JSON-RPC messages through HTTP POST to an MCP endpoint. Responses can be ordinary JSON or an SSE stream. | Independently deployed services, local or remote. |

**Key nuances:** stdio logs belong on **stderr**, because stdout carries protocol messages. Streamable HTTP does not require every response to stream, and using HTTP does not make MCP a REST API.
### 4.8. What are structured tool outputs, and why are they useful compared with plain text?

**Structured tool outputs** return machine-readable data with explicit fields and types, rather than requiring downstream code to extract values from prose.
Example retrieval payload:
```json
{
  "document_id": "doc-123",
  "block_id": "b004",
  "text": "Extracted passage...",
  "score": 0.91
}
```
They support:
- **Reliable integration:** Code reads specific fields directly, without parsing sentences.
- **Validation:** An output schema checks required fields, types and constraints.
- **Traceability:** Source IDs and metadata remain attached to evidence.
- **Automation and evaluation:** Results can be compared, routed and passed between tools consistently.
In MCP, structured data is returned through **`structuredContent`**. If the tool declares an **`outputSchema`**, its structured result must conform to it.
**Key nuance:** Correct structure does not guarantee correct facts. Evidence and business-rule checks are still needed.
### 4.9. What is the difference between a protocol error and a tool-execution error, and how should each be reported?

| Error type | What failed? | How to report it |
|---|---|---|
| **Protocol error** | The MCP/JSON-RPC request cannot be handled correctly—for example, a malformed request, unknown method or unknown tool. | A top-level JSON-RPC **`error`** object containing a numeric `code` and a `message`, with the matching request ID where available. |
| **Tool-execution error** | A recognized tool reports invalid argument values, an upstream API failure or a business-rule failure. | A normal JSON-RPC **`result`** containing **`isError: true`** and explanatory tool content. |

**Example:** An unknown `book_flight` tool is a protocol error. A known `book_flight` tool rejecting a departure date in the past is a tool-execution error.

Tool errors should provide actionable feedback so the model can correct its inputs or choose another action.

**Key nuance:** Receiving a JSON-RPC `result` does not prove the operation succeeded—check `isError`.
### 4.10. How do authentication, authorization and least-privilege access apply to MCP tools?

| Principle | Application to MCP |
|---|---|
| **Authentication** | Establish who the caller is—a user or service. Protected HTTP MCP servers validate access tokens, including expiry and intended audience. |
| **Authorization** | Check whether that caller may invoke this tool on the requested resources. Enforce document, account and tenant restrictions on every call. |
| **Least privilege** | Grant only the necessary tools, scopes, data access and downstream permissions. Use read-only credentials for retrieval and restrict local stdio server privileges. |

**Example:** A research assistant may search permitted filings, but should not receive database administrator credentials or access another tenant’s documents.

The host can restrict available tools and require approval for sensitive actions. **The server must independently enforce access controls**—hiding a tool from the model is insufficient.

**Key nuance:** Derive caller identity and tenant context from trusted credentials, not model-generated tool arguments.

## Section 5: LLM evaluation, grounding and guardrails

### 5.1. What is the difference between retrieval evaluation, response evaluation and end-to-end evaluation?

| Evaluation | What it measures | Typical checks |
|---|---|---|
| **Retrieval** | Whether the system finds and ranks the evidence needed to answer. | Recall@K, precision@K, MRR, nDCG. |
| **Response** | Whether the generated answer is accurate, supported and useful. | Correctness, faithfulness, relevance, completeness and citations. |
| **End-to-end** | Whether the complete application successfully handles the user’s task. | Task success, policy adherence, latency and cost. |

**Key nuance:** Good retrieval does not guarantee a good answer. Evaluate components separately to diagnose failures, and the complete system to assess actual user outcomes.

### 5.2. What is the difference between faithfulness to retrieved evidence and factual correctness?

- **Faithfulness:** Are the answer’s claims supported by the retrieved evidence?
- **Factual correctness:** Are those claims true for the question’s entity, time period and scope, checked against reliable references?

An answer can faithfully repeat an incorrect or outdated source. Conversely, it can state a true fact from model knowledge that the supplied evidence does not support.

**Key nuance:** Measure these separately. Grounding establishes support from evidence; it does not establish that the evidence itself is accurate. Reference-based correctness scores also depend on the quality of their reference answers.

### 5.3. What is the difference between answer relevance and answer completeness?

- **Relevance:** Does the answer directly address the question without distracting material?
- **Completeness:** Does it cover every required part of the question?

If the user requests revenue, growth and fiscal year-end, an answer giving only revenue is **relevant but incomplete**.

A long company overview may contain useful facts while failing to answer the specific question.

**Key nuance:** Evaluate completeness against an explicit checklist of required items. Length is not a reliable measure, and neither relevance nor completeness alone proves factual correctness.

### 5.4. What is claim-level validation, and how do citation correctness and citation coverage differ?

**Claim-level validation** breaks an answer into independently checkable claims and evaluates each against evidence—for example, supported, contradicted or insufficient evidence.

- **Citation correctness:** Do the supplied citations support the claims attached to them?
- **Citation coverage:** What proportion of claims requiring evidence have sufficient supporting citations?

If five claims require evidence and only one has a correct supporting citation, citation correctness could be **100%**, while coverage is only **20%**.

**Key nuance:** A working link proves that a source exists, not that it supports the claim. Check the cited passage, including entity, period and units; multiple passages may jointly support a claim.

## Section 6: Asynchronous processing and distributed-system reliability

### 6.1. What is queue-based asynchronous processing, and how is it different from using `async/await` inside an API?



### 6.2. What are at-most-once, at-least-once and exactly-once delivery semantics?



### 6.3. What is idempotency, and how do idempotency keys prevent duplicate processing?



### 6.4. What are message acknowledgments and visibility timeouts, and how do they support recovery after a worker crashes?



### 6.5. What are exponential backoff and jitter, and which failures should be retried?



### 6.6. What is a dead-letter queue, and when should a message be moved into it?



### 6.7. What are bounded concurrency and backpressure, and how do they work together to control load?



### 6.8. What is a race condition, and how do atomic operations and distributed locks help prevent it?



### 6.9. What is rate limiting, and how does a Redis-backed token-bucket limiter work?



### 6.10. What is a circuit breaker, and how does it work alongside timeouts and retries?



## Section 7: Applied ML and NLP

### 7.1. What are training, validation and test sets, and what is data leakage?



### 7.2. What are overfitting and underfitting, and how does regularization help?



### 7.3. What are precision, recall and F1, and how do macro, micro and weighted F1 differ?

- **Precision:** Of everything predicted positive, how much was correct? `TP / (TP + FP)`. Useful when false alarms are costly.
- **Recall:** Of everything actually positive, how much did we detect? `TP / (TP + FN)`. Useful when missed positives are costly.
- **F1:** Harmonic mean of precision and recall: `2PR / (P + R)`. A low value in either pulls F1 down.

`TP` = correct positive predictions, `FP` = false alarms, `FN` = missed positives.

For multiple classes, treat each class as positive against all others:

| Average | Calculation | Emphasis |
|---|---|---|
| **Macro F1** | Calculate each class’s F1, then take the unweighted mean | Every class matters equally |
| **Micro F1** | Pool TP, FP and FN across classes, then calculate F1 | Every prediction contributes equally |
| **Weighted F1** | Average per-class F1 weighted by actual class counts, called support | Larger classes contribute more |

**Key nuance:** For single-label multiclass classification with all classes included, micro F1 equals accuracy. Weighted F1 can hide poor minority-class performance.


### 7.4. What is class imbalance, and how do class weights, oversampling and undersampling address it?

**Class imbalance** means some classes have far more examples than others. With 99% legitimate transactions, predicting “legitimate” every time achieves 99% accuracy while detecting zero fraud.

| Method | How it addresses imbalance | Tradeoff |
|---|---|---|
| **Class weights** | Give minority-class examples greater weight in the training loss; sample counts stay unchanged | Excessive weights can increase false positives |
| **Oversampling** | Repeat minority examples or generate synthetic examples, such as with SMOTE | Repetition can overfit; synthetic examples can be unrealistic |
| **Undersampling** | Train on fewer majority-class examples | Faster training, but may discard useful information |

**Key nuance:** Split first, then resample only training data—including inside each cross-validation training fold. Keep validation and test data representative of production.

Evaluate per-class precision/recall and macro F1, and choose the approach based on the business cost of missed positives versus false alarms.


### 7.5. What is a classification threshold, and how do ROC-AUC and PR-AUC differ when evaluating a fraud model?



### 7.6. What is transfer learning, and how does fine-tuning differ from using a pretrained model as a frozen feature extractor?



### 7.7. What is tokenization, and why do transformer models use subword tokens, padding and truncation?



### 7.8. What is knowledge distillation, and how does DistilBERT differ from BERT?



### 7.9. What is gradient boosting, and how does XGBoost differ from a random forest?



### 7.10. What is SHAP, and how do local and global model explanations differ?



## Section 8: MLOps, cloud deployment and production observability

### 8.1. What is MLOps, and what roles do experiment tracking and a model registry play?



### 8.2. What are CI/CD and continuous training in an ML system, and what checks should happen before a model is promoted?



### 8.3. What is the difference between a Docker image and a container, and why is containerization useful for model deployment?



### 8.4. What is the difference between real-time, asynchronous and batch inference?



### 8.5. What are canary deployments and shadow deployments, and how do they support safe releases and rollback?



### 8.6. What is the difference between data drift, concept drift and model-performance degradation?



### 8.7. What is the difference between logs, metrics and traces, and when would you use each?

| Signal | What it records | When to use it |
|---|---|---|
| **Logs** | Timestamped events with details: errors, retry attempts and contextual fields | Debug a specific failure and inspect what happened |
| **Metrics** | Numerical measurements aggregated over time: request counts, error rates, p95 latency and token usage | Monitor trends, build dashboards and trigger alerts |
| **Traces** | The execution path of a request or agent run, composed of timed operations called **spans** | Find bottlenecks and understand interactions across retrieval, LLM calls, tools and services |

**Agent example:** Metrics reveal rising response latency. A trace identifies a slow tool call and its retries. The associated logs show the timeout errors.

**Key nuance:** Use them together. Propagate trace context across services and include `trace_id` and `span_id` in structured logs so you can connect an individual event to its execution path.

### 8.8. What is distributed tracing, and how do trace IDs, spans and context propagation connect API, queue and worker activity?



### 8.9. What are SLIs and SLOs, and why do p95/p99 latency and error rates matter more than averages alone?



### 8.10. What is agent observability, and how do recorded prompts, tool calls, state changes and token/cost metrics help debug agent runs?

**Agent observability means inspecting an agent’s execution to understand its behavior, failures, latency and cost.** It connects the final answer to the steps that produced it.

| Recorded data | How it helps debug |
|---|---|
| **Prompts and context** | Show what instructions, history and retrieved evidence the model actually received; expose missing evidence or stale context |
| **Tool calls** | Record tool names, arguments, results, errors and duration; reveal wrong tool choices, invalid arguments and dependency failures |
| **State changes** | Show how memory, evidence and workflow status changed; reveal overwritten values, lost results and incorrect routing |
| **Token/cost metrics** | Track usage and estimated charges per step and run, including retries; expose growing context and unnecessary model calls |

**Example:** Repeated searches appear in tool traces. State snapshots reveal that earlier results were never saved. Token/cost metrics quantify the wasted calls.

**Key nuance:** Correlate records using run/trace IDs, capture model and prompt versions, and redact sensitive content. A recorded trace supports investigation; resumable execution requires checkpoints.

