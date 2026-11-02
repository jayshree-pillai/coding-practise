# LangGraph: Easy–Medium Questions and Answers

38 questions for FDE / Applied AI coding interview practice. Each answer follows its choices and includes a complete Python example, observed output, and a plain walkthrough.

## Scope and verification

Reviewed every question and answer-key entry in the four supplied PDFs: `LangGraph-E-M-Set1-Questions.pdf`, `LangGraph-E-M-Set1-Answers.pdf`, `LangGraph-M-H-Set2-Questions.pdf`, and `LangGraph-M-H-Set2-Answers.pdf`.

- Retained all 20 questions from Set 1 and 18 from Set 2, judging their actual difficulty rather than copying the original set label. Original set and question numbers are preserved; numbering gaps are intentional.
- Excluded Set 2 Q12 (durable recovery using saved pending writes) and Q16 (matching multiple interrupt responses after call-order changes) as Hard. Their full questions and answers are omitted.
- No answer-key letters needed correction. Stems and assumptions were clarified, and the examples expand only concepts already present in the supplied sets.
- All 38 answer examples were executed independently in fresh Python processes. Their standard output was compared with the output printed below. Expected graph errors are caught explicitly in the relevant examples.
- Graph execution uses the real installed LangGraph APIs. Sample evidence, drafts, ticket systems, tool responses, database-client stand-ins, and token counts are fixed or simulated wherever stated. No model provider, hosted service, or API key is required.

Verified locally on November 1, 2026 with Python **3.12.14**, `langgraph==1.2.19`, `langchain-core==1.7.3`, `langgraph-checkpoint==4.3.1`, and `langgraph-checkpoint-sqlite==3.1.3`. The SQLite package is needed for Set 1 Q18 only.

Install the tested versions once in your Python environment:

```bash
python -m pip install "langgraph==1.2.19" "langchain-core==1.7.3" "langgraph-checkpoint==4.3.1" "langgraph-checkpoint-sqlite==3.1.3"
```

Every Python block can then be copied into its own file and run independently. It includes its own imports, state definitions, helper functions, and input data. Outputs correspond to these pinned versions; generated internal IDs are avoided in the displayed output.

For practice, predict the next node, its input values, and its returned update before reading the output. `TypedDict` describes dictionary fields for type checking; it does not perform Pydantic-style runtime validation or fill missing fields automatically.

---

## Set 1 - Q01: What LangGraph coordinates (Easy)

**Original reference:** LangGraph-E-M-Set1, question 01.

A report application needs to retrieve evidence, create a draft, and choose whether that draft needs revision. It must carry data between these steps. Which requirement is LangGraph's main responsibility in this design?


A. Store document embeddings and rank their similarity.

B. Coordinate a stateful workflow with branches, loops, and optional human review.

C. Validate HTTP request payloads against Python type definitions.

D. Expose Python functions as HTTP endpoints.

**Answer: B.**

- B: The graph defines which step runs next and carries the state between steps.
- A: A retrieval backend stores and searches embeddings; a graph can call it.
- C: A validation library handles payload validation. Graph coordination is a different job.
- D: An HTTP framework exposes endpoints; an endpoint can invoke the graph.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    company: str
    evidence: str
    draft: str

def retrieve(state: State):
    evidence = f"{state['company']} revenue grew 12%."
    print("retrieved:", evidence)
    return {"evidence": evidence}

def draft(state: State):
    # Fixed Python formatting, not an LLM response.
    text = f"Report: {state['evidence']}"
    print("drafted:", text)
    return {"draft": text}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("draft", draft)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
graph = builder.compile()
result = graph.invoke({"company": "Acme", "evidence": "", "draft": ""})
print("final draft:", result["draft"])
```

**Expected output (captured from the local run):**

```text
retrieved: Acme revenue grew 12%.
drafted: Report: Acme revenue grew 12%.
final draft: Report: Acme revenue grew 12%.
```

**Follow the data flow:**

1. `State` names the information this tiny workflow carries. A `TypedDict` describes the dictionary shape; it is not a runtime payload validator.
2. `retrieve` receives that dictionary and returns one new value, `evidence`.
3. The edge from `retrieve` to `draft` makes the draft step run after the evidence is available.
4. `invoke` runs the compiled workflow. The example uses the simplest linear path; branches and human review can be added when required.

---

## Set 1 - Q02: Read and update shared state (Easy)

**Original reference:** LangGraph-E-M-Set1, question 02.

A report workflow starts with `company="Acme"`, an empty evidence list, and an empty draft. The retrieval step returns evidence; the drafting step reads it. What is graph state?


A. The Python call stack for whichever node is running.

B. A prompt template automatically sent to every model.

C. An external vector index shared by all workers.

D. Structured data that nodes read and update during execution.

**Answer: D.**

- D: State carries the company, evidence, and draft between nodes.
- A: The call stack tracks active Python calls; it is not the workflow data dictionary.
- B: Nodes explicitly decide whether to build and send prompts. State is not sent automatically.
- C: A vector index is an external resource, not the graph state itself.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    company: str
    evidence: list[str]
    draft: str

def retrieve(state: State):
    print("retrieve reads company:", state["company"])
    return {"evidence": ["Revenue: $120 million", "Growth: 12%"]}

def draft(state: State):
    print("draft reads evidence:", state["evidence"])
    return {"draft": state["company"] + ": " + "; ".join(state["evidence"])}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("draft", draft)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
graph = builder.compile()
result = graph.invoke({"company": "Acme", "evidence": [], "draft": ""})
print("final state:", result)
```

**Expected output (captured from the local run):**

```text
retrieve reads company: Acme
draft reads evidence: ['Revenue: $120 million', 'Growth: 12%']
final state: {'company': 'Acme', 'evidence': ['Revenue: $120 million', 'Growth: 12%'], 'draft': 'Acme: Revenue: $120 million; Growth: 12%'}
```

**Follow the data flow:**

1. The input dictionary supplies all three initial fields.
2. `retrieve` returns only `evidence`. The existing `company` stays available for the next step.
3. `draft` reads the updated evidence list and joins its two strings with `"; "`.
4. The final dictionary contains the original company plus the evidence and draft produced by the nodes. No model is called.

---

## Set 1 - Q03: Return a partial state update (Easy)

**Original reference:** LangGraph-E-M-Set1, question 03.

A `TypedDict`-based graph has ordinary fields `question`, `evidence`, and `answer`, with no custom reducers. Before a node runs, `question="Can we approve?"`, `evidence=["Reviewed"]`, and `answer=""`. The node must set `answer` to `"Approved"` and preserve both other values. Which return value does that?


A. `{"answer": "Approved"}`

B. `"Approved"`

C. `{"question": None, "evidence": None, "answer": "Approved"}`

D. `None`, after assigning `answer = "Approved"` only to a local variable

**Answer: A.**

- A: Returning just `answer` updates that field while preserving omitted fields.
- B: A bare string does not tell this state graph which field to update.
- C: Explicit `None` values overwrite the question and evidence; they do not preserve them.
- D: A local assignment is not a state update returned to LangGraph.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str
    evidence: list[str]
    answer: str

def approve(state: State):
    print("node reads:", state)
    update = {"answer": "Approved"}
    print("node returns:", update)
    return update

builder = StateGraph(State)
builder.add_node("approve", approve)
builder.add_edge(START, "approve")
builder.add_edge("approve", END)
graph = builder.compile()
result = graph.invoke({"question": "Can we approve?", "evidence": ["Reviewed"], "answer": ""})
print("final state:", result)
```

**Expected output (captured from the local run):**

```text
node reads: {'question': 'Can we approve?', 'evidence': ['Reviewed'], 'answer': ''}
node returns: {'answer': 'Approved'}
final state: {'question': 'Can we approve?', 'evidence': ['Reviewed'], 'answer': 'Approved'}
```

**Follow the data flow:**

1. The node receives the full input state.
2. `update` contains one key. It says exactly which value the graph should change.
3. The graph replaces the empty answer with `"Approved"`.
4. Because the node omits `question` and `evidence`, their previous values remain in the final state.

---

## Set 1 - Q04: Compile first, execute second (Easy)

**Original reference:** LangGraph-E-M-Set1, question 04.

You have added a node and valid `START`/`END` edges to a `StateGraph` builder. No invocation has occurred. What does `builder.compile()` return?


A. A vector index containing all node outputs.

B. The final result of a run using invented default input.

C. An executable graph with methods such as `invoke()` and `stream()`.

D. An HTTP server with one endpoint per node.

**Answer: C.**

- C: Compilation prepares an executable graph; invoking it is a separate action.
- A: No retrieval index is built by compilation.
- B: Compilation does not run the nodes or invent input.
- D: Serving HTTP requires separate application or deployment code.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    number: int

calls: list[int] = []

def double(state: State):
    calls.append(state["number"])
    return {"number": state["number"] * 2}

builder = StateGraph(State)
builder.add_node("double", double)
builder.add_edge(START, "double")
builder.add_edge("double", END)
graph = builder.compile()
print("calls after compile:", calls)
result = graph.invoke({"number": 3})
print("calls after invoke:", calls)
print("result:", result)
```

**Expected output (captured from the local run):**

```text
calls after compile: []
calls after invoke: [3]
result: {'number': 6}
```

**Follow the data flow:**

1. `calls` is a local observation list, used only to show whether the node ran.
2. After `compile`, the list is still empty: the node has not executed.
3. `invoke({"number": 3})` supplies actual input and runs `double`.
4. The node records `3`, then returns `6`. The graph result is a state dictionary, not a raw integer.

---

## Set 1 - Q05: Follow START and END (Easy)

**Original reference:** LangGraph-E-M-Set1, question 05.

A linear report graph has edges `START → retrieve → draft → END`. What do `START` and `END` represent?


A. The first and last chat messages.

B. The workflow entry point and a terminal destination.

C. Opening and closing a database connection.

D. The beginning and end of a model response.

**Answer: B.**

- B: These special markers describe graph control flow.
- A: Chat messages are data in state, separate from these markers.
- C: Database lifecycle handling must be implemented separately.
- D: A model call has its own response lifecycle inside a node.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    steps: list[str]

def retrieve(state: State):
    steps = state["steps"] + ["retrieve"]
    print("retrieve returns:", steps)
    return {"steps": steps}

def draft(state: State):
    steps = state["steps"] + ["draft"]
    print("draft returns:", steps)
    return {"steps": steps}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("draft", draft)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
graph = builder.compile()
print("final steps:", graph.invoke({"steps": []})["steps"])
```

**Expected output (captured from the local run):**

```text
retrieve returns: ['retrieve']
draft returns: ['retrieve', 'draft']
final steps: ['retrieve', 'draft']
```

**Follow the data flow:**

1. `START → retrieve` chooses the first node.
2. `retrieve → draft` schedules the second node after the first finishes.
3. `draft → END` ends this linear path. `START` and `END` do not run your Python functions.
4. The `steps` list is ordinary application data added for observation. The special markers are not automatically inserted into it.

---

## Set 1 - Q06: Choose one branch from updated state (Medium)

**Original reference:** LangGraph-E-M-Set1, question 06.

An `evaluate` node writes `quality` into state. After it finishes, exactly one next node must run: `revise` when `quality < 0.8`, otherwise `publish`. Which design expresses that decision?


A. Add two unconditional edges from `evaluate`, one to each destination.

B. Give `quality` a reducer and expect the reducer to schedule a destination.

C. Create a separate `thread_id` for each destination.

D. Add a conditional edge from `evaluate` whose routing function chooses the destination.

**Answer: D.**

- D: The routing function reads the updated quality and selects one destination for this scenario.
- A: Two unconditional edges schedule both destinations rather than making an either/or choice.
- B: Reducers combine state values; they do not schedule graph nodes.
- C: A thread ID selects persisted execution state, not the next branch.

**Standalone example — run locally; no API key required.**

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    sample_score: float
    quality: float
    action: str

def evaluate(state: State):
    # Fixed sample score, not a model-based evaluator.
    return {"quality": state["sample_score"]}

def choose_next(state: State) -> Literal["revise", "publish"]:
    destination = "revise" if state["quality"] < 0.8 else "publish"
    print("router sees:", state["quality"], "->", destination)
    return destination

def revise(state: State):
    return {"action": "needs revision"}

def publish(state: State):
    return {"action": "published"}

builder = StateGraph(State)
builder.add_node("evaluate", evaluate)
builder.add_node("revise", revise)
builder.add_node("publish", publish)
builder.add_edge(START, "evaluate")
builder.add_conditional_edges("evaluate", choose_next)
builder.add_edge("revise", END)
builder.add_edge("publish", END)
graph = builder.compile()
for score in [0.6, 0.9]:
    result = graph.invoke({"sample_score": score, "quality": 0.0, "action": ""})
    print("result:", result["action"])
```

**Expected output (captured from the local run):**

```text
router sees: 0.6 -> revise
result: needs revision
router sees: 0.9 -> publish
result: published
```

**Follow the data flow:**

