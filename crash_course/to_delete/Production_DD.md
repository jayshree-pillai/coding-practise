# CAR Conversational Agent: LangGraph Execution in Azure Functions

## Interview question

**How is a LangGraph conversational workflow built and invoked in Azure Functions, and how are multiple chats handled across Python worker processes?**

## 1. Builder, compiled graph, run, and conversation state

| Concept | What it does | Lifecycle in the design we discussed |
|---|---|---|
| **Builder**: `StateGraph(...)` | Assemble the nodes, edges, routing, and state schema. | Created during each Python worker process's startup. |
| **Compiled graph**: `builder.compile(...)` | Produce the executable workflow object. | Reused by that worker process. |
| **Run**: `graph.ainvoke(...)` | Execute the workflow for an incoming user message. | A new invocation for each user turn. |
| **Conversation state** | Hold that conversation's messages, specialist results, and other context. | Kept separate from other conversations; persisted through the checkpointer. |

Awaiting `graph.ainvoke(...)` starts one run of the existing compiled graph. Calling this async method without awaiting or scheduling it creates a coroutine object. It does not require another builder or another compilation for that message.

One process can reuse one compiled graph for multiple conversations. If compilation is placed inside the request handler instead, the application creates a graph per request. Our example uses compilation at startup.

## 2. Where does the code go?

In Azure Functions' Python v2 model, `function_app.py` is the application entry point.

- **Steps 1 and 2: build and compile outside the chat handler**, once during worker startup.
- **Step 3: invoke inside the chat handler**, for each incoming message.

The following is the simplified placement sketch we discussed. `ChatState`, the checkpointer, node registration, and request preparation are application components omitted from the sketch.

```python
# function_app.py
import azure.functions as func
from langgraph.graph import StateGraph

app = func.FunctionApp()

# Startup — once per Python worker process
builder = StateGraph(ChatState)                       # 1. Build
# Add Supervisor, SQL, Evidence nodes and edges...
graph = builder.compile(checkpointer=checkpointer)    # 2. Compile


# Each incoming chat request
@app.route(route="chat", methods=["POST"])
async def chat(req: func.HttpRequest):
    # Authenticate and prepare input_state and config...
    result = await graph.ainvoke(                     # 3. Invoke
        input_state,
        config=config,
    )
    return func.HttpResponse(result["answer"])
```

The **same process executes both parts**: startup creates the graph; the API handler reuses it when messages arrive.

Graph construction can also live in `orchestrator.py`, with the compiled `graph` imported into `function_app.py`.

## 3. Does the API call only `graph.ainvoke(...)`?

That is the API's call to start the entire conversational workflow. Around that call, the API:

1. Authenticates the user, verifies CAR/company scope, and prepares the message and conversation configuration.
2. Calls `result = await graph.ainvoke(input_state, config=config)`.
3. Extracts the completed answer from `result` and returns it to the UI.

During that **one invocation**, the normal successful workflow can execute:

**Supervisor → SQL → Supervisor → Evidence → Supervisor synthesis → validation → END**

When SQL returns, its result updates that run's state. Routing schedules the supervisor again, and it receives the updated state. The API does not call `ainvoke()` again for the SQL response or final synthesis.

**One graph invocation can contain multiple node executions, LLM calls, and tool calls.**

## 4. Does one worker mean one Function App?

No. These are different levels:

| Level | Meaning |
|---|---|
| **Function App** | The deployed application containing the functions. |
| **Host instance** | One running instance of that application; scaling can add more. |
| **Python worker process** | A process inside a host instance that executes Python code. |

By default, a host instance has one language worker process. `FUNCTIONS_WORKER_PROCESS_COUNT` can increase that number.

Each worker process has its own memory and its own compiled graph object in the startup design above.

## 5. What do four compiled graphs mean?

The example we discussed was:

**1 Function App × 2 host instances × 2 Python workers = 4 compiled graph objects.**

This assumes each worker builds and compiles one graph during startup. These numbers were an example, not confirmed deployment settings.