1. `evaluate` copies a fixed sample score into `quality` so you can focus on routing.
2. The conditional edge runs `choose_next` after that update. The router sees `0.6` or `0.9`, not the initial `0.0`.
3. The router returns a node name. It does not return a state update.
4. For `0.6`, only `revise` runs. For `0.9`, only `publish` runs. This small example ends after the chosen action.

---

## Set 1 - Q07: Replace a message by its ID (Medium)

**Original reference:** LangGraph-E-M-Set1, question 07.

The current message history contains an assistant message with `id="answer-1"` and content `"Revenue is 10."`. An update contains an assistant message with the same ID and corrected content `"Revenue is 12."`, plus a new message with `id="answer-2"`. What does `add_messages` do?


A. Replace the matching message and append the message with the new ID.

B. Append both messages, leaving a duplicate `answer-1`.

C. Discard both messages because existing history cannot change.

D. Sort every message alphabetically by its ID.

**Answer: A.**

- A: `add_messages` merges by message ID: a matching ID replaces, and a new ID appends.
- B: Plain list concatenation would duplicate the matching message; this reducer is ID-aware.
- C: Existing messages can be replaced through ID-based updates.
- D: The reducer preserves history positions for replacements; it does not alphabetically sort IDs.

**Standalone example — run locally; no API key required.**

```python
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages

history = [
    HumanMessage(content="What is revenue?", id="question-1"),
    AIMessage(content="Revenue is 10.", id="answer-1"),
]
updates = [
    AIMessage(content="Revenue is 12.", id="answer-1"),
    AIMessage(content="Growth is 20%.", id="answer-2"),
]
print("before:", [(m.id, m.content) for m in history])
print("updates:", [(m.id, m.content) for m in updates])
merged = add_messages(history, updates)
print("after:", [(m.id, m.content) for m in merged])
print("message count:", len(merged))
```

**Expected output (captured from the local run):**

```text
before: [('question-1', 'What is revenue?'), ('answer-1', 'Revenue is 10.')]
updates: [('answer-1', 'Revenue is 12.'), ('answer-2', 'Growth is 20%.')]
after: [('question-1', 'What is revenue?'), ('answer-1', 'Revenue is 12.'), ('answer-2', 'Growth is 20%.')]
message count: 3
```

**Follow the data flow:**

1. Every message has an explicit ID, making the merge easy to inspect.
2. The new `answer-1` takes the old `answer-1` position and replaces its text.
3. `answer-2` has no match, so it appears at the end.
4. There are three messages, not four. The messages contain fixed sample text; no model is called. In graph state, you attach this function as the message field reducer.

---

## Set 1 - Q08: Inspect checkpointed state (Easy)

**Original reference:** LangGraph-E-M-Set1, question 08.

A report graph uses a checkpointer and a stable thread ID. After a run completes, the application needs to inspect the saved report state or continue that thread later. What is the checkpointer's primary job?


A. Judge whether the report is factually correct.

B. Store only the Python source files.

C. Save graph execution state and execution information for a thread.

D. Convert all synchronous node functions into asynchronous functions.

**Answer: C.**

- C: Checkpoints preserve thread state and execution information that support inspection and continuation.
- A: Factual evaluation requires explicit logic and evidence.
- B: Checkpoints concern execution state, not merely source code.
- D: A checkpointer does not rewrite node functions into async functions.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    company: str
    status: str

def finish(state: State):
    print("node reads company:", state["company"])
    return {"status": "draft saved"}

builder = StateGraph(State)
builder.add_node("finish", finish)
builder.add_edge(START, "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "report-42"}}
graph.invoke({"company": "Acme", "status": "new"}, config=config)
snapshot = graph.get_state(config)
print("saved values:", snapshot.values)
print("next nodes:", snapshot.next)
```

**Expected output (captured from the local run):**

```text
node reads company: Acme
saved values: {'company': 'Acme', 'status': 'draft saved'}
next nodes: ()
```

**Follow the data flow:**

1. `InMemorySaver()` provides a real local checkpointer. It lasts only as long as this process and saver instance.
2. `config` identifies which thread receives the checkpoints.
3. `get_state(config)` reads the saved snapshot for that thread after the run.
4. `snapshot.values` contains the report data. The empty `snapshot.next` tuple means this completed run has no next node scheduled; a paused run can have pending work.

---

## Set 1 - Q09: Select the checkpoint thread (Easy)

**Original reference:** LangGraph-E-M-Set1, question 09.

A compiled graph uses a checkpointer. You want checkpoints for report 42 to use the thread identity `"report-42"`. Which configuration sets that identity in the checkpointer's expected location?


A. `{"configurable": {"thread_id": "report-42"}}`

B. `{"metadata": {"thread_id": "report-42"}}`

C. `{"configurable": {"run_name": "report-42"}}`

D. `{"tags": ["report-42"]}`

**Answer: A.**

- A: The checkpointer reads the thread identity from `config["configurable"]["thread_id"]`.
- B: Metadata describes a run; this location does not set the required configurable thread identity.
- C: A run name is not a checkpoint thread ID.
- D: Tags label runs; they do not select a checkpoint thread.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    company: str
    status: str

def finish(state: State):
    return {"status": "ready"}

builder = StateGraph(State)
builder.add_node("finish", finish)
builder.add_edge(START, "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())
config_42 = {"configurable": {"thread_id": "report-42"}}
config_43 = {"configurable": {"thread_id": "report-43"}}
graph.invoke({"company": "Acme", "status": "new"}, config=config_42)
graph.invoke({"company": "Beta", "status": "new"}, config=config_43)
print("thread 42:", graph.get_state(config_42).values)
print("thread 43:", graph.get_state(config_43).values)
```

**Expected output (captured from the local run):**

```text
thread 42: {'company': 'Acme', 'status': 'ready'}
thread 43: {'company': 'Beta', 'status': 'ready'}
```

**Follow the data flow:**

1. The two configuration dictionaries differ only in their thread IDs.
2. The same compiled graph runs both reports, but the checkpointer records their states separately.
3. `get_state(config_42)` selects Acme; `get_state(config_43)` selects Beta.
4. Reusing the correct thread identity selects its saved state. An application must still enforce which users may access each thread.

---

## Set 1 - Q10: Read node updates while the graph runs (Easy)

**Original reference:** LangGraph-E-M-Set1, question 10.

A graph runs two nodes in order. `retrieve` returns only an `evidence` field; `draft` returns only an `answer` field. With `graph.stream(..., stream_mode="updates")` and the default stream format used in this file, what do you receive as execution progresses?


A. Only individual text tokens emitted by a model.

B. Only the entire final state, after all nodes finish.

C. A distributed tracing dashboard generated automatically.

D. Node-produced state updates, identified by node name.

**Answer: D.**

- D: Updates mode emits each node's returned state update during execution.
- A: Model message chunks belong to a different streaming mode; these ordinary nodes do not call a model.
- B: The stream emits incremental updates, not just a final dictionary.
- C: The stream supplies data; a dashboard would need separate UI or tracing infrastructure.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str
    evidence: str
    answer: str

def retrieve(state: State):
    return {"evidence": "Revenue grew 12%."}

def draft(state: State):
    # Fixed sample response; no LLM call.
    return {"answer": f"Answer: {state['evidence']}"}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("draft", draft)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
graph = builder.compile()
sample = {"question": "What changed?", "evidence": "", "answer": ""}
for update in graph.stream(sample, stream_mode="updates"):
    print(update)
```

**Expected output (captured from the local run):**

```text
{'retrieve': {'evidence': 'Revenue grew 12%.'}}
{'draft': {'answer': 'Answer: Revenue grew 12%.'}}
```

**Follow the data flow:**

1. `stream` returns an iterator; the `for` loop consumes events as the graph executes.
2. The first event identifies `retrieve` and contains only its returned `evidence` update.
3. The graph merges that evidence into state before `draft` reads it.
4. The second event identifies `draft` and contains only its returned `answer` update. Neither event repeats the unchanged question.

---

## Set 1 - Q11: Reducers apply separately to each field (Medium)

**Original reference:** LangGraph-E-M-Set1, question 11.

A graph uses `count: int` with the default replacement behavior, and `notes: Annotated[list[str], operator.add]` with list concatenation. Just before a node runs, state is `{"count": 4, "notes": ["retrieved"]}`. The node returns `{"count": 7, "notes": ["drafted"]}`. No other node writes in this step. What state does the next node receive?

A. `{"count": 11, "notes": ["drafted"]}`

B. `{"count": 7, "notes": ["retrieved", "drafted"]}`

C. `{"count": 11, "notes": ["retrieved", "drafted"]}`

D. `{"count": 7, "notes": ["drafted"]}`

**Answer: B.**

**Why it works:** `count` becomes `7` because its incoming update replaces its old value. For `notes`, the reducer calculates `["retrieved"] + ["drafted"]`, retaining both entries.

**Why the other choices fail:**

- A sums the integer even though it has no addition reducer, and drops an existing note.
- C gets the notes right but incorrectly sums `count` to `11`.
- D gets `count` right but ignores the list reducer.

**Standalone example — run locally; no API key required.**

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    count: int
    notes: Annotated[list[str], operator.add]

def draft(state: State) -> dict:
    print("Node reads:", state)
    update = {"count": 7, "notes": ["drafted"]}
    print("Node returns:", update)
    return update

builder = StateGraph(State)
builder.add_node("draft", draft)
builder.add_edge(START, "draft")
builder.add_edge("draft", END)
graph = builder.compile()
result = graph.invoke({"count": 4, "notes": ["retrieved"]})
print("Final state:", result)
```

**Expected output (observed locally):**

```text
Node reads: {'count': 4, 'notes': ['retrieved']}
Node returns: {'count': 7, 'notes': ['drafted']}
Final state: {'count': 7, 'notes': ['retrieved', 'drafted']}
```

**Follow the key lines:**

1. `Annotated[list[str], operator.add]` attaches an update rule to **notes only**. Because the values are lists, `operator.add` concatenates them.
2. `draft` reads the existing values, then returns only the values it wants to contribute. It does not manually rebuild the accumulated list.
3. `invoke` applies the return value field by field: replace `count`; concatenate `notes`. The final print makes those two different rules visible.


---

## Set 1 - Q12: Two parallel writes need a merge rule (Medium)

**Original reference:** LangGraph-E-M-Set1, question 12.

Two nodes, `section_a` and `section_b`, are both scheduled directly from `START`, so they run in the same superstep. The state field `results` is declared as `list[str]` with **no reducer**. Each node returns a new value for that field: `["A"]` and `["B"]`. What happens when LangGraph tries to apply both updates?

A. It automatically concatenates the lists into `["A", "B"]`.

B. It keeps whichever list was returned by the slower node.

C. It raises a concurrent-update error because no merge rule combines the writes.

D. It automatically reruns the nodes one at a time in alphabetical order.

**Answer: C.**

**Why it works:** The ordinary `results` field accepts one update per superstep. Two concurrent values need an explicit merge rule. LangGraph raises `InvalidUpdateError` rather than guessing which result to keep.

**Why the other choices fail:**

- A assumes list concatenation that the schema never requested.
- B assumes a last-writer-wins policy that this state channel does not provide.
- D assumes the graph changes its scheduling to repair a schema conflict.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import InvalidUpdateError

class State(TypedDict):
    results: list[str]

def section_a(state: State) -> dict:
    return {"results": ["A"]}

def section_b(state: State) -> dict:
    return {"results": ["B"]}

builder = StateGraph(State)
builder.add_node("section_a", section_a)
builder.add_node("section_b", section_b)
builder.add_edge(START, "section_a")
builder.add_edge(START, "section_b")
builder.add_edge("section_a", END)
builder.add_edge("section_b", END)
graph = builder.compile()
print("Initial results:", [])
print("Parallel updates:", {"section_a": ["A"], "section_b": ["B"]})
try:
    graph.invoke({"results": []})
except InvalidUpdateError as error:
    print("Error:", type(error).__name__)
    print("No combined final results were produced.")
```

**Expected output (observed locally):**

```text
Initial results: []
Parallel updates: {'section_a': ['A'], 'section_b': ['B']}
Error: InvalidUpdateError
No combined final results were produced.
```

**Follow the key lines:**

1. Both `START` edges schedule work for the same next superstep. The branches each return a dictionary containing `results`.
2. `results: list[str]` describes the value type, but does not tell LangGraph how to combine two writes. Typing a field as a list does not imply append behavior.
3. The `except` catches the expected graph error so the example finishes cleanly. The printed updates are a labeled summary of the two node return values; they do not claim a worker-completion order.
4. If collecting both lists is the intended behavior, the field needs an appropriate reducer, such as the list-concatenation annotation in the previous question. This example deliberately keeps the failing schema to demonstrate the error.


---

## Set 1 - Q13: Send a separate input to each worker (Medium)

**Original reference:** LangGraph-E-M-Set1, question 13.

A request contains a runtime list of section names. The list may have a different length on every request. You want one `write_section` task per name, each receiving `{"section": name}`, and you will combine the returned lists with an explicit reducer. Which routing pattern directly creates these tasks?

A. Return one `Send("write_section", {"section": name})` per name from routing logic.

B. Add one ordinary edge to `write_section`; it automatically iterates over every list item.

C. Attach a reducer to the section list; the reducer automatically schedules workers.

D. Give every section a different `thread_id`; the parent graph automatically joins those threads.

**Answer: A.**

**Why it works:** Each `Send` names a destination node and supplies the input for one task. Returning a list of two `Send` objects schedules two worker tasks; returning five schedules five.

**Why the other choices fail:**

- B schedules a destination through an ordinary edge; it does not map over a list.
- C confuses merging state updates with scheduling work.
- D creates separate checkpoint identities, not an automatic parent-worker relationship.

**Standalone example — run locally; no API key required.**

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    sections: list[str]
    results: Annotated[list[str], operator.add]

class WorkerInput(TypedDict):
    section: str

def dispatch(state: State) -> list[Send]:
    inputs = [{"section": name} for name in state["sections"]]
    print("Worker inputs:", inputs)
    return [Send("write_section", item) for item in inputs]

def write_section(state: WorkerInput) -> dict:
    return {"results": [state["section"] + ": drafted"]}

builder = StateGraph(State)
builder.add_node("write_section", write_section)
builder.add_conditional_edges(START, dispatch)
builder.add_edge("write_section", END)
graph = builder.compile()
result = graph.invoke({"sections": ["Risk", "Revenue"], "results": []})
print("Number of results:", len(result["results"]))
print("Results, sorted for display:", sorted(result["results"]))
```

**Expected output (observed locally):**

```text
Worker inputs: [{'section': 'Risk'}, {'section': 'Revenue'}]
Number of results: 2
Results, sorted for display: ['Revenue: drafted', 'Risk: drafted']
```

**Follow the key lines:**

1. `dispatch` converts `["Risk", "Revenue"]` into two small input dictionaries. The first print shows exactly what each worker receives.
2. `Send("write_section", item)` schedules the same node with a different input for each task. The worker reads `section`, rather than assuming it receives the whole parent state.
3. Each worker returns a one-item `results` list. `operator.add` combines those lists in the parent state.
4. The last line sorts **only for a stable display**. It does not assert that worker completion order is a reliable report order. Both requested sections have been drafted.


---

## Set 1 - Q14: Join two completed branches (Medium)

**Original reference:** LangGraph-E-M-Set1, question 14.

Two independent branches produce `section_a` and `section_b`. The `assemble` node needs both values. Which **single edge declaration** explicitly expresses that both named source nodes must finish before `assemble` is scheduled?

A. `builder.add_edge("section_a", "assemble")`

B. `builder.add_edge("section_b", "assemble")`

C. `builder.add_edge("assemble", END)`

D. `builder.add_edge(["section_a", "section_b"], "assemble")`

**Answer: D.**

**Why it works:** A list of source node names creates an all-sources join. Here, `assemble` waits for both `section_a` and `section_b`, then reads their completed state updates.

**Why the other choices fail:**

- A alone declares a dependency on `section_a`, with no explicit dependency on `section_b`.
- B alone declares a dependency on `section_b`, with no explicit dependency on `section_a`.
- C declares where execution goes after assembly, rather than when assembly can start.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    section_a: str
    section_b: str
    report: str

def section_a(state: State) -> dict:
    return {"section_a": "Revenue grew."}

def section_b(state: State) -> dict:
    return {"section_b": "Risk is stable."}

def assemble(state: State) -> dict:
    print("Assembly reads A:", state["section_a"])
    print("Assembly reads B:", state["section_b"])
    return {"report": state["section_a"] + " " + state["section_b"]}

builder = StateGraph(State)
builder.add_node("section_a", section_a)
builder.add_node("section_b", section_b)
builder.add_node("assemble", assemble)
builder.add_edge(START, "section_a")
builder.add_edge(START, "section_b")
builder.add_edge(["section_a", "section_b"], "assemble")
builder.add_edge("assemble", END)
graph = builder.compile()
result = graph.invoke({"section_a": "", "section_b": "", "report": ""})
print("Report:", result["report"])
```

**Expected output (observed locally):**

```text
Assembly reads A: Revenue grew.
Assembly reads B: Risk is stable.
Report: Revenue grew. Risk is stable.
```

**Follow the key lines:**

1. The two edges from `START` schedule the two section nodes. Each writes a **different** state field, so their updates do not conflict.
2. The list argument in `add_edge(["section_a", "section_b"], "assemble")` is the join. It names both prerequisites together.
3. `assemble` prints both values before combining them. The output shows that assembly receives both completed sections.
4. One branch could finish earlier in wall-clock time. The explicit join still expresses the requirement that both branches finish before assembly.


---

## Set 1 - Q15: Update state and choose the next node (Medium)

**Original reference:** LangGraph-E-M-Set1, question 15.

The `approve` node must set `approved` to `True` and choose `publish` as the next node. It has **no static outgoing edges**. Which return value expresses both operations?

A. `{"approved": True}`

B. `Command(update={"approved": True}, goto="publish")`

C. Return `Send("publish", {"approved": True})` directly as an ordinary node state update.

D. `Command(resume=True)`

**Answer: B.**

**Why it works:** `Command` can carry both a state update and a routing instruction. Its `update` field sets `approved`; its `goto` field schedules `publish`.

**Why the other choices fail:**

- A changes state but supplies no next destination in this graph.
- C uses a task-dispatch object as though it were this node's ordinary shared-state update-and-route return.
- D supplies a value to an already paused interrupt; it does not express this node's approval update and destination.

**Standalone example — run locally; no API key required.**

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class State(TypedDict):
    approved: bool
    status: str

def approve(state: State) -> Command[Literal["publish"]]:
    print("Approve reads approved:", state["approved"])
    return Command(update={"approved": True}, goto="publish")

def publish(state: State) -> dict:
    print("Publish reads approved:", state["approved"])
    return {"status": "published"}

builder = StateGraph(State)
builder.add_node("approve", approve)
builder.add_node("publish", publish)
builder.add_edge(START, "approve")
# approve has no static outgoing edge: its Command selects publish.
builder.add_edge("publish", END)
graph = builder.compile()
result = graph.invoke({"approved": False, "status": "draft"})
print("Final state:", result)
```

**Expected output (observed locally):**

```text
Approve reads approved: False
Publish reads approved: True
Final state: {'approved': True, 'status': 'published'}
```

**Follow the key lines:**

1. `Command[Literal["publish"]]` describes the possible destination in the return type. The actual runtime instruction is `goto="publish"`.
2. `update={"approved": True}` becomes visible to the next node. `publish` therefore prints `True`, even though the initial input was `False`.
3. There is deliberately no `approve -> publish` static edge. The returned `Command` provides the route.
4. A `Command` does not cancel existing ordinary outgoing edges. The question's no-static-edges assumption makes this one requested route unambiguous.


---

## Set 1 - Q16: Resume the paused thread with a decision (Medium)

**Original reference:** LangGraph-E-M-Set1, question 16.

A graph compiled with a checkpointer is paused inside `approved = interrupt("Approve report?")`. `original_thread_config` identifies that paused thread; `new_thread_config` identifies a different thread. Which call delivers the boolean `True` to the waiting interrupt and resumes the original execution?

A. `graph.invoke({"approved": True}, config=new_thread_config)`

B. `graph.invoke(None, config=new_thread_config)`

C. `graph.invoke(Command(resume=True), config=original_thread_config)`

D. `graph.invoke(Command(goto="publish"), config=original_thread_config)`

**Answer: C.**

**Why it works:** `Command(resume=True)` is the response to the interrupt. Using the same thread configuration finds the saved execution. In the resumed node, the waiting `interrupt(...)` call returns `True`.

**Why the other choices fail:**

- A starts or addresses a different thread and uses a plain state update instead of an interrupt response.
- B neither identifies the paused thread nor supplies its review decision.
- D supplies a routing command rather than the value requested by the interrupt.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

class State(TypedDict):
    approved: bool
    status: str

def review(state: State) -> dict:
    approved = interrupt("Approve report?")
    print("interrupt returned:", approved)
    return {"approved": approved, "status": "approved" if approved else "rejected"}

builder = StateGraph(State)
builder.add_node("review", review)
builder.add_edge(START, "review")
builder.add_edge("review", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "report-42"}}
paused = graph.invoke({"approved": False, "status": "waiting"}, config=config)
print("Prompt:", paused["__interrupt__"][0].value)
print("Paused status:", graph.get_state(config).values["status"])
result = graph.invoke(Command(resume=True), config=config)
print("Final state:", result)
```

**Expected output (observed locally):**

```text
Prompt: Approve report?
Paused status: waiting
interrupt returned: True
Final state: {'approved': True, 'status': 'approved'}
```

**Follow the key lines:**

1. The first `invoke` reaches `interrupt` and pauses. It has not yet executed the return statement, so the saved `status` remains `"waiting"`.
2. The interrupt payload is the prompt shown to the reviewer. The example prints only that prompt, avoiding generated internal identifiers.
3. The second `invoke` uses the **same** `config` and supplies the response with `Command(resume=True)`.
4. On resumption, the node starts again. When it reaches this interrupt, its saved response is available, so `approved` receives `True`.
5. `"approved" if approved else "rejected"` is ordinary Python logic that maps the boolean to a status. LangGraph does not decide what `True` means for your business process. If this example resumed with `False`, that expression would produce `"rejected"`.


---

## Set 1 - Q17: Code before an interrupt can run again (Medium)

**Original reference:** LangGraph-E-M-Set1, question 17.

A node first calls `create_ticket()`, then calls `interrupt()` to wait for approval. Every call to `create_ticket()` creates a new external ticket; the service does not deduplicate requests. The graph has a checkpointer. What risk remains when the paused node resumes?

A. The node can rerun the code before `interrupt`, creating a second ticket.

B. LangGraph automatically deletes the first ticket before resuming.

C. Resuming prevents every future call to `create_ticket`.

D. The checkpointer makes the external ticket creation happen exactly once.

**Answer: A.**

**Why it works:** Resuming an interrupted node restarts that node from its beginning. The ticket call is before the interrupt, so it runs again unless the application or external service prevents duplicate effects.

**Why the other choices fail:**

- B assumes LangGraph rolls back an action performed in another system.
- C assumes resumption disables an ordinary function, which it does not.
- D treats checkpointing and an external service as one transaction; checkpointing alone does not provide that guarantee.

**Standalone example — run locally; no API key required.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

# Simulated ticket service: this list stands in for an external system.
tickets: list[str] = []

def create_ticket() -> str:
    ticket_id = "T" + str(len(tickets) + 1)
    tickets.append(ticket_id)
    return ticket_id

class State(TypedDict):
    approved: bool
    ticket_id: str

def review(state: State) -> dict:
    ticket_id = create_ticket()
    print("Created ticket:", ticket_id)
    approved = interrupt("Approve report?")
    return {"approved": approved, "ticket_id": ticket_id}

builder = StateGraph(State)
builder.add_node("review", review)
builder.add_edge(START, "review")
builder.add_edge("review", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "ticket-demo"}}
graph.invoke({"approved": False, "ticket_id": ""}, config=config)
print("Tickets while paused:", tickets)
result = graph.invoke(Command(resume=True), config=config)
print("Tickets after resuming:", tickets)
print("Final state ticket:", result["ticket_id"])
```

**Expected output (observed locally):**

```text
Created ticket: T1
Tickets while paused: ['T1']
Created ticket: T2
Tickets after resuming: ['T1', 'T2']
Final state ticket: T2
```

**Follow the key lines:**

1. The `tickets` list is an explicitly **simulated external ticket service**. It is intentionally outside graph state, so its side effect remains visible while the graph is paused.
2. On the first run, `create_ticket` adds `T1`. `interrupt` then pauses before the node can return a state update.
3. Resuming runs `review` again from its first line. The second call adds `T2`, then the interrupt returns the saved approval.
4. The state finally records `T2`, but the simulated service still contains **both** tickets. Saving only the final state does not undo the earlier side effect.
5. A practical protection is a stable request key that the ticket service deduplicates. The example intentionally omits that protection to make the duplicate visible.


---

## Set 1 - Q18: Persistent checkpoints (Medium)

**Original reference:** LangGraph-E-M-Set1, question 18.

A report graph pauses for approval and currently uses `InMemorySaver`. The application must later resume the same report after the Python process has exited and restarted. Assume the new process runs a compatible graph definition. Which change is required?

A. Increase `recursion_limit` while keeping `InMemorySaver`.

B. Use `stream_mode="updates"` to retain checkpoints after shutdown.

C. Keep the same `thread_id`, with no change to the in-memory storage.

D. Use a persistent checkpointer and resume using the original thread identity.

**Answer: D.**

**Why D works:** The checkpoint data must survive the old process, and the thread ID must identify that saved execution. A database-backed checkpointer provides storage with a lifetime independent of the graph object.

**Why the others fail:** A changes the execution step limit, not storage. B streams updates to the caller; it does not persist them as resumable checkpoints. C supplies the right lookup key but cannot recover checkpoints lost with the old process.