| Host instance | Worker process | Compiled graph in its memory |
|---|---|---|
| Host A | Worker A1 | Graph A1 |
| Host A | Worker A2 | Graph A2 |
| Host B | Worker B1 | Graph B1 |
| Host B | Worker B2 | Graph B2 |

All four are **copies of the same workflow** in separate processes. They are not four different workflows, and one request does not execute the workflow four times.

The graph-object count is separate from the run count. Each graph object can be invoked repeatedly, and each worker can handle multiple asynchronous chat requests concurrently.

## 6. What happens when a chat message arrives?

1. Azure routes the request to a host instance.
2. The Functions host dispatches the invocation to a Python worker.
3. That worker executes its `chat()` handler.
4. The handler calls `await graph.ainvoke(...)` on its compiled graph.
5. The workflow completes and the handler returns the answer.

Different requests can be handled by different workers. Each invocation has separate execution state.

## 7. How does the next message continue the same conversation?

Set the conversation identifier in the invocation configuration:

```python
config = {
    "configurable": {
        "thread_id": conversation_id,
    }
}
```

A follow-up message starts another invocation using the **same conversation `thread_id`**. With a checkpointer configured, LangGraph retrieves that conversation's saved state.

Independent conversations use different IDs, even when they belong to the same user. Here, a LangGraph thread means a persisted conversation, not a Python operating-system thread.

The next message may reach another worker. Using the same conversation ID and a shared Cosmos-backed checkpointer lets that worker retrieve the saved state and continue.

## 8. How is concurrency handled?

These were the controls discussed in this chat:

- **Different conversations:** The server schedules asynchronous graph invocations. Application limits control concurrent requests and downstream LLM/SQL calls.
- **User context:** Supply verified user, CAR, and document scope for each execution. Shared node functions and tool wrappers must not put the current user in mutable global variables.
- **Two messages in the same conversation:** Serialize them using a queue or lock for that conversation. Across multiple workers, coordination must work across processes. Checkpoint persistence alone does not establish exclusive execution.

## 9. Objects and coroutine execution, step by step

### Step 1: The API receives the chat request and prepares the inputs for the graph.

Angular sends the HTTP request. Azure dispatches it to a Python worker whose compiled `graph` already exists. The API prepares the inputs for this invocation:

```python
# Inside the API handler, after parsing and validating the request.
input_state = {"messages": [("user", user_message)]}
config = {"configurable": {"thread_id": conversation_id}}
```

These snippets illustrate object flow. Other `ChatState` fields, authentication, and application helper implementations are omitted.

| Object | What it contains | Scope |
|---|---|---|
| `graph` | The compiled workflow and registered nodes/edges | Existing object, shared within this worker |
| `input_state` | This turn's message and input fields | Prepared for this invocation |
| `config` | Conversation `thread_id` and invocation settings | Prepared for this invocation |

No Supervisor or tool call has started at this point.

### Step 2: Calling `graph.ainvoke(...)` creates a coroutine for this chat.

Separate the call from the `await` to see the new object:

```python
run_coroutine = graph.ainvoke(input_state, config=config)
```

Calling an `async def` function such as this method creates a **coroutine object**. The function body starts executing when that coroutine is awaited or scheduled.

`run_coroutine` represents this invocation's pending execution of the whole graph. It holds references to the existing graph and the invocation arguments; it does not copy the compiled graph.

**One shared compiled graph can therefore have multiple separate coroutine executions for different chats.**

#### What is special about a coroutine?

A coroutine can suspend and resume while preserving its local variables and execution position:

```python
async def example():
    x = 10
    result = await fetch_number()  # Illustrative async I/O helper.
    return x + result
```

If the number is not ready, execution waits at `await`. It retains `x = 10` and the position at which to continue. The event loop can run other tasks during the wait. When the number arrives, this execution resumes and calculates `x + result`.

An `await` yields control when the awaited operation actually needs to wait. An already completed operation can proceed immediately.

### Step 3: The API awaits the graph coroutine and the graph starts.

```python
result = await run_coroutine
```

The graph's code now executes. The API handler waits for its result and cannot execute the next line until this `await` completes.

LangGraph prepares this run's working state from the input and, when a checkpointer is configured, the conversation's saved state. It then reaches the first Supervisor node.