**Standalone example — run locally; no API key.** Install `langgraph-checkpoint-sqlite` in addition to `langgraph`. This example closes one SQLite connection, creates a fresh checkpointer and graph, and resumes from the same database. It tests reopening saved storage **within one Python process**, not a full operating-system process restart. The temporary database is deleted when the example finishes.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    report: str
    approved: bool


def review(state: State):
    approved = interrupt("Approve this report?")
    return {"approved": approved}


def build_graph(checkpointer):
    builder = StateGraph(State)
    builder.add_node("review", review)
    builder.add_edge(START, "review")
    builder.add_edge("review", END)
    return builder.compile(checkpointer=checkpointer)


config = {"configurable": {"thread_id": "report-18"}}

with TemporaryDirectory() as folder:
    database_path = str(Path(folder) / "checkpoints.sqlite")

    with SqliteSaver.from_conn_string(database_path) as saver:
        graph = build_graph(saver)
        paused = graph.invoke(
            {"report": "Revenue grew 12%.", "approved": False}, config=config
        )
        print("Pause question:", paused["__interrupt__"][0].value)

    # The first database connection is now closed. Reopen the same database.
    with SqliteSaver.from_conn_string(database_path) as new_saver:
        new_graph = build_graph(new_saver)
        saved = new_graph.get_state(config)
        print("Reloaded report:", saved.values["report"])
        print("Pending node:", saved.next)
        result = new_graph.invoke(Command(resume=True), config=config)
        print("Approved:", result["approved"])
```

**Expected output — observed locally:**

```text
Pause question: Approve this report?
Reloaded report: Revenue grew 12%.
Pending node: ('review',)
Approved: True
```

**Follow the key lines:**

1. `SqliteSaver.from_conn_string(database_path)` opens the database used for checkpoints. The first invocation pauses at `interrupt(...)`; the decision has not been supplied yet.
2. Leaving the first `with` block closes that database connection. The saved checkpoint remains in the file while the temporary directory exists.
3. `new_saver` and `new_graph` are fresh objects. `get_state(config)` loads the saved report and shows `('review',)`, meaning review is still pending.
4. The original `thread_id` locates that paused execution. `Command(resume=True)` supplies the approval decision, so `interrupt(...)` now returns `True` and the node saves it.

For an application restart, use a database location that remains available after shutdown and recreate a compatible graph. `TemporaryDirectory` is only convenient cleanup for this local demonstration.


---

## Set 1 - Q19: Stopping a revision loop (Medium)

**Original reference:** LangGraph-E-M-Set1, question 19.

A report graph follows `draft → evaluate → revise → evaluate`. Evaluation may keep rejecting the draft. The application should retain the latest draft and request human review after at most two revisions. Which design meets that requirement?

A. Route every failed evaluation back to `revise`, without counting revisions.

B. Count revisions, route to escalation at the limit, and keep a reasonable `recursion_limit` safeguard.

C. Increase `recursion_limit` whenever it is reached, without changing routing.

D. Publish every draft regardless of its evaluation result.

**Answer: B.**

**Why B works:** The counter expresses the business rule: stop after two revisions and preserve the draft for a human. The recursion limit is a second guard against unintended graph loops.

**Why the others fail:** A has no deliberate stopping condition. C permits more graph steps without fixing the missing exit rule. D ignores the quality requirement and publishes a rejected draft.

**Standalone example — run locally; no API key.** The evaluator is explicitly simulated: it always returns `False` so the stopping behavior is easy to see. Draft strings are also ordinary Python sample data; no LLM is called.

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    draft: str
    revisions: int
    quality_ok: bool
    status: str


def draft_report(state: State):
    return {"draft": "Draft v0"}


def evaluate(state: State):
    # Simulated evaluator: every draft still needs work. No LLM is called.
    print("Evaluate:", state["draft"], "revisions =", state["revisions"])
    return {"quality_ok": False}


def choose_next(state: State):
    if state["quality_ok"]:
        return "publish"
    if state["revisions"] >= 2:
        return "escalate"
    return "revise"


def revise(state: State):
    next_revision = state["revisions"] + 1
    return {"revisions": next_revision, "draft": f"Draft v{next_revision}"}


def publish(state: State):
    return {"status": "published"}


def escalate(state: State):
    return {"status": "needs_human_review"}


builder = StateGraph(State)
builder.add_node("draft", draft_report)
builder.add_node("evaluate", evaluate)
builder.add_node("revise", revise)
builder.add_node("publish", publish)
builder.add_node("escalate", escalate)
builder.add_edge(START, "draft")
builder.add_edge("draft", "evaluate")
builder.add_conditional_edges(
    "evaluate", choose_next,
    {"publish": "publish", "revise": "revise", "escalate": "escalate"},
)
builder.add_edge("revise", "evaluate")
builder.add_edge("publish", END)
builder.add_edge("escalate", END)
graph = builder.compile()

result = graph.invoke(
    {"draft": "", "revisions": 0, "quality_ok": False, "status": "working"},
    config={"recursion_limit": 20},
)
print("Final revisions:", result["revisions"])
print("Final draft:", result["draft"])
print("Final status:", result["status"])
```

**Expected output — observed locally:**

```text
Evaluate: Draft v0 revisions = 0
Evaluate: Draft v1 revisions = 1
Evaluate: Draft v2 revisions = 2
Final revisions: 2
Final draft: Draft v2
Final status: needs_human_review
```

**Follow the key lines:**

1. The first evaluation sees `revisions = 0`. Because quality is unacceptable and the count is below two, `choose_next` selects `revise`.
2. `next_revision = state["revisions"] + 1` calculates the new count. Returning it replaces the previous integer; no reducer is needed for these sequential updates.
3. The graph evaluates `Draft v1`, revises once more, and then evaluates `Draft v2`. At that point the count is two, so the router selects `escalate` instead of another revision.
4. `escalate` changes only `status`. The latest draft and count stay in state and are available for human review.
5. `recursion_limit=20` limits graph execution steps. It does **not** mean twenty revisions, and reaching it would raise an execution error rather than perform the useful escalation shown here.

The simulated evaluator takes the failure path every time; the `publish` branch is included to show where a successful evaluation would route.


---

## Set 1 - Q20: Preferences shared across threads (Medium)

**Original reference:** LangGraph-E-M-Set1, question 20.

One user starts two independent report threads. Each thread needs its own report state, but both should read the same saved writing preference. Which design matches that requirement?

A. Assume each new thread automatically inherits the checkpoints of the other thread.

B. Give all users and reports one global `thread_id`.

C. Save preferences in a Store under a user-scoped namespace and explicitly read them when a report needs them.

D. Keep preferences only in a local variable inside the first report's node.

**Answer: C.**

**Why C works:** A Store can hold application data outside an individual thread's checkpoints. Both report threads can explicitly read the same user preference while keeping separate report state.

**Why the others fail:** A assumes inheritance that does not happen. B mixes separate report executions and users. D creates a temporary function variable, not shared application memory.

**Standalone example — run locally; no API key.** Report text is explicitly simulated with Python string formatting. `InMemoryStore` and `InMemorySaver` keep this demonstration small; both lose their contents when the process exits. Sharing data across threads is a different requirement from surviving process restarts.

```python
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


class State(TypedDict):
    user_id: str
    company: str
    draft: str


def write_report(state: State, runtime: Runtime):
    namespace = ("preferences", state["user_id"])
    item = runtime.store.get(namespace, "writing")
    style = item.value["style"] if item else "standard"
    print("Loaded style for", state["company"] + ":", style)
    # Simulated report text: no model is called.
    return {"draft": f"{state['company']}: {style} report"}


store = InMemoryStore()
store.put(("preferences", "user-7"), "writing", {"style": "concise"})

builder = StateGraph(State)
builder.add_node("write_report", write_report)
builder.add_edge(START, "write_report")
builder.add_edge("write_report", END)
graph = builder.compile(checkpointer=InMemorySaver(), store=store)

first_config = {"configurable": {"thread_id": "report-A"}}
second_config = {"configurable": {"thread_id": "report-B"}}

first = graph.invoke(
    {"user_id": "user-7", "company": "Acme", "draft": ""}, config=first_config
)
second = graph.invoke(
    {"user_id": "user-7", "company": "Beta", "draft": ""}, config=second_config
)
print("First draft:", first["draft"])
print("Second draft:", second["draft"])
print("First thread company:", graph.get_state(first_config).values["company"])
print("Second thread company:", graph.get_state(second_config).values["company"])
```

**Expected output — observed locally:**

```text
Loaded style for Acme: concise
Loaded style for Beta: concise
First draft: Acme: concise report
Second draft: Beta: concise report
First thread company: Acme
Second thread company: Beta
```

**Follow the key lines:**

1. `store.put(("preferences", "user-7"), "writing", {"style": "concise"})` saves one item. The tuple is its namespace, `writing` is its key, and the dictionary is its value.
2. `compile(..., store=store)` makes that Store available to nodes through `runtime.store`. Merely adding a Store does not make nodes read it automatically.
3. `runtime.store.get(namespace, "writing")` retrieves the item. `item.value["style"]` extracts `concise`; the fallback handles a missing preference.
4. The calls use different thread IDs, `report-A` and `report-B`, but the same user namespace. Both receive `concise` while their checkpointed companies remain `Acme` and `Beta` respectively.

Here `user_id` is trusted sample input. In an application, use the authenticated user's identity to choose the namespace; a namespace alone is not an authorization check.

---

## Set 2 - Q01: Pass a database client through runtime context (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `01`.

A graph retrieves a company's revenue. Several nodes need the same live database client for this invocation. The client is an execution dependency; the company name and revenue are business state. Where should the application supply the client so nodes can use it without making it a normal state field?

A. Put the client in a normal state field so it is included in checkpointed business data.

B. Supply the client through runtime context and let nodes read it from `runtime.context`.

C. Put the client in the text of a system message.

D. Create a graph node whose name contains the connection identifier.

**Answer: B. Supply the client through runtime context.**

**Why this works:** A node can receive a `Runtime` object alongside its state. The caller supplies the context for this invocation; the node reads the client from that context. The node returns only the business result, here `revenue`. Context is not a normal state channel and does not automatically become part of the returned business state.

**Why the other choices fail:**

- **A:** A live connection belongs to execution resources. Treating it as business state creates serialization and lifecycle problems.
- **C:** A system message carries model-facing content. It does not inject a live client into Python node code.
- **D:** A node name identifies a step. Naming a step after a connection does not supply that connection to other nodes.

**Standalone Python example — tested locally.** The database is simulated with a local Python object. No database server or model API is contacted.

```python
from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime


class State(TypedDict):
    company: str
    revenue: int


class SimulatedDatabase:
    def __init__(self):
        self.rows = {"Acme": 120}

    def get_revenue(self, company):
        return self.rows[company]


@dataclass
class Context:
    db: SimulatedDatabase


def retrieve(state: State, runtime: Runtime[Context]):
    revenue = runtime.context.db.get_revenue(state["company"])
    print("lookup:", state["company"], "->", revenue)
    return {"revenue": revenue}


builder = StateGraph(State, context_schema=Context)
builder.add_node("retrieve", retrieve)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", END)
graph = builder.compile()

db = SimulatedDatabase()  # Local stand-in; no database server is contacted.
result = graph.invoke({"company": "Acme"}, context=Context(db=db))
print("result:", result)
print("db in business state:", "db" in result)
```

**Expected output (observed locally):**

```text
lookup: Acme -> 120
result: {'company': 'Acme', 'revenue': 120}
db in business state: False
```

**Read the key lines slowly:**

1. `Context` declares one dependency, `db`. The dataclass gives us a small container for the actual object.
2. `StateGraph(State, context_schema=Context)` declares both interfaces: workflow data in `State`, invocation dependencies in `Context`.
3. `context=Context(db=db)` supplies the live object when the graph runs. Inside `retrieve`, `runtime.context.db` is that same object.
4. `get_revenue("Acme")` looks up `120` in the local dictionary. Returning `{"revenue": revenue}` writes `120` into state; it does not write the client into state.
5. The final `False` checks that `db` is absent from the business result. Recreate or supply the dependency again for a later invocation or resumed run as needed.


---

## Set 2 - Q02: Return only the public output fields (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `02`.

A graph uses `company`, `evidence`, and `review_notes` while preparing `final_report`. Nodes must keep using those internal fields. The ordinary return value of `graph.invoke(...)` should contain only `final_report`. Which design expresses that output contract? This question concerns returned fields, not access control for checkpoints or traces.

A. Attach a checkpointer and rely on it to hide intermediate fields from the return value.

B. Delete the internal fields from every state schema before the workflow runs.

C. Prefix internal field names with underscores and rely on automatic output filtering.

D. Keep the internal state schema and supply an output schema containing only `final_report`.

**Answer: D. Keep the internal state and define a narrower output schema.**

**Why this works:** The graph can work with a broad internal state while exposing a smaller final result. `output_schema=Output` selects which state fields are returned through this ordinary output interface.

**Why the other choices fail:**

- **A:** A checkpointer saves execution state; it does not define the public output field list.
- **B:** Removing the working fields prevents nodes from passing the data they need through the declared state.
- **C:** Underscores are a naming convention here, not an output-filtering rule.