The two lines are normally combined:

```python
result = await graph.ainvoke(input_state, config=config)
```

#### Who retains the coroutine while execution is suspended?

The suspended API handler remains alive with its local variables. In the two-line example, `run_coroutine` still references the graph coroutine.

An **`asyncio.Task`** manages async execution. It retains the coroutine it runs; nested awaited coroutines remain reachable through the awaiting execution chain. LangGraph can also schedule additional tasks for node execution.

| Object | What retains it during an ordinary wait? |
|---|---|
| Compiled `graph` | The module-level variable and references used by executions |
| API handler's coroutine execution | The request runtime/task and awaiting execution chain |
| Graph coroutine | The handler's `run_coroutine` variable and its `await` |

These objects remain in the worker process's memory. When pending I/O completes, the event loop resumes the waiting execution. **Suspension preserves the live execution; it is not a checkpoint or a completed HTTP response.**

### Step 4: LangGraph starts the first Supervisor node and its model call.

The registered Supervisor function already exists. Calling an async Supervisor node creates a new coroutine for **this visit to that node**.

```python
async def supervisor_node(state):
    messages = build_supervisor_messages(state)
    response = await supervisor_llm.ainvoke(messages)
    update = validate_and_make_handoff(response, state)
    return update
```

In this sketch, `supervisor_llm` is an existing reusable model client. The helper functions are application-specific placeholders. Model/MCP clients can be reused when their implementations and lifetimes support concurrent use; user-specific messages and scope remain in invocation data.

Calling its async `ainvoke` creates another coroutine, representing this model request. While the model response is pending:

| Execution | What it is waiting for |
|---|---|
| API handler | The overall graph result |
| Graph run | The Supervisor node to finish |
| Supervisor node | Its LLM response |
| LLM client call | The model service's response |

The model response is assigned to `response`. The Supervisor then validates it and returns a state update/handoff. For our SQL route, that update directs the graph to SQL. This Supervisor invocation finishes, while the overall graph run continues.

The repeated Supervisor visits in **Supervisor → SQL → Supervisor → Evidence → Supervisor synthesis → validation → END** are separate invocations of the registered node function.

### The SQL node's MCP call uses the same async mechanism for a different operation.

In the routing design, the Supervisor returns its routing decision. LangGraph then schedules SQL; the Supervisor does not need to remain suspended around SQL's whole execution.

```python
async def sql_node(state):
    arguments = make_sql_arguments(state["handoff"])
    tool_result = await mcp_client.call_tool(
        "run_sql",
        arguments=arguments,
    )
    return {"sql_result": decode_and_validate(tool_result)}
```

This excerpt shows the MCP boundary. The SQL specialist can also make its own LLM calls before choosing its tool arguments.

| Awaited call | What the execution does | What it eventually produces |
|---|---|---|
| `graph.ainvoke(...)` | Run the entire graph | The overall graph output |
| `supervisor_llm.ainvoke(...)` | Make one Supervisor model request | That model response |
| `mcp_client.call_tool(...)` | Invoke one MCP tool | That tool's result |

They can all create coroutine executions because their client methods are async. **Their purpose and returned data differ; none of these calls creates another copy of the parent compiled graph.**

During pending MCP I/O, the SQL invocation and the outer graph remain pending, and the worker can progress other chats. When the response arrives, SQL resumes, validates the result, and returns its state update. The graph schedules Supervisor again with the updated state.

The SQL execution is then complete, but its result remains available in graph state. Its function/client objects remain reusable. Completed execution objects and temporary values can be reclaimed when no longer referenced; completion does not guarantee immediate destruction.

On normal completion at `END`, the overall graph returns its result and the API handler can send the HTTP response.

The dependent steps of one chat still follow their required order. Evidence that needs SQL findings waits for SQL; async calls allow other work to progress during waits, rather than automatically making dependent nodes concurrent.

### Where do the subsequent calls execute?

The local graph execution stays in the worker that is handling the request. Starting an async invocation does not fork a new process, and ordinary `await` suspension does not cause Azure to route the running graph to another worker.