**Standalone Python example — tested locally.** Evidence and the report are built from local strings; no retrieval service or LLM is called.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    company: str
    evidence: str
    review_notes: str
    final_report: str


class Output(TypedDict):
    final_report: str


def retrieve(state: State):
    evidence = f"{state['company']}: revenue 120"
    print("retrieve returns:", {"evidence": evidence})
    return {"evidence": evidence}


def draft(state: State):
    print("draft reads evidence:", state["evidence"])
    return {
        "review_notes": "Revenue checked",
        "final_report": state["evidence"] + ".",
    }


builder = StateGraph(State, output_schema=Output)
builder.add_node("retrieve", retrieve)
builder.add_node("draft", draft)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
graph = builder.compile()

result = graph.invoke({"company": "Acme"})
print("public result:", result)
```

**Expected output (observed locally):**

```text
retrieve returns: {'evidence': 'Acme: revenue 120'}
draft reads evidence: Acme: revenue 120
public result: {'final_report': 'Acme: revenue 120.'}
```

**Read the key lines slowly:**

1. `State` includes all fields used while preparing the report. `Output` includes only `final_report`.
2. `retrieve` returns evidence. LangGraph adds it to internal state before `draft` runs, so `draft` can read it.
3. `draft` returns both an internal review note and the final report. Both are valid state updates.
4. `output_schema=Output` makes the final printed result contain only `final_report`. It does not erase internal data from authorized checkpoint or tracing access.


---

## Set 2 - Q03: Map fields when calling a child graph (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `03`.

A parent graph uses fields `question` and `answer`. A reusable child graph uses `query` and `response`; it shares no field names with the parent. Given parent input `{"question": "What was revenue?"}`, how should a parent node call the child and return the child's response as `answer` without changing either schema?

A. Use a wrapper node that maps `question` to `query`, invokes the child, and maps `response` to `answer`.

B. Give both graphs the same `thread_id` and rely on it to translate field names.

C. Define a reducer that globally renames the parent state keys before each step.

D. Add the child directly and rely on automatic semantic matching between the field names.

**Answer: A. Use a wrapper node with explicit input and output mappings.**

**Why this works:** The wrapper is ordinary Python code at the boundary between two interfaces. It creates the child's input dictionary, calls the child, and returns a valid parent update. No automatic field translation is assumed.

**Why the other choices fail:**

- **B:** A thread identifier selects persisted execution state. It does not rename fields.
- **C:** A field reducer combines updates for a state field; it is not a global schema translator.
- **D:** LangGraph does not infer that `question` means `query` or that `response` means `answer`.

**Standalone Python example — tested locally.** The child uses a simulated answer function that joins strings. No model API is called.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class ChildState(TypedDict):
    query: str
    response: str


def answer_query(state: ChildState):
    return {"response": "Answer to: " + state["query"]}


child_builder = StateGraph(ChildState)
child_builder.add_node("answer_query", answer_query)
child_builder.add_edge(START, "answer_query")
child_builder.add_edge("answer_query", END)
child = child_builder.compile()


class ParentState(TypedDict):
    question: str
    answer: str


def call_child(state: ParentState):
    child_input = {"query": state["question"]}
    print("child input:", child_input)
    child_result = child.invoke(child_input)
    print("child response:", child_result["response"])
    return {"answer": child_result["response"]}


parent_builder = StateGraph(ParentState)
parent_builder.add_node("call_child", call_child)
parent_builder.add_edge(START, "call_child")
parent_builder.add_edge("call_child", END)
parent = parent_builder.compile()

print("parent result:", parent.invoke({"question": "What was revenue?"}))
```

**Expected output (observed locally):**

```text
child input: {'query': 'What was revenue?'}
child response: Answer to: What was revenue?
parent result: {'question': 'What was revenue?', 'answer': 'Answer to: What was revenue?'}
```

**Read the key lines slowly:**

1. `ChildState` and `ParentState` deliberately use different names. Each graph can retain its own interface.
2. `child_input = {"query": state["question"]}` reads the parent question and places its value under the child key.
3. `child.invoke(child_input)` executes the child graph. The returned dictionary contains its `response`.
4. `return {"answer": child_result["response"]}` maps the child response back into the parent. The parent result keeps its original `question` and adds `answer`.


---

## Set 2 - Q04: Route from a child to its parent (Medium)

**Original reference: LangGraph-M-H-Set2, Q04.**

A parent graph contains nodes named `child` and `finalize`. Inside `child`, a node named `handoff` must send execution to the parent's `finalize` node. There is no `finalize` node inside the child. The command only changes routing; it does not update shared state. Which return value selects the correct graph and destination?

A. `Command(goto="finalize")`

B. `Command(update={"graph": "parent", "next": "finalize"})`

C. `Command(goto="finalize", graph=Command.PARENT)`

D. `Send("finalize", {"graph": "parent"})`

**Answer: C. `Command(goto="finalize", graph=Command.PARENT)`**

**Why it works:** `goto` names the destination. `graph=Command.PARENT` says to find that destination in the nearest parent graph. The child hands control back to that parent.

**Why the others fail:**

- **A:** Without parent scope, the destination belongs to the current child graph, which has no `finalize` node.
- **B:** Keys inside `update` describe state changes. Naming keys `graph` and `next` does not turn them into routing instructions.
- **D:** A `graph` entry inside a `Send` payload is ordinary task data; it does not select the parent graph.

**Standalone example - tested locally; no API key or simulated service is involved.**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command


class State(TypedDict):
    report: str


def handoff(state: State):
    print("child input:", state["report"])
    print("handoff target:", "parent.finalize")
    return Command(goto="finalize", graph=Command.PARENT)


def finalize(state: State):
    print("parent finalize input:", state["report"])
    return {"report": state["report"] + " | finalized"}


child_builder = StateGraph(State)
child_builder.add_node("handoff", handoff)
child_builder.add_edge(START, "handoff")
child = child_builder.compile()

parent_builder = StateGraph(State)
parent_builder.add_node("child", child)
parent_builder.add_node("finalize", finalize)
parent_builder.add_edge(START, "child")
parent_builder.add_edge("finalize", END)
parent = parent_builder.compile()

print("final state:", parent.invoke({"report": "Draft A"}))
```

**Expected output - observed locally:**

```text
child input: Draft A
handoff target: parent.finalize
parent finalize input: Draft A
final state: {'report': 'Draft A | finalized'}
```

**Read the key lines slowly:**

1. `State` has one field: `report`. Both graphs use that same simple field so this example needs no input translation.
2. `child_builder.add_edge(START, "handoff")` makes `handoff` the child's first node. It reads `"Draft A"` and returns a routing command.
3. `Command.PARENT` changes where LangGraph looks for `finalize`. It does not rename any state field or alter the report text.
4. `parent_builder.add_node("child", child)` installs the compiled child as one parent node. The parent also has its own `finalize` node.
5. The parent receives the handoff and runs `finalize` with `report="Draft A"`. That node returns the sole state update: `report="Draft A | finalized"`.
6. Only `finalize` has an edge to `END`. The child has no ordinary outgoing edge to the parent's destination; the explicit command supplies that handoff.


---

## Set 2 - Q05: Build a cache key that separates tenants (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `05`.

A retrieval node receives `tenant_id`, `corpus_version`, and `query`. Those three values determine which authorized local corpus it searches and what evidence it returns. A custom cache key currently uses only `query`, so tenants A and B collide when both ask for `"revenue"`. Which correction prevents that collision and also avoids reusing a result after the corpus version changes?

A. Include `tenant_id`, `corpus_version`, and `query` in the cache key.

B. Keep the key unchanged and add tenant names only to trace tags.

C. Keep the key unchanged and increase the cache time-to-live.

D. Keep the key unchanged and attach a graph checkpointer.

**Answer: A. Include every stated factor that changes the result in the cache key.**

**Why this works:** The corrected key distinguishes A's request from B's request and distinguishes corpus versions. Repeating A's same request can still reuse A's cached result. This example assumes authorization has already established which tenant corpus the request may access.

**Why the other choices fail:**

- **B:** Trace tags do not change the custom key used for the cache lookup.
- **C:** A longer lifetime keeps a mistaken cache entry around longer; it does not separate requests.
- **D:** Checkpointing and node caching serve different purposes. Saving graph state does not repair this cache-key collision.

**Standalone Python example — tested locally.** Retrieval is simulated with a local corpus dictionary. The node cache is the real LangGraph in-memory cache.

```python
import json
from typing import TypedDict
from langgraph.cache.memory import InMemoryCache
from langgraph.graph import StateGraph, START, END
from langgraph.types import CachePolicy


class State(TypedDict):
    tenant_id: str
    corpus_version: str
    query: str
    evidence: str


corpora = {("A", "v1"): "A revenue: 120", ("B", "v1"): "B revenue: 90"}
retrieval_calls = 0


def cache_key(state: State):
    return json.dumps([state["tenant_id"], state["corpus_version"], state["query"]])


def retrieve(state: State):
    global retrieval_calls
    retrieval_calls += 1
    return {"evidence": corpora[(state["tenant_id"], state["corpus_version"])]}


builder = StateGraph(State)
builder.add_node("retrieve", retrieve, cache_policy=CachePolicy(key_func=cache_key))
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", END)
graph = builder.compile(cache=InMemoryCache())

for tenant in ["A", "B", "A"]:
    request = {"tenant_id": tenant, "corpus_version": "v1", "query": "revenue"}
    print("cache key:", cache_key(request))
    print("evidence:", graph.invoke(request)["evidence"])
print("actual retrieval calls:", retrieval_calls)
```

**Expected output (observed locally):**

```text
cache key: ["A", "v1", "revenue"]
evidence: A revenue: 120
cache key: ["B", "v1", "revenue"]
evidence: B revenue: 90
cache key: ["A", "v1", "revenue"]
evidence: A revenue: 120
actual retrieval calls: 2
```

**Read the key lines slowly:**

1. `cache_key` converts the three relevant values into one unambiguous JSON string. Tenant A and tenant B therefore produce different keys.
2. `CachePolicy(key_func=cache_key)` tells this node how to identify equivalent requests. `compile(cache=InMemoryCache())` supplies the cache storage.
3. The first A request runs `retrieve`, which reads `"A revenue: 120"`. The B request has a different key, so it runs retrieval and reads `"B revenue: 90"`.
4. The last A request repeats its earlier key. The graph reuses the cached node output, so the counter finishes at `2`, not `3`.
5. This example counts local function calls only. A correctly scoped key complements the application's authorization checks; it does not replace them.


---

## Set 2 - Q06: Read a parallel step’s input state (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `06`.

Nodes A and B are both scheduled from `START`, so they run in the same graph superstep. Their input state has `count=0`. A returns `{"count": 1}`. B only reads the state supplied to it; neither node mutates shared objects. Even if A finishes first, what value does B read for `count` in that same superstep?

A. `1`, because a node publishes its returned update to peer nodes immediately when it finishes.

B. `0`, because both nodes read this step's input state and returned updates apply at the step boundary.

C. Either `0` or `1`, determined only by operating-system scheduling.

D. A concurrent-read error, because two parallel nodes cannot read the same field.

**Answer: B. B reads `0` from the shared step input.**

**Why this works:** Within a superstep, nodes read the state available at that step's start. A's returned update becomes part of the next state after the step's work completes. Finishing earlier does not change the state snapshot already supplied to B.

**Why the other choices fail:**

- **A:** Returned state updates are not immediate writes into a peer node's supplied state.
- **C:** Under the stated conditions, node completion timing does not change this read.
- **D:** Parallel reads are allowed. Conflicting writes to one field without a reducer are a different issue.

**Standalone Python example — tested locally.** This is a real two-branch LangGraph example. It does not depend on forcing a particular completion order.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    count: int
    b_saw: int


def node_a(state: State):
    return {"count": state["count"] + 1}


def node_b(state: State):
    return {"b_saw": state["count"]}


builder = StateGraph(State)
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_edge(START, "a")
builder.add_edge(START, "b")
builder.add_edge("a", END)
builder.add_edge("b", END)
graph = builder.compile()

print("step input count:", 0)
result = graph.invoke({"count": 0})
print("B read count:", result["b_saw"])
print("count after the step:", result["count"])
```

**Expected output (observed locally):**

```text
step input count: 0
B read count: 0
count after the step: 1
```

**Read the key lines slowly:**

1. Two separate edges from `START` schedule `a` and `b` together. There is no edge from `a` to `b`.
2. `node_a` reads `0` and returns a count update of `1`. `node_b` reads the same step input, `0`, and returns it under a different field, `b_saw`.
3. Only A writes `count`, and only B writes `b_saw`, so the example has no conflicting writes.
4. At the end, `count` is `1`, while `b_saw` records B's earlier read of `0`. To make B consume A's new count, schedule B after A in a later step.


---

## Set 2 - Q07: Check whether a merge is associative (Easy)

**Original reference:** `LangGraph-M-H-Set2`, question `07`.