| Moving part | Execution location |
|---|---|
| Graph runner, Supervisor, SQL, Evidence, validation | The same Python worker process |
| Coroutine making the LLM request | Same worker; the model executes in the model service |
| Coroutine making a remote MCP request | Same worker; the tool implementation executes on the MCP server |

There can be nested coroutine calls and separately scheduled node tasks within that process. The remote service has its own execution lifecycle.

### What if the worker crashes during an MCP call?

Assume Supervisor's output was successfully committed to a durable Cosmos-backed checkpoint, SQL sent an MCP request, and the worker crashed while awaiting its response.

| Object | What happens after the crash? |
|---|---|
| Crashed worker's compiled graph | Lost; a healthy worker uses its own graph, or a replacement builds one during startup |
| Crashed worker's model/MCP/checkpointer client objects | Lost; recreated during replacement-worker startup |
| Live graph, node and MCP-call coroutines, plus their Tasks | Lost; recovery creates fresh execution objects |
| Local variables and unsaved results | Lost; recomputed or loaded from separately persisted data |
| Successfully committed Cosmos checkpoint | Survives; preserves graph state and pending-work metadata |

**Checkpoint recovery reconstructs execution from saved data. It does not restore the old coroutine at the exact suspended `await` line.** In our ordinary SQL-node layout, SQL starts again from its beginning and may repeat its LLM and MCP calls.

LangGraph checkpoints at graph step boundaries. Merely constructing a state object or reaching an `await` does not persist it. Recovery depends on the last checkpoint that actually committed. An in-memory checkpointer would lose its checkpoints on process loss too.

A recovery invocation for an unfinished checkpointed run can look like:

```python
# A new recovery request/job, using the existing conversation ID.
config = {"configurable": {"thread_id": existing_conversation_id}}
result = await graph.ainvoke(None, config=config)
```

The checkpointer loads the saved state; LangGraph executes the pending work. This code assumes a durable checkpoint with unfinished work. It resumes that execution rather than submitting another copy of the user's message.

### Who is responsible for restarting?

| Responsibility | Owner |
|---|---|
| Restart or replace the worker process | Azure Functions host/platform |
| Trigger recovery of the unfinished workflow | Application retry/recovery logic |
| Load the checkpoint and execute pending nodes | LangGraph with its durable checkpointer |
| Prevent a repeated write from duplicating an update | MCP tool's backend |

For Angular → HTTP API, a configured Angular retry/resume request can trigger recovery. A backend job mechanism is another option. HTTP triggers do not have Azure Functions' built-in function-level retry policies, so the recovery trigger must be implemented explicitly. Worker replacement alone does not replay the failed HTTP request.

### What if the MCP tool performs an update? Where does idempotency fit?

This is the hypothetical write scenario we discussed. The remote tool might have committed its update even though the calling worker never received or checkpointed the response. Retrying can send that operation again.

The application generates an **operation key once per logical update**, and persists that key with the exact tool arguments **before** the request is sent. A checkpointed preparation step can produce that data:

```python
from uuid import uuid4


def prepare_update_node(state):
    operation = {
        "operation_id": str(uuid4()),
        "tool_name": "update_record",
        "arguments": {
            "record_id": state["record_id"],
            "status": state["requested_status"],
        },
    }
    return {"pending_update": operation}
```

`pending_update` and the tool name are illustrative fields for this example. **The preparation checkpoint must durably commit before the execution step sends the tool request.** Generating a key only in the executing coroutine's local variables would lose it on a crash.

```python
async def execute_update_node(state):
    operation = state["pending_update"]
    result = await mcp_client.call_tool(
        operation["tool_name"],
        arguments={
            **operation["arguments"],
            "operation_id": operation["operation_id"],
        },
    )
    return {"update_result": decode_and_validate(result)}
```

The intended recovery sequence is:

1. Application durably records the operation key and arguments.
2. SQL/update execution sends them to the MCP tool.
3. The backend commits the update and records the key plus result atomically, typically in the same database transaction.
4. The caller's worker crashes before receiving/checkpointing the result.
5. Recovery retries with the same key and arguments.
6. The backend returns the recorded result without applying the update again. If the first transaction never committed, the retry can perform it.