A numeric merge function is defined as `merge(a, b) = a - b`. You want the answer to remain the same when partial results are grouped differently. Compare `merge(merge(10, 3), 2)` with `merge(10, merge(3, 2))`. Which statement is correct? This question tests grouping; it does not assume a particular graph scheduling order.

A. The merge is associative because it accepts two numbers.

B. The merge becomes associative when the graph uses a checkpointer.

C. The merge becomes associative when all workers use integers.

D. The merge is not associative: the two groupings produce `5` and `9`.

**Answer: D. The different groupings produce `5` and `9`.**

**Why this works:** Associative means that changing parentheses does not change the result. Here `(10 - 3) - 2 = 5`, whereas `10 - (3 - 2) = 9`. One counterexample is enough to show that subtraction does not have that property.

**Why the other choices fail:**

- **A:** Accepting two arguments makes a function binary; it does not make it associative.
- **B:** Saving state does not change how subtraction works.
- **C:** Both calculations already use integers and still give different answers.

**Standalone Python example — tested locally.** This standalone example uses Python only. No LangGraph setup or API key is needed to check the algebra.

```python
def merge(a, b):
    return a - b


first_left = merge(10, 3)
left = merge(first_left, 2)
first_right = merge(3, 2)
right = merge(10, first_right)

print("left inner: 10 - 3 =", first_left)
print("left result: 7 - 2 =", left)
print("right inner: 3 - 2 =", first_right)
print("right result: 10 - 1 =", right)
print("same result:", left == right)
```

**Expected output (observed locally):**

```text
left inner: 10 - 3 = 7
left result: 7 - 2 = 5
right inner: 3 - 2 = 1
right result: 10 - 1 = 9
same result: False
```

**Read the key lines slowly:**

1. `first_left` calculates the inner call on the left: `10 - 3`, which is `7`. Subtracting `2` next gives `5`.
2. `first_right` calculates the inner call on the right: `3 - 2`, which is `1`. Subtracting that value from `10` gives `9`.
3. `left == right` prints `False`. A deterministic function can still depend on how its calls are grouped.
4. When designing a reducer, check the needed merge properties with real values. For a total of independent numeric contributions, addition has the grouping property shown missing here.


---

## Set 2 - Q08: Assemble parallel results in business order (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `08`.

Two parallel workers write report sections. The requested order is overview at index `0`, then finance at index `1`. Either worker may finish first, and node names or graph structure may change. Which design makes the assembled report follow the requested section order?

A. Return a unique requested section index with each section and sort by that index before assembly.

B. Concatenate sections in whichever order workers happen to finish.

C. Rename the worker nodes alphabetically and treat that naming order as the report specification.

D. Give every section the same index and concatenate the collected values.

**Answer: A. Carry the requested section index and sort explicitly during assembly.**

**Why this works:** The index describes the report's required order independently of execution. Workers can run in parallel; assembly uses their indexes to arrange their results. The example uses unique indexes to avoid ambiguous ties.

**Why the other choices fail:**

- **B:** Completion order reflects execution timing, which does not define the report's requested order.
- **C:** Node names are implementation details and may change without changing the report specification.
- **D:** Identical indexes discard the information needed to distinguish the two requested positions.

**Standalone Python example — tested locally.** The two workers generate local strings. No model API is called; parallel collection uses a real LangGraph reducer.

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    sections: Annotated[list[tuple[int, str]], operator.add]
    report: str


def write_finance(state: State):
    return {"sections": [(1, "Revenue: 120.")]}


def write_overview(state: State):
    return {"sections": [(0, "Company: Acme.")]}


def assemble(state: State):
    ordered = sorted(state["sections"], key=lambda item: item[0])
    print("sections by requested index:", ordered)
    report = " ".join(text for index, text in ordered)
    return {"report": report}


builder = StateGraph(State)
builder.add_node("finance", write_finance)
builder.add_node("overview", write_overview)
builder.add_node("assemble", assemble)
builder.add_edge(START, "finance")
builder.add_edge(START, "overview")
builder.add_edge(["finance", "overview"], "assemble")
builder.add_edge("assemble", END)
graph = builder.compile()

print("requested order:", [0, 1])
result = graph.invoke({"sections": []})
print("report:", result["report"])
```

**Expected output (observed locally):**

```text
requested order: [0, 1]
sections by requested index: [(0, 'Company: Acme.'), (1, 'Revenue: 120.')]
report: Company: Acme. Revenue: 120.
```

**Read the key lines slowly:**

1. `sections` uses `operator.add` so each worker can contribute a one-item list to the same field.
2. Finance returns `(1, "Revenue: 120.")`; overview returns `(0, "Company: Acme.")`. Each tuple keeps the requested index beside its text.
3. `add_edge(["finance", "overview"], "assemble")` makes assembly wait for both branches.
4. `sorted(..., key=lambda item: item[0])` orders the collected results by index. `join` then uses only their text, producing overview before finance.
5. The printed intermediate list is deliberately sorted for inspection. It does not assert that raw collection order follows either completion time or the report order.


---

## Set 2 - Q09: Apply a reducer during a manual state update (Medium)

**Original reference:** `LangGraph-M-H-Set2`, question `09`.

A graph uses a checkpointer and declares `audit` as a list with the `operator.add` reducer. Its current checkpoint contains `audit=["old"]`. You call `graph.update_state(config, {"audit": ["corrected"]})` and use the returned configuration to inspect the new checkpoint. What is the new `audit` value?

A. `["corrected"]`, because manual updates bypass field reducers.

B. `[]`, because manual updates clear existing accumulated values first.

C. `["old", "corrected"]`, because the declared reducer also applies to manual updates.

D. `["old"]`, because checkpointed state cannot be updated.

**Answer: C. The new checkpoint contains `["old", "corrected"]`.**

**Why this works:** `update_state` applies state-update rules, including the declared reducer. `operator.add` concatenates the existing list and the supplied list. The update creates a new checkpoint; the previously saved checkpoint still contains its earlier value.

**Why the other choices fail:**

- **A:** A manual update does not automatically bypass a reducer.
- **B:** No implicit clearing happens before this update.
- **D:** A new checkpoint can be created with updated state. Historical state is not rewritten in place.

**Standalone Python example — tested locally.** This uses a real in-memory checkpointer. It demonstrates saved versions within one Python process.

```python
import operator
from typing import Annotated, TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    audit: Annotated[list[str], operator.add]


def keep_state(state: State):
    return {}


builder = StateGraph(State)
builder.add_node("keep_state", keep_state)
builder.add_edge(START, "keep_state")
builder.add_edge("keep_state", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "audit-1"}}

graph.invoke({"audit": ["old"]}, config)
before = graph.get_state(config)
print("before:", before.values["audit"])
updated_config = graph.update_state(config, {"audit": ["corrected"]})
print("after:", graph.get_state(updated_config).values["audit"])
print("old checkpoint:", graph.get_state(before.config).values["audit"])
```

**Expected output (observed locally):**

```text
before: ['old']
after: ['old', 'corrected']
old checkpoint: ['old']
```

**Read the key lines slowly:**

1. `Annotated[list[str], operator.add]` means updates to `audit` concatenate lists rather than replace the current list.
2. The first invocation supplies `["old"]`. `before` captures the resulting checkpoint, including its exact checkpoint configuration.
3. `update_state` combines `["old"]` with `["corrected"]` and returns the configuration for a new checkpoint.
4. `get_state(updated_config)` reads the combined value. `get_state(before.config)` still reads `["old"]` because that configuration identifies the historical checkpoint.


---

## Set 2 - Q10: Treating a manual edit as draft output (Medium)

**Original reference:** LangGraph-M-H-Set2, question 10.

A graph has the linear route `START -> retrieve -> draft -> evaluate -> END`. It uses a checkpointer and is paused immediately before `evaluate`. Its saved draft is wrong.

You call `graph.update_state(config, {"draft": "Human-corrected draft"}, as_node="draft")`, then resume with `graph.invoke(None, edited_config)`, where `edited_config` is the configuration returned by `update_state`.

What does `as_node="draft"` mean here?

A. Rename the edited state field to `draft`, regardless of the supplied update keys.

B. Execute the `draft` function immediately inside `update_state`.

C. Mark the graph complete because a human supplied the update.

D. Treat the update as output from `draft`, so the next work follows its edge to `evaluate`.

**Answer: D. Treat the update as output from `draft`, then continue toward `evaluate`.**

`as_node` identifies the execution position represented by the edit. The new checkpoint contains the corrected draft and schedules the work after `draft`. It does not call the `draft` function.

- **A fails:** the supplied dictionary controls field names; `as_node` does not rename them.
- **B fails:** attributing an update to a node does not execute that node.
- **C fails:** a manual edit does not imply that the workflow has finished.

**Standalone example — run locally; no API key required.** The static pause before `evaluate` makes the editing point explicit.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    evidence: str
    draft: str
    verdict: str

calls = []

def retrieve(state: State):
    calls.append('retrieve')
    return {'evidence': 'Revenue grew 12%.'}

def draft(state: State):
    calls.append('draft')
    return {'draft': 'Original draft: ' + state['evidence']}

def evaluate(state: State):
    calls.append('evaluate')
    return {'verdict': 'Reviewed: ' + state['draft']}

builder = StateGraph(State)
builder.add_node('retrieve', retrieve)
builder.add_node('draft', draft)
builder.add_node('evaluate', evaluate)
builder.add_edge(START, 'retrieve')
builder.add_edge('retrieve', 'draft')
builder.add_edge('draft', 'evaluate')
builder.add_edge('evaluate', END)
graph = builder.compile(checkpointer=InMemorySaver(), interrupt_before=['evaluate'])
config = {'configurable': {'thread_id': 'edit-demo'}}
graph.invoke({'evidence': '', 'draft': '', 'verdict': ''}, config)
print('Before edit:', graph.get_state(config).values['draft'])
print('Calls before edit:', calls)
edited_config = graph.update_state(config, {'draft': 'Human-corrected draft'}, as_node='draft')
print('After edit:', graph.get_state(edited_config).values['draft'])
print('Calls after edit:', calls)
print('Next nodes:', graph.get_state(edited_config).next)
result = graph.invoke(None, edited_config)
print('Final verdict:', result['verdict'])
print('Final calls:', calls)
```

**Expected output — captured from the local run:**

```text
Before edit: Original draft: Revenue grew 12%.
Calls before edit: ['retrieve', 'draft']
After edit: Human-corrected draft
Calls after edit: ['retrieve', 'draft']
Next nodes: ('evaluate',)
Final verdict: Reviewed: Human-corrected draft
Final calls: ['retrieve', 'draft', 'evaluate']
```

**Follow the key lines:**

1. Each node returns only the fields it changes. The `calls` list is diagnostic data used to show which Python functions ran.
2. `interrupt_before=['evaluate']` pauses after `draft` has produced its output and before evaluation starts.
3. `update_state(..., as_node='draft')` saves the human edit as though it were draft output. The unchanged `calls` list proves that this call does not execute a node function.
4. The snapshot's `next` value is `('evaluate',)`. That is the next scheduled node, not a field in business state.
5. `invoke(None, edited_config)` continues from the newly returned checkpoint configuration. `evaluate` reads the corrected draft and produces the final verdict.


---

## Set 2 - Q11: Replaying a drafting node (Medium)

**Original reference:** LangGraph-M-H-Set2, question 11.

A checkpointer saved a graph immediately before its `draft` node. That node normally calls an LLM. There is no node cache. You later replay from that saved checkpoint by invoking the graph with `None` and that checkpoint's configuration.

Which statement is accurate about the replayed draft?

A. It must match the original draft because the checkpoint fixes all future responses.

B. It may differ because the drafting node executes again and can call the model again.

C. It must match unless you change the `thread_id`.

D. It is read directly from the original final result without running the drafting node.

**Answer: B. The drafting node executes again, so its new response may differ.**

A checkpoint preserves work up to the selected point. Replaying continues execution after that point. It does not turn future model calls into recordings of the first run. A real model might produce the same text or different text; neither outcome is guaranteed by checkpointing.

- **A fails:** saved past state does not determine future external responses.
- **C fails:** thread identity identifies saved execution state; it does not force deterministic model responses.
- **D fails:** viewing a saved final snapshot and replaying execution are different operations.

**Standalone example — run locally; no API key required.** The model is simulated with a counter so the second call is visible. No real LLM was called or tested.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    evidence: str
    draft: str

# Simulated model: no provider or API key is used.
model_calls = 0

def retrieve(state: State):
    return {'evidence': 'Revenue grew 12%.'}

def draft(state: State):
    global model_calls
    model_calls += 1
    return {'draft': f'Simulated draft {model_calls}: ' + state['evidence']}