Adding a key to the request is insufficient: the MCP tool's backend must implement durable duplicate detection and enforce that atomic update/result-recording behavior.

| Identifier | What it identifies |
|---|---|
| `thread_id` | The conversation |
| Operation/idempotency key | One logical write operation within the conversation |

Different updates receive different operation keys. Retries of one update reuse its saved key and arguments.

## Connection Pooling when running concurrently 

### Why did the agent call the tool 5 times, and how do you stop it?
```python
SQL → Returns the verified financial changes.
Evidence → Searches, but finds no supported explanation.
Supervisor → “The ‘why’ is still unanswered. Search again.”
Evidence → Rephrases the query; retrieves the same unhelpful passages.
Supervisor → “The ‘why’ is still unanswered. Search again.”
...and the cycle continues.

# add application owned section
{
  "execution_control": {
    "tool_calls_used": 3,
    "tool_call_limit": 5,
    "consecutive_no_progress": 2,
    "no_progress_limit": 2,
    "stop_reason": null
  }
}
```
The application would update the counters; the limits would come from trusted configuration.The supervisor LLM should not be able to reset the counters or increase its own budget.

3. Python control logic: “Is another call permitted? - The key is enforcing a Python boundary: the supervisor proposes actions, while only application code can read or mutate protected execution-control state.
The specialist Result contract makes unresolved gaps explicit. Shared workflow state tracks attempts and budgets across delegations. Application code checks that state before allowing another call and routes to a qualified answer when a stopping condition is reached
```
Supervisor proposes another Evidence call
                  ↓
Python checks the budget and no-progress limit
                  ↓
Allowed → execute the call
Stopped → retain verified findings and disclose the evidence gap
```
Only the executor - not the supervisor manages execution controls

| Field | Where its value comes from |
|---|---|
| `tool_call_limit` | Trusted application configuration—not model output. |
| `tool_calls_used` | Executor accounting for actual tool-call attempts—not the model’s self-report. |
| `stop_reason` | Python’s stopping checks—not a model-requested override. |

Before each actual SQL or Evidence tool call, the executor checks the stored usage against the trusted limit. At the limit, it refuses another tool call and routes to the stopping path—even when the supervisor proposes another search.
All specialist tool calls must pass through that check, and re-delegating within the same request must reuse the existing budget. I would not expose a tool that lets the model reset budgets or write arbitrary workflow state.


### How do you design tools so the agent uses them correctly?
Each MCP Tool has a clear purpose and boundary - MCP tool definitions support a name, description, and input schema
our CAR MCP Tools have:
| Tool | Description I would give it |
|---|---|
| **SQL retrieval tool** | “Retrieve structured financial records from the SQL database for numerical analysis. Use for financial values and reporting periods—not for searching documentary explanations.” |
| **Evidence retrieval tool** | “Search the permitted CAR/document sources for relevant passages and return their source references. Use for documented explanations—not for querying the SQL database.” |

ReACT Pattern: the supervisor LLM decides whether to invoke SQL or Evidence or both. That is exactly how your CAR notes describe its ReAct loop: choose a specialist, delegate, observe the result, and decide the next action.

You can reliably enure that supevisor calls SQL Specialist - we nade specialist descriptions clear; supervir instructions strong and
structured next_action: Literal["sql","evidence","clarify","finish"],

### What happens when the task is longer than the model’s context window?
```
The whole state at a glance. 
LANGGRAPH STATE
│
├── REQUEST OBJECT
│   ├── Entity / report scope
│   │     └── company, CAR, report version
│   ├── Analysis topic
│   │     └── liquidity / profitability / leverage / etc.
│   ├── Measures
│   │     └── requested or unresolved financial measures
│   ├── Time scope
│   │     └── FY2024, FY2025, etc.
│   ├── Operation
│   │     └── compare / explain / calculate / retrieve
│   └── Output requirements
│         └── figures, changes, explanation, citations
│
├── CURRENT HANDOFF OBJECT
│   ├── Task
│   │     └── what this specialist must do
│   ├── Scope
│   │     └── verified company + CAR context
│   ├── Analysis topic
│   │     └── liquidity
│   ├── Measures + time scope
│   │     └── definitions + FY2024/FY2025
│   ├── Source scope
│   │     └── SQL data / CAR docs / uploads
│   ├── Input findings
│   │     └── prior specialist findings, if needed
│   └── Output requirements
│         └── what this specialist must return
│
└── RESULT OBJECT(S)
    ├── Specialist
    │     └── SQL / Evidence
    ├── Assignment / scope
    │     └── what work was completed
    ├── Status
    │     └── complete / partial / needs clarification / failed
    ├── Resolved context
    │     └── measures, definitions, periods, interpretations
    ├── Findings
    │     └── numerical results or documented explanations
    ├── Provenance
    │     └── DB records / query refs / chunk IDs / citations
    └── Gaps
          └── unresolved or missing information
```
```
The StateEvolves
Initial State
│
├── Request object
├── Handoff = SQL assignment
└── Results = []

        ↓ SQL executes

Updated State
│
├── Request object
├── Handoff = SQL assignment
└── Results
      └── SQL Result
            ├── resolved measures
            ├── resolved periods
            ├── financial findings
            └── provenance

        ↓ Supervisor observes SQL result
        ↓ creates next assignment

Updated State
│
├── Request object
├── Handoff = Evidence assignment
│     └── includes relevant SQL findings
└── Results
      └── SQL Result

        ↓ Evidence executes

Updated State
│
├── Request object
├── Handoff = Evidence assignment
└── Results
      ├── SQL Result
      └── Evidence Result
            ├── explanation
            ├── citations
            └── gaps

        ↓ Supervisor synthesizes

Final Answer
```

Request = what the user ultimately wants.
Handoff = what the next specialist needs to do.
Result = what that specialist actually accomplished.

And the LangGraph state is the container holding all three as the workflow evolves.

```
Supervisor LLM
   ↓
decides:
"What work is still needed?"
"What context should the next specialist use?"

        ↓

Python / LangGraph node
   ↓
reads the shared State
   ↓
selects/copies the relevant fields
   ↓
builds the Handoff object

        ↓

Next specialist
```
In CAR, I don’t use the LLM context window as the system’s memory. The workflow state is maintained outside the model as LangGraph state and persisted for the conversation. That state contains the original request, current handoff, specialist results, resolved context, and other workflow information.
As the workflow progresses,  Each Python/LangGraph node reads the shared state and builds the context needed for that specific agent. For example, after SQL completes, the supervisor determines that the remaining task is to find the documentary explanation. Python then constructs the Evidence handoff using only the relevant state: the verified company and CAR scope, resolved measures and periods, the SQL findings, provenance, and the outstanding evidence task.

The original request remains available in state, while structured handoffs carry only what the next specialist needs.

### what happens when the conversation history becomes large
```
BEFORE COMPACTION

LANGGRAPH STATE
│
├── current_request
│
├── resolved_context               ← keep exact
│     ├── company / CAR
│     ├── definitions
│     ├── periods
│     └── established facts
│
├── results                        ← keep relevant structured results
│     ├── SQL results
│     └── Evidence results
│
└── conversation_history
      ├── Turn 1
      ├── Turn 2
      ├── Turn 3
      ├── ...
      └── Turn 10
```

Once that history becomes large:
```
                 SUMMARIZATION NODE
                        │
                        ▼

LANGGRAPH STATE
│
├── current_request
│
├── resolved_context               ← exact, unchanged
│
├── relevant_results               ← exact, structured
│
└── conversation_summary
      └── "User is analyzing ABC's liquidity.
           Scope is CAR 101, consolidated basis.
           FY2024/FY2025 comparison established.
           Cash declined 20%.
           Prior discussion focused on working-capital
           drivers and short-term debt..."
```
As a conversation grows, I can periodically compact older message history into a rolling summary stored in LangGraph state. I preserve canonical structured state—scope, periods, definitions, validated findings and provenance—exactly, while replacing older conversational turns with the summary. Future calls use the summary plus the current request and relevant structured state, rather than replaying the entire conversation