builder = StateGraph(State)
builder.add_node('retrieve', retrieve)
builder.add_node('draft', draft)
builder.add_edge(START, 'retrieve')
builder.add_edge('retrieve', 'draft')
builder.add_edge('draft', END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {'configurable': {'thread_id': 'replay-demo'}}
first = graph.invoke({'evidence': '', 'draft': ''}, config)
print('First result:', first['draft'])
# Choose the saved point whose next node is draft.
before_draft = next(s for s in graph.get_state_history(config) if s.next == ('draft',))
print('Saved evidence:', before_draft.values['evidence'])
print('Saved next nodes:', before_draft.next)
second = graph.invoke(None, before_draft.config)
print('Replayed result:', second['draft'])
print('Simulated model calls:', model_calls)
```

**Expected output — captured from the local run:**

```text
First result: Simulated draft 1: Revenue grew 12%.
Saved evidence: Revenue grew 12%.
Saved next nodes: ('draft',)
Replayed result: Simulated draft 2: Revenue grew 12%.
Simulated model calls: 2
```

**Follow the key lines:**

1. `retrieve` writes the evidence. The next step is `draft`, so LangGraph saves a checkpoint with `next == ('draft',)`.
2. `draft` increases `model_calls` each time its Python function executes. This is an intentionally simulated response, not a model configuration.
3. The first invocation completes the graph and produces simulated draft 1.
4. `get_state_history(config)` exposes saved checkpoints. The `next(...)` expression chooses the one immediately before `draft`.
5. `invoke(None, before_draft.config)` executes the work after that saved point. The same evidence is reused, but `draft` runs again, producing simulated draft 2.
6. The final count of 2 verifies re-execution. It does not claim that every real model call must return different text.


---

## Set 2 - Q13: Retrying temporary failures selectively (Medium)

**Original reference:** LangGraph-M-H-Set2, question 13.

A retrieval node can fail in two ways: `ConnectionError` means a temporary connection outage; `ValueError` means the supplied document ID is malformed. Repeating the same malformed ID will never fix it.

Which policy is appropriate?

A. Retry `ConnectionError` a bounded number of times; let `ValueError` reach the caller for correction.

B. Catch both exceptions and return an empty successful retrieval result.

C. Retry both exception types forever because retrieval is read-only.

D. Delay every failure equally and remove the attempt limit.

**Answer: A. Retry known temporary failures with a limit; surface malformed input.**

A temporary connection failure may resolve on a later attempt. Malformed input needs correction. The retry policy should express that difference instead of converting failures into success or repeating them indefinitely.

- **B fails:** empty evidence would conceal a failed operation and could be mistaken for a valid empty search.
- **C fails:** read-only work still consumes time and resources, and the malformed input remains malformed.
- **D fails:** a delay alone neither classifies the error nor bounds repeated attempts.

**Standalone example — run locally; no API key required.** The outage and evidence are simulated locally. A one-millisecond retry delay keeps this demonstration quick.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    document_id: str
    evidence: str

attempts = {}

def retrieve(state: State):
    document_id = state['document_id']
    attempts[document_id] = attempts.get(document_id, 0) + 1
    print(f'Attempt {attempts[document_id]} for {document_id}')
    if not document_id.startswith('doc-'):
        raise ValueError('Document ID must start with doc-')
    if attempts[document_id] == 1:
        raise ConnectionError('Simulated temporary outage')
    return {'evidence': 'Revenue grew 12%.'}

builder = StateGraph(State)
builder.add_node('retrieve', retrieve, retry_policy=RetryPolicy(
    max_attempts=2,
    retry_on=ConnectionError,
    initial_interval=0.001,
    jitter=False,
))
builder.add_edge(START, 'retrieve')
builder.add_edge('retrieve', END)
graph = builder.compile()
result = graph.invoke({'document_id': 'doc-1', 'evidence': ''})
print('Evidence:', result['evidence'])
try:
    graph.invoke({'document_id': 'bad-id', 'evidence': ''})
except ValueError as error:
    print('Caller received:', str(error))
print('Attempt counts:', attempts)
```

**Expected output — captured from the local run:**

```text
Attempt 1 for doc-1
Attempt 2 for doc-1
Evidence: Revenue grew 12%.
Attempt 1 for bad-id
Caller received: Document ID must start with doc-
Attempt counts: {'doc-1': 2, 'bad-id': 1}
```

**Follow the key lines:**

1. `attempts` records each invocation of the retrieval function. The counter lets you see actual retry behavior.
2. Validation happens before the simulated outage. `bad-id` raises `ValueError` immediately, and repeating it would not help.
3. For `doc-1`, the first attempt raises `ConnectionError`; the second returns evidence.
4. `retry_on=ConnectionError` selects the exception type that LangGraph should retry. `max_attempts=2` means two total attempts, including the first call.
5. `initial_interval=0.001` sets the small first delay. `jitter=False` removes random variation from this example's delay; it does not affect which errors qualify.
6. The caller catches `ValueError` outside the graph invocation and displays it. The output shows two attempts for the temporary outage and only one for the malformed ID.


---

## Set 2 - Q14: Keep saved node names compatible (Medium)

**Original reference: LangGraph-M-H-Set2, Q14.**

A checkpointed execution has paused immediately before the graph node named `legal_review`. Its saved next-node name is still `legal_review`. A new graph definition deletes that name and adds `review_v2` instead. No migration has been performed. What compatibility issue must the developer address?

A. The checkpointer will automatically infer that `review_v2` replaces `legal_review`.

B. Saved execution positions can still reference `legal_review`; preserve that node identity or migrate the affected runs.

C. Node names affect diagrams only, so every saved execution will resume unchanged.

D. Removing `legal_review` automatically records a human approval for each paused report.

**Answer: B. Saved execution positions can still reference `legal_review`; preserve that node identity or migrate the affected runs.**

**Why it works:** A checkpoint can contain the name of work that must run next. Changing the Python implementation is different from removing the graph node name that saved work references. Keeping `legal_review` as a compatible node name is one straightforward way to support those runs.

**Why the others fail:**

- **A:** The checkpointer does not infer semantic renames from similarly named or implemented functions.
- **C:** A node name participates in execution. Here it appears directly in the saved next-node position.
- **D:** Deleting a node creates no approval decision and does not legitimately complete the review.

**Standalone example - tested locally; no API key.** This rebuilds a graph against the same in-memory checkpoint data and retains the old graph node name while using a new Python review function. It demonstrates compatibility within one Python process; it does not claim to test deployment or storage across a process restart.

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    report: str
    status: str


def draft(state: State):
    print("draft ran")
    return {"status": "drafted"}


def review_v1(state: State):
    return {"status": "reviewed by v1"}


def review_v2(state: State):
    print("review_v2 implementation ran")
    return {"status": "reviewed by v2"}


def build_graph(saver, review_function, pause_before_review):
    builder = StateGraph(State)
    builder.add_node("draft", draft)
    # Keep the saved node name; its Python implementation may change.
    builder.add_node("legal_review", review_function)
    builder.add_edge(START, "draft")
    builder.add_edge("draft", "legal_review")
    builder.add_edge("legal_review", END)
    return builder.compile(
        checkpointer=saver,
        interrupt_before=["legal_review"] if pause_before_review else [],
    )


saver = InMemorySaver()
config = {"configurable": {"thread_id": "report-14"}}
old_graph = build_graph(saver, review_v1, True)
old_graph.invoke({"report": "Draft A", "status": "new"}, config=config)
snapshot = old_graph.get_state(config)
print("saved next:", snapshot.next)
print("saved status:", snapshot.values["status"])

# Rebuild against the same saved execution while retaining its node identity.
new_graph = build_graph(saver, review_v2, False)
print("compatible node name:", "legal_review")
result = new_graph.invoke(None, config=config)
print("final state:", result)
```

**Expected output - observed locally:**

```text
draft ran
saved next: ('legal_review',)
saved status: drafted
compatible node name: legal_review
review_v2 implementation ran
final state: {'report': 'Draft A', 'status': 'reviewed by v2'}
```

**Read the key lines slowly:**

1. `old_graph` uses `review_v1` as the implementation of the graph node named `legal_review`.
2. `interrupt_before=["legal_review"]` pauses before that node starts. This is a static pause before a node, so `invoke(None, ...)` will continue it; there is no `interrupt()` return value to supply here.
3. The first invocation runs `draft`, stores `status="drafted"`, and stops. `snapshot.next` shows exactly what remains: `("legal_review",)`.
4. `new_graph` uses the same saver and thread configuration, so it can find that saved execution. This demonstration deliberately keeps the saver alive.
5. `builder.add_node("legal_review", review_function)` preserves the saved graph identity. Passing `review_v2` changes the Python function behind that name, while the pending destination remains valid.
6. `new_graph.invoke(None, config=config)` continues from the pause. The output contains only one `draft ran` line: the saved draft step was not repeated. The new review implementation then sets `status="reviewed by v2"`.
7. This example shows a compatible rebuild. It does not rely on any particular failure message from an incompatible graph that deletes the saved node name.

---

## Set 2 - Q15: Allowing an interrupt to reach the runtime (Medium)

**Original reference:** LangGraph-M-H-Set2, question 15.

An approval node calls `interrupt("Approve report?")` inside a `try` block. A bare `except:` catches anything raised and returns `{"status": "failed"}`. The caller receives a failed status instead of an approval pause.

What best explains the behavior?

A. An interrupt payload must be a dictionary; a string is invalid.

B. A bare `except:` automatically creates an extra approval checkpoint.

C. Calling `interrupt()` inside a graph node is unsupported.

D. The broad handler catches the special exception used to signal the pause.

**Answer: D. The handler swallows the control-flow exception that signals the pause.**

`interrupt()` transfers control to LangGraph by raising a special exception. That signal must reach the graph runtime. A broad exception handler can intercept it and make the node appear to have completed with a normal failure update.

- **A fails:** the string in this question is a valid serializable interrupt payload.
- **B fails:** catching an exception does not create the intended approval pause.
- **C fails:** calling `interrupt()` inside a node is a supported pattern.

**Standalone example — run locally; no API key required.** The first node intentionally contains the bug. The second lets the pause signal reach LangGraph.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    status: str

def bad_review(state: State):
    try:
        approved = interrupt('Approve report?')
    except:  # Intentionally wrong: this catches the pause signal too.
        return {'status': 'failed'}
    return {'status': 'approved' if approved else 'rejected'}

def good_review(state: State):
    approved = interrupt('Approve report?')
    return {'status': 'approved' if approved else 'rejected'}

for label, review_node in [('bad', bad_review), ('good', good_review)]:
    builder = StateGraph(State)
    builder.add_node('review', review_node)
    builder.add_edge(START, 'review')
    builder.add_edge('review', END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {'configurable': {'thread_id': label}}
    first = graph.invoke({'status': 'pending'}, config)
    paused = bool(first.get('__interrupt__'))
    print(f'{label}: paused={paused}, status={first["status"]}')
    if paused:
        resumed = graph.invoke(Command(resume=True), config)
        print(f'{label}: resumed status={resumed["status"]}')
```

**Expected output — captured from the local run:**

```text
bad: paused=False, status=failed
good: paused=True, status=pending
good: resumed status=approved
```

**Follow the key lines:**

1. `bad_review` wraps `interrupt()` in a bare `except:`. On the first call, the interrupt raises its pause signal, but the handler catches it and returns `status='failed'`.
2. `good_review` places the interrupt outside broad exception handling. The runtime receives the signal and returns interrupt information to the caller.
3. Each graph has an `InMemorySaver` and a thread ID, so the good graph can resume its paused execution.
4. `bool(first.get('__interrupt__'))` checks whether this invocation paused. The bad version prints `False`; the good version prints `True`.
5. `Command(resume=True)` supplies `True` as the return value of the paused interrupt. The good node returns `status='approved'`.
6. Catch specific operational errors around the operations that can raise them. In the tested version, the interrupt exception subclasses `Exception`, so a broad `except Exception:` can swallow it too.


---

## Set 2 - Q17: Matching tool results to requested calls (Medium)

**Original reference:** LangGraph-M-H-Set2, question 17.

An `AIMessage` requests two calls to the same `search` tool. Their IDs are `call_a` and `call_b`, and their query arguments differ. Your custom graph node executes both calls and returns a `ToolMessage` for each result.

Which field must distinguish and correlate the results?

A. Give each result a different invented tool name.

B. Give both results the same `tool_call_id` because their tool name is `search`.

C. Set each result's `tool_call_id` to the ID of the corresponding requested call.

D. Rely on the order of the results in a Python list; IDs are unnecessary.

**Answer: C. Each result must carry its corresponding requested call ID.**

The two invocations share a function name, but they are separate requests. `tool_call_id` connects a tool result to the request that produced it, including when calls complete in a different order.

- **A fails:** changing tool names does not establish the request/result relationship.
- **B fails:** using one ID for two distinct requests loses that relationship.
- **D fails:** list position is not the identifier used to correlate a tool response.

**Standalone example — run locally; no API key required.** The assistant request and search results are simulated local data. The graph and message objects are real.

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Simulated local search results; there is no model or search API call.
def search(query: str) -> str:
    documents = {'revenue': 'Revenue grew 12%.', 'risk': 'Main risk: supplier concentration.'}
    return documents[query]

def run_tools(state: State):
    request = state['messages'][-1]
    results = []
    for call in request.tool_calls:
        result = search(call['args']['query'])
        results.append(ToolMessage(content=result, name='search', tool_call_id=call['id']))
    return {'messages': results}

request = AIMessage(content='', tool_calls=[
    {'name': 'search', 'args': {'query': 'revenue'}, 'id': 'call_a'},
    {'name': 'search', 'args': {'query': 'risk'}, 'id': 'call_b'},
])
builder = StateGraph(State)
builder.add_node('run_tools', run_tools)
builder.add_edge(START, 'run_tools')
builder.add_edge('run_tools', END)
graph = builder.compile()
result = graph.invoke({'messages': [HumanMessage(content='Find revenue and risk.'), request]})
print('Requested IDs:', [call['id'] for call in request.tool_calls])
for message in result['messages']:
    if isinstance(message, ToolMessage):
        print(f'{message.tool_call_id} -> {message.content}')
```

**Expected output — captured from the local run:**

```text
Requested IDs: ['call_a', 'call_b']
call_a -> Revenue grew 12%.
call_b -> Main risk: supplier concentration.
```

**Follow the key lines:**

1. The simulated assistant message requests `search(query='revenue')` with ID `call_a` and `search(query='risk')` with ID `call_b`.
2. `run_tools` reads the last message, then loops through its `tool_calls`.
3. `call['args']['query']` selects the query for that particular call. The local `search` function returns the corresponding sample document.
4. `ToolMessage(..., tool_call_id=call['id'])` copies the request's ID onto its result. It does not reuse the tool name as an identifier.
5. The `add_messages` reducer adds the returned tool messages to the graph's message state.
6. The printed `ID -> content` pairs make the relationship visible. This example checks local execution and message construction; it does not send the history to a model provider.


---

## Set 2 - Q18: Trimming a tool exchange coherently (Medium)

**Original reference:** LangGraph-M-H-Set2, question 18.

Assume the selected model provider requires tool results to be accompanied by the assistant message that requested them. Your history contains a user message, an assistant tool request, its `ToolMessage` result, and an assistant answer.

A trimming step removes the assistant tool request but keeps its result. The next model request is rejected because that tool result has no matching request. What should the trimming policy do?

A. Give the orphaned tool result a random ID and retry.

B. Blindly convert the tool result to a system message.

C. Keep only the tool results and discard the rest of the conversation.

D. Preserve the related request/result exchange together, or remove that exchange together.

**Answer: D. Keep or remove the related tool exchange coherently.**

A tool result depends on a specific earlier request. Trimming must preserve the message structure required by the selected provider. In this small example, either keep both related messages or remove both.

- **A fails:** a random ID does not restore the missing request.
- **B fails:** changing a role blindly changes the conversation semantics and does not reconstruct the exchange.
- **C fails:** orphaned results alone do not provide the required request/result structure.

**Standalone example — run locally; no API key required.** Messages and results are simulated. The helper checks only for results whose call ID was never requested earlier; it is not a complete provider-protocol validator. No provider rejection or acceptance was tested.

```python
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# All messages and tool results are simulated. No model request is sent.
history = [
    HumanMessage(content='Find revenue.'),
    AIMessage(content='', tool_calls=[
        {'name': 'search', 'args': {'query': 'revenue'}, 'id': 'call_a'},
    ]),
    ToolMessage(content='Revenue grew 12%.', tool_call_id='call_a'),
    AIMessage(content='Revenue grew 12%.'),
]

def find_orphan_results(messages):
    # This checks missing earlier call IDs only, not a provider's full protocol.
    requested_ids = set()
    orphan_ids = []
    for message in messages:
        if isinstance(message, AIMessage):
            requested_ids.update(call['id'] for call in message.tool_calls)
        if isinstance(message, ToolMessage) and message.tool_call_id not in requested_ids:
            orphan_ids.append(message.tool_call_id)
    return orphan_ids

broken_history = [history[0], history[2], history[3]]
# Remove both the requesting assistant message and its tool result.
trimmed_history = [history[0], history[3]]
print('Original orphan IDs:', find_orphan_results(history))
print('Broken orphan IDs:', find_orphan_results(broken_history))
print('Trimmed orphan IDs:', find_orphan_results(trimmed_history))
print('Trimmed roles:', [message.type for message in trimmed_history])
```

**Expected output — captured from the local run:**

```text
Original orphan IDs: []
Broken orphan IDs: ['call_a']
Trimmed orphan IDs: []
Trimmed roles: ['human', 'ai']
```

**Follow the key lines:**

1. `history[1]` contains the assistant request for `call_a`. `history[2]` is the corresponding result.
2. `find_orphan_results` collects requested IDs as it walks through the messages. A tool result whose ID is absent from that collection is an orphan under this limited check.
3. `broken_history` keeps the result but removes its requesting assistant message. The helper reports `call_a`.
4. `trimmed_history` removes both related messages while retaining the user question and final assistant answer. It contains no tool result that needs the deleted request.
5. Empty orphan lists show that this specific check passed. They do not establish every provider requirement, such as complete results for multiple calls, message adjacency, role ordering, or provider-specific restrictions.


---

## Set 2 - Q19: Streaming progress from inside a node (Medium)

**Original reference:** LangGraph-M-H-Set2, question 19.

A node performs a long operation. While it is running, the UI should receive a progress event such as `"30% complete"`. That progress text is temporary UI feedback, not a business-state field.

Using LangGraph's stream-mode API, which pattern directly supports this?

A. Print to stdout and assume `graph.stream()` automatically forwards every print.

B. Emit through `get_stream_writer()` and consume the `custom` stream mode.

C. Put progress only in the final output schema and wait until execution ends.

D. Use an ordinary `return` after each loop iteration and expect the same function call to continue.

**Answer: B. Emit custom events through the stream writer.**

A stream writer can emit progress while the node continues working. The caller receives those events through the custom stream. The node still returns its normal state update when it finishes.

- **A fails:** stdout output is not automatically converted into LangGraph custom events.
- **C fails:** waiting for final output does not deliver progress while the operation is running.
- **D fails:** an ordinary `return` ends the function call; it is not an intermediate progress event.

**Standalone example — run locally; no API key required.** Progress values are illustrative; the example emits them immediately rather than performing slow work.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

class State(TypedDict):
    report: str

def write_report(state: State):
    writer = get_stream_writer()
    writer({'progress': '30% complete'})
    writer({'progress': '100% complete'})
    return {'report': 'Finished report'}

builder = StateGraph(State)
builder.add_node('write_report', write_report)
builder.add_edge(START, 'write_report')
builder.add_edge('write_report', END)
graph = builder.compile()
for mode, data in graph.stream({'report': ''}, stream_mode=['custom', 'updates']):
    print(f'{mode}: {data}')
```

**Expected output — captured from the local run:**

```text
custom: {'progress': '30% complete'}
custom: {'progress': '100% complete'}
updates: {'write_report': {'report': 'Finished report'}}
```

**Follow the key lines:**

1. `get_stream_writer()` obtains the writer for the currently executing graph node.
2. `writer({'progress': '30% complete'})` sends a custom event. It does not write a `progress` key into graph state.
3. A second writer call emits the next event, and the function continues until its ordinary `return`.
4. The returned `{'report': 'Finished report'}` is the actual business-state update.
5. `stream_mode=['custom', 'updates']` asks for both kinds of events. Each yielded pair contains the mode name and its data, so the caller can distinguish UI progress from node state updates.
6. Only `report` is declared in the state schema. The output shows progress events separately from the final report update.


---

## Set 2 - Q20: Separating concurrency from token rate (Medium)

**Original reference:** LangGraph-M-H-Set2, question 20.

A graph invocation sets `config={"max_concurrency": 4}` to limit simultaneous scheduled work. Its model provider still returns token-per-minute quota errors. The quota is scoped by the provider account, not by graph thread IDs.

Which conclusion is accurate?

A. Concurrency limits simultaneous work; token-rate limits need separate budgeting or throttling.

B. Four concurrent tasks imply at most four tokens per minute.

C. A token quota error proves that the concurrency setting has no effect.

D. A fresh `thread_id` automatically resets the provider's token quota.

**Answer: A. Simultaneous task count and tokens consumed over time are separate limits.**

Four concurrent requests can each consume thousands of tokens. A concurrency cap controls how much scheduled work can run at once; it does not impose a token budget for a one-minute window.

- **B fails:** task count does not specify tokens per request or how many requests finish in a minute.
- **C fails:** the concurrency cap can work while a different resource limit is exceeded.
- **D fails:** a graph thread ID does not reset an external account quota.

**Standalone example — run locally; no API key required.** The graph schedules four workers. Each returns a simulated usage count of 3,000 tokens. For the arithmetic, assume all four requests fall within one quota minute and the quota is 10,000 tokens. No provider or real rate limiter is called or tested.

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    request_ids: list[int]
    token_counts: Annotated[list[int], operator.add]

class WorkerInput(TypedDict):
    request_id: int

def dispatch(state: State):
    return [Send('model_request', {'request_id': i}) for i in state['request_ids']]

def model_request(state: WorkerInput):
    # Simulated usage per request, not a real provider response.
    return {'token_counts': [3000]}

builder = StateGraph(State)
builder.add_node('model_request', model_request)
builder.add_conditional_edges(START, dispatch, ['model_request'])
builder.add_edge('model_request', END)
graph = builder.compile()
result = graph.invoke(
    {'request_ids': [1, 2, 3, 4], 'token_counts': []},
    config={'max_concurrency': 4},
)
# Assume these four simulated requests occur in one quota window.
quota = 10000
used = sum(result['token_counts'])
print('Configured concurrency cap:', 4)
print('Simulated tokens per request:', result['token_counts'])
print('Simulated tokens in one minute:', used)
print('Assumed token-per-minute quota:', quota)
print('Would exceed assumed quota:', used > quota)
```

**Expected output — captured from the local run:**

```text
Configured concurrency cap: 4
Simulated tokens per request: [3000, 3000, 3000, 3000]
Simulated tokens in one minute: 12000
Assumed token-per-minute quota: 10000
Would exceed assumed quota: True
```

**Follow the key lines:**

1. `dispatch` returns one `Send` per request ID, creating four worker tasks. This uses the dynamic fan-out pattern already covered in Set 1.
2. `max_concurrency=4` supplies the scheduling cap. It does not inspect or budget the simulated token counts.
3. Each worker returns `[3000]`. The `operator.add` reducer concatenates those lists into `[3000, 3000, 3000, 3000]`.
4. `sum(...)` calculates 12,000 tokens under the stated one-minute assumption.
5. Comparing 12,000 against the assumed quota of 10,000 gives `True`. That arithmetic illustrates why respecting the concurrency cap does not guarantee respecting a token-rate quota.
6. This example does not measure wall-clock throughput or test the provider's quota enforcement. A real token budget must account for the provider's quota rules and the requests sharing that quota.

---

## API verification references

The official pages below were checked alongside the installed package signatures and the executed examples. They explain the API contracts; the displayed outputs come from the local examples, not from copied documentation examples. Provider-side message rejection, real token quotas, live external side effects, production deployment, and full operating-system process restarts were not tested. The SQLite example tests closing and reopening checkpoint storage within one process.

| Questions | Official reference |
| --- | --- |
| Set 1 Q01–Q07, Q11–Q15; Set 2 Q01–Q02, Q04–Q08, Q14 | [Graph API overview: state, routing, context, caching, migrations](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| Set 1 Q11–Q15, Q19; Set 2 Q02, Q06, Q08, Q13 | [Use the graph API: reducers, joins, schemas, retries](https://docs.langchain.com/oss/python/langgraph/use-graph-api) |
| Set 1 Q08–Q09, Q18; Set 2 Q09–Q10 | [Checkpointers: threads, snapshots, updates, attribution](https://docs.langchain.com/oss/python/langgraph/checkpointers) |
| Set 1 Q16–Q18; Set 2 Q15 | [Interrupts: pausing, resuming, replay, exception handling](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| Set 1 Q10; Set 2 Q19 | [Streaming: updates and custom stream modes](https://docs.langchain.com/oss/python/langgraph/streaming) |
| Set 1 Q20 | [Stores: data shared across threads](https://docs.langchain.com/oss/python/langgraph/stores) |
| Set 2 Q03 | [Subgraphs: translating parent and child interfaces](https://docs.langchain.com/oss/python/langgraph/use-subgraphs) |
| Set 2 Q10–Q11 | [Time travel: attribution and replay](https://docs.langchain.com/oss/python/langgraph/use-time-travel) |
| Set 1 Q07; Set 2 Q17 | [Messages: message IDs and tool-call IDs](https://docs.langchain.com/oss/python/langchain/messages) |
| Set 2 Q20 | [RunnableConfig: maximum concurrency](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) |
| Set 2 Q18 | [Memory: preserving valid message histories](https://docs.langchain.com/oss/python/langgraph/add-memory) |

`stream_mode="updates"` and `stream_mode="custom"` remain valid APIs in the tested version. These examples retain the stream-mode API used in the original questions. The concurrency example passes `max_concurrency` to the installed API, but does not measure peak concurrency. Its token arithmetic is an explicitly simulated budget, not a provider rate-limit test.