#### So 4 layers to the answer 
#1: Don’t use the context window as memory:
LangGraph state holds the durable workflow context, and checkpoints persist that state.
#2: Don’t pass the entire state to every LLM call.
Each Python/LangGraph node projects only the relevant pieces into that agent’s prompt.
#3: Keep authoritative data exact.
Company/CAR scope, periods, definitions, validated findings, provenance, current gaps, and relevant results remain structured.
#4: Compact long conversational history.
After enough turns, older dialogue can be replaced with a rolling summary while preserving the canonical structured state.

### The agent ran for 10 minutes and the bill tripled — who stops it and how

```
LANGGRAPH STATE
│
├── Request
├── Handoff
├── Results
│
└── execution_control
      ├── tool_calls_used
      ├── tool_call_limit
      ├── model_calls_used
      ├── model_call_limit
      ├── tokens_used
      ├── token_budget
      ├── estimated_cost
      ├── cost_budget
      ├── elapsed_time
      └── max_runtime

```
Application code stops it. I maintain request-level execution controls in the LangGraph state—such as model/tool-call counts, token or cost budget, and maximum runtime. Before each additional action, the executor checks those limits. If a limit is reached, it refuses further execution and routes to a controlled stop or escalation. The model can propose another action, but it cannot extend its own budget.

### Prompt injection — how will you stop it?
Treat retrieved documents and tool outputs as untrusted data, not as instructions.
```
Prompt injection defense
│├── Separate instructions from retrieved evidence
│├── Treat document/tool content as untrusted
│├── Allow only bounded specialist actions
│├── Python validates tool arguments
│├── Python enforces company/CAR/user scope
│└── Tool/API layer authorizes actual access
```
Retrieved content is treated as untrusted data. The model operates within a bounded action set, and Python validates every requested action and enforces the authenticated CAR/company scope before a tool call is executed. So even if a document contains malicious instructions, it cannot expand the agent’s permissions.
Application/tool layer: enforce permissions and scope regardless of what the model says.

### HITL
I used HITL in Adaptive Context Enrichment when automated recovery could no longer safely resolve the issue and human judgment was required. The automated recovery itself was bounded to two additional attempts. After that, the workflow would not keep looping; it either remained explicitly unresolved or, for cases requiring analyst judgment, paused through LangGraph HITL and persisted the state for review.

### steps crashed at Step40:
#### Restore execution state: Checkpointing
I used a Cosmos-backed LangGraph checkpointer keyed by thread_id. After graph steps, LangGraph persisted the current state. If the worker crashed, I invoked the graph again with the same thread_id; LangGraph restored the most recent durable checkpoint and continued from that saved workflow state rather than restarting the entire task.
#### Idempotency
Use a stable idempotency key representing one logical execution. Every retry reuses the same key. A durable operation store enforces uniqueness when that key is first registered, so a repeated request can short-circuit rather than execute the action.
CAR did not have irreversible business actions. Idempotency was mainly needed for distributed section processing and retries. Checkpointing preserved workflow progress, while stable execution/section identities and idempotent result writes prevented duplicate queue deliveries or retries from creating duplicate section outputs.
The thread_id identified the LangGraph execution state to restore from the checkpointer, while the AgentState contained the evolving workflow data such as results, status and counters. If a worker crashed, the replacement worker resumed the same thread from the latest durable checkpoint rather than starting the workflow again.

### The final answer is correct — but is the agent actually good? Trajectory Eval
In CAR, I used OpenTelemetry with Azure Application Insights for distributed tracing. Each execution had a `trace_id`, and individual operations—such as retrieval, LLM generation, guard evaluation, or recovery—were represented by spans with their own `span_id`. Trace context was propagated across the API, queue, and worker boundaries, so I could reconstruct one execution end to end.

If the same input produced different behavior across two runs, I would first locate both executions using their execution identifiers and trace IDs. Then I would compare the span sequence to find the first point where the trajectories diverged—for example, whether the supervisor selected a different route, retrieval returned different evidence, a different tool was called, a guard produced a different verdict, or an additional recovery attempt occurred.

Once I found the divergent span, I would correlate it with the relevant LangGraph `thread_id` and checkpoint to inspect the workflow state at that point—such as the selected evidence, current result, recovery count, or next action. That helps distinguish whether the difference came from model behavior, retrieval, state assembly, or an operational failure.

So my debugging approach is: **trace both runs, compare their trajectories, find the first divergent span, and then inspect the corresponding checkpoint and state to identify the root cause.**”

```
Run A trace ──┐
              ├── compare span-by-span
Run B trace ──┘
                    ↓
            first divergence
                    ↓
       inspect checkpoint/state
                    ↓
              root cause
```
Debugging scenario:use use KQL to locate the execution around the incident timestamp, get the operation_Id/trace, and then reconstruct the spans
```
Known:
CAR / execution ID
+
approximate failure timestamp
        ↓
Application Insights + KQL
        ↓
find matching telemetry
        ↓
get operation_Id / trace_id
        ↓
retrieve requests + dependencies + traces + exceptions
        ↓
order by timestamp
        ↓
reconstruct execution trajectory
        ↓
find failing/divergent span
        ↓
use thread_id/checkpoint_id
        ↓
inspect LangGraph state
```

### Monitor health of the Application

```
CHAT
├── Latency → request start → response end; track p95
├── Failures → failed turns / total turns
└── Agent efficiency → tool calls or supervisor iterations / successful turn

CAR BATCH
├── Backlog → queue depth + oldest message age
├── Completion time → job accepted → CAR completed; track p95
└── Failures/retries → failed jobs / total jobs + retries / job

AGENTIC EVAL
├── Quality improvement → pass rate before vs after recovery
├── Human/unresolved → HITL rate + unresolved rate
└── Recovery cost → extra tokens, calls, $, and latency per recovery
```
App telemetry → OpenTelemetry → Application Insights → KQL → Workbook → Alert

### Fraud Detection 
**Question: Once a fraud model is deployed in production, how do you monitor drift? What tools do you use?**

**Remember: Baseline → Capture → Compare → Alert → Validate → Act.**

Once a fraud model is deployed, I monitor two things: **whether production data is changing, and whether fraud detection quality is deteriorating.** My approach has six steps:

1. **Baseline:** Stable version of normal that was used to train the model.

2. **Capture:** Features actually used by the model to score;

3. **Compare:** run scheduled checks against numerical (mean, std dev, % of values in each range); categorical(% in each cat;); Data quality(missing data)  -- measure distribution of input data vs baseline data

**Use of Evidently
Supply Baseline; inputs to model ;Production scoring records and validated scores 
Drift: Evidently compares baseline features against production features. This needs no fraud labels.
Performance: Your job joins predictions with confirmed outcomes by transaction ID, then Evidently calculates precision, recall and other metrics.

Features = what the model saw. Prediction = what it said. Outcome = what actually happened.

### Sub 220ms latency 
```
Client
  → ALB / API Gateway
  → ECS / EKS / SageMaker model service
      ├── Redis / ElastiCache: retrieve real-time transaction features
      ├── XGBoost model loaded in application memory
      └── Return risk score / decision
```
Redis is a fast, in-memory key–value database used here to cache model features and track transaction status for duplicate-request handling.
Redis is used for rolling features = Feature data + overhead/headroom ≈ 7–10 GB
and to save idempotency - short-circuting key


### how to get 44 to 88% F1 increase
Model: Fine-tune DistilBERT on labeled complaints using one classification head with five outputs, one per category. Fine-tuning adapts its representations to your complaint language. Hugging Face

Training: Use class-weighted cross-entropy, giving rare categories higher weights so errors on those examples contribute more to the training loss. PyTorch 2.4 documentation

Evaluation: Use macro F1 to give every category equal importance when comparing models. Macro F1 measures performance; the class-weighted loss provides the stronger training penalty.
The five outputs define the task; fine-tuning and the training loss drive learning; F1 measures the result.

### SHAP score - to see which features contributed most to the risk score
SHAP only needs input feature and model artifact to show contributions that that one transaction

Background worker: Compute SHAP in batches using recorded features and the matching model version. Include flagged transactions and a representative sample of normal transactions.

Overall monitoring: Aggregate contributions—for example, average absolute SHAP value per feature—to see which features influence predictions most. Compare these across time for the same model versio