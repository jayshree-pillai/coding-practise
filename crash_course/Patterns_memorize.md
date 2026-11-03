# LangChain — Must-Memorize Snippets

Each Python snippet runs independently after setup.

## Setup

```bash
pip install langchain langchain-openai python-dotenv pydantic azure-search-documents
```

Create `.env`:
```env
OPENAI_API_KEY=your-key
```

## 1. Call a model

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

response = model.invoke("Explain revenue in one sentence.")
print(response.text)
```

**Critical notes:**

- `response` is an `AIMessage`; `.text` extracts its text.
- `load_dotenv()` loads `.env` into environment variables; the model reads `OPENAI_API_KEY`.

## 2. Prompt → model → string

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the report in one sentence."),
    ("human", "Company: {company}\nReport: {report_text}"),
])

chain = prompt | model | StrOutputParser()

answer = chain.invoke({
    "company": "Acme",
    "report_text": "Revenue grew 12%.",
})

print(answer)
```

**Critical notes:**

- The chain's first step determines its input; dictionary keys must match prompt variables.
- `prompt.invoke(...)` only formats messages. The model generates the answer; `StrOutputParser()` returns its text as a string.

## 3. Structured output

```python
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class Report(BaseModel):
    company: str
    growth_percent: float = Field(description="Use 12 for 12%.")

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")
structured_model = model.with_structured_output(Report)

result = structured_model.invoke("Acme's revenue grew 12%.")

print(result.company)
print(result.growth_percent)
```

**Critical notes:**

- Passing a Pydantic class returns a validated object of that class.
- Schema validation checks structure and types, not factual accuracy.

## 4. RunnableLambda

```python
from langchain_core.runnables import RunnableLambda

prepare = RunnableLambda(
    lambda text: {"report_text": text.strip()}
)

result = prepare.invoke("  Revenue grew 12%.  ")
print(result)
# {"report_text": "Revenue grew 12%."}
```

**Critical note:** Wraps a Python function so it can participate in a runnable chain. It does not inherently call a model.

## 5. RunnableParallel

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}"),
])

summary_chain = prompt | model | StrOutputParser()

parallel = RunnableParallel(
    summary=summary_chain,
    character_count=RunnableLambda(
        lambda data: len(data["report_text"])
    ),
)

result = parallel.invoke({"report_text": "Revenue grew 12%."})

print(result["summary"])
print(result["character_count"])  # 17
```

**Critical notes:**

- Both branches receive the same original input and run concurrently.
- One branch cannot use the other branch's result; the character count measures the original report.

## 6. Extract, pass through, and assign

```python
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough

data = {"question": "  What was revenue?  "}

print(itemgetter("question")(data))
print(RunnablePassthrough().invoke(data))

enrich = RunnablePassthrough.assign(
    search_query=lambda data: data["question"].strip()
)

print(enrich.invoke(data))
# {
#     "question": "  What was revenue?  ",
#     "search_query": "What was revenue?"
# }
```

**Critical notes:**

- `itemgetter("question")` extracts one value; `RunnablePassthrough()` passes through the entire input.
- `.assign()` requires a dictionary and adds or overwrites keys in the returned dictionary.
- Fields computed in the same `.assign()` cannot use each other's newly computed values.

## 7. Batch

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

responses = model.batch(
    ["Define revenue.", "Define profit."],
    config={"max_concurrency": 2},
)

for response in responses:
    print(response.text)
```

**Critical note:** Results preserve input order even if calls finish in a different order. `max_concurrency` limits simultaneous work.

## 8. Async invocation and batch

```python
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

async def main():
    response = await model.ainvoke("Define revenue.")
    print(response.text)

    responses = await model.abatch(
        ["Define revenue.", "Define profit."],
        config={"max_concurrency": 2},
    )
    for response in responses:
        print(response.text)

asyncio.run(main())
```

**Critical notes:**

- Calling `ainvoke(...)` only creates a coroutine; await or schedule it to execute.
- Consecutive `await` calls run sequentially. `abatch()` handles multiple inputs concurrently.
- In a notebook with an active event loop, use `await main()` instead of `asyncio.run(main())`.
| Command | What it does |
|---|---|
| `asyncio.run(main())` | **Creates** an event loop → runs `main()` → **closes** the loop afterward |
| `await main()` | Runs `main()` using the **existing** event loop; waits for its result while allowing other async tasks to run |

## 9. Streaming

```python
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

for chunk in model.stream("Explain revenue briefly."):
    print(chunk.text, end="", flush=True)
print()

async def main():
    async for chunk in model.astream("Explain profit briefly."):
        print(chunk.text, end="", flush=True)
    print()

asyncio.run(main())
```

**Critical note:** Direct model streaming yields `AIMessageChunk` objects. Streaming a chain ending with `StrOutputParser()` yields strings.

## 10. Manual two-tool execution loop

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

@tool
def get_revenue(company: str, year: int):
    """Get a company's annual revenue."""
    data = {("ACME", 2024): 100000}
    return data.get((company.strip().upper(), year))

@tool
def get_employee(company: str, year: int):
    """Get a company's employee count."""
    data = {("ACME", 2024): 100}
    return data.get((company.strip().upper(), year))

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

tools = [get_revenue, get_employee]
model_with_tools = model.bind_tools(tools)
tools_by_name = {t.name: t for t in tools}

messages = [
    HumanMessage(
        content="Use both tools: Acme's revenue and employee count for 2024."
    )
]

for _ in range(5):
    response = model_with_tools.invoke(messages)
    messages.append(response)

    if not response.tool_calls:
        print(response.text)
        break

    for call in response.tool_calls:
        selected_tool = tools_by_name[call["name"]]
        result = selected_tool.invoke(call["args"])

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=call["id"],
            )
        )
else:
    raise RuntimeError("No final answer within 5 model calls.")
```

**Critical notes:**

- Binding tools lets the model request them; `selected_tool.invoke(...)` actually executes them.
- Append the model's message before its tool results; match each result using `tool_call_id`.
- Handle every tool call in the response.
- The `else` belongs to the outer loop and runs when all five iterations finish without `break`.

## 11. create_agent

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

@tool
def get_revenue(company: str, year: int):
    """Get a company's annual revenue."""
    data = {("ACME", 2024): 100000}
    return data.get((company.strip().upper(), year))

@tool
def get_employee(company: str, year: int):
    """Get a company's employee count."""
    data = {("ACME", 2024): 100}
    return data.get((company.strip().upper(), year))

load_dotenv()
model = ChatOpenAI(model="gpt-5-nano")

agent = create_agent(
    model=model,
    tools=[get_revenue, get_employee],
    system_prompt="Use tools to look up company figures. Do not guess.",
)

result = agent.invoke({
    "messages": [
        HumanMessage(
            content="Find Acme's revenue and employee count for 2024."
        )
    ]
})

print(result["messages"][-1].text)
```

**Critical notes:**

- The agent manages tool execution, tool-result messages, and repeated model calls.
- Its result is a state dictionary, not a single `AIMessage`.

## 12. Azure Search → context → answer

Add to `.env`:
```env
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_INDEX=your-index
AZURE_SEARCH_API_KEY=your-search-key
```

```python
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["AZURE_SEARCH_INDEX"],
    credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]),
)

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer only from context. If insufficient, say you don't know."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

chain = prompt | model | StrOutputParser()
question = "What was Acme's revenue in 2024?"

results = client.search(
    search_text=question,
    search_fields=["content"],
    select=["content"],
    top=3,
)

context = "\n\n".join(
    row["content"] for row in results if row.get("content")
)

if context.strip():
    answer = chain.invoke({"context": context, "question": question})
    print(answer)
else:
    print("No matching content found.")
```

**Critical notes:**

- Requires an existing index with a searchable, retrievable text field named `content`.
- `search_fields` controls where to search; `select` controls which fields are returned.
- This uses keyword search, with Azure Search retrieving evidence and OpenAI generating the answer.

# LangGraph — Must-Memorize Interview Snippets

Memorize these 8 patterns in order. Each Python block is standalone.

Keep required state/tool annotations; skip optional function annotations.

## 1. Build a Graph, Return Updates, and Choose the Next Node

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    question: str
    prompt: str

def clean(state):
    return {"question": state["question"].strip()}

def route(state):
    return "build_prompt" if state["question"] else END

def build_prompt(state):
    return {"prompt": f"Answer: {state['question']}"}

builder = StateGraph(State)
builder.add_node("clean", clean)
builder.add_node("build_prompt", build_prompt)
builder.add_edge(START, "clean")
builder.add_conditional_edges("clean", route)
builder.add_edge("build_prompt", END)

graph = builder.compile()
data = {"question": "  What was revenue?  ", "prompt": ""}

for update in graph.stream(data, stream_mode="updates"):
    print(update)
```

**Critical notes:**

- Nodes return **partial state updates**; omitted fields retain their values.
- Routers return **destinations**, not state updates.
- `compile()` builds the runnable graph; it does not execute it.
- `graph.invoke(data)` executes the graph and returns the final state.
- Iterating over `graph.stream(...)` executes the graph while yielding progress.
- `"updates"` gives node updates; `"values"` gives full state snapshots.
- Calling `invoke()` and then `stream()` executes the graph twice.

## 2. Parallel Branches → Reducer → Join

```python
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    evidence: Annotated[list[str], add]
    summary: str

def revenue(state):
    return {"evidence": ["Revenue grew 12%"]}

def debt(state):
    return {"evidence": ["Debt fell 5%"]}

def summarize(state):
    return {"summary": "; ".join(state["evidence"])}

builder = StateGraph(State)
builder.add_node("revenue", revenue)
builder.add_node("debt", debt)
builder.add_node("summarize", summarize)
builder.add_edge(START, "revenue")
builder.add_edge(START, "debt")
builder.add_edge(["revenue", "debt"], "summarize")
builder.add_edge("summarize", END)

graph = builder.compile()
print(graph.invoke({"evidence": [], "summary": ""}))
```

**Critical notes:**

- Concurrent updates to the same field need a suitable reducer.
- `Annotated[list[str], add]` combines lists using concatenation.
- Return **only new items**; returning existing items again causes duplication.
- `add_edge(["revenue", "debt"], "summarize")` waits for both branches.
- Parallel nodes see the state available at the start of their step.
- LangGraph collects their updates and applies the reducer.
- This does not protect external shared mutable objects from races.
- Do not infer completion order from the final list order.

## 3. MessagesState + Checkpointing + Thread ID

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

def reply(state):
    return {"messages": [{"role": "assistant", "content": "Noted."}]}

builder = StateGraph(MessagesState)
builder.add_node("reply", reply)
builder.add_edge(START, "reply")
builder.add_edge("reply", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "chat-1"}}

graph.invoke(
    {"messages": [{"role": "user", "content": "Review revenue."}]},
    config
)

result = graph.invoke(
    {"messages": [{"role": "user", "content": "Also review debt."}]},
    config
)

print(len(result["messages"]))  # 4
```

**Critical notes:**

- Same `thread_id` + same checkpointer → saved conversation state.
- A different `thread_id` separates the conversation state.
- Send **new messages only**.
- `MessagesState` uses the `add_messages` reducer.
- A new message ID appends a message.
- An existing message ID replaces that message in its existing position.
- Matching is by **ID**, not by message text.
- `thread_id` identifies the conversation; message `id` identifies one message.
- `InMemorySaver` loses data when the process ends.

## 4. Model → Tools → Model Loop

Requires `langgraph`, `langchain`, `langchain-openai`, and `OPENAI_API_KEY`.

```python
from langgraph.graph import StateGraph, MessagesState, START
from langchain.tools import tool, ToolNode
from langchain.tools.tool_node import tools_condition
from langchain_openai import ChatOpenAI

@tool
def get_revenue(company: str, year: int):
    """Look up annual revenue in USD."""
    return {("Acme", 2025): 120_000_000}.get((company, year))

model = ChatOpenAI(model="gpt-5-nano").bind_tools([get_revenue])

def call_model(state):
    return {"messages": [model.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("model", call_model)
builder.add_node("tools", ToolNode([get_revenue]))
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition)
builder.add_edge("tools", "model")

graph = builder.compile()
result = graph.invoke(
    {"messages": [{
        "role": "user",
        "content": "Use get_revenue for Acme's 2025 revenue."
    }]},
    config={"recursion_limit": 10}
)

print(result["messages"][-1].content)
```

**Critical notes:**

- The model requests tool calls; `ToolNode` executes them.
- `tools_condition` routes to `"tools"` when the model requests a tool.
- Otherwise, `tools_condition` routes to `END`.
- Keep the node named `"tools"` with this default routing.
- The `"tools" → "model"` edge lets the model use the tool results.
- `recursion_limit` limits graph supersteps, not individual tool calls.
- Exceeding the limit raises `GraphRecursionError`.

## 5. Pause → Inspect → Resume → Inspect History

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    report: str
    status: str

def review(state):
    approved = interrupt({"report": state["report"]})
    return {"status": "approved" if approved else "rejected"}

builder = StateGraph(State)
builder.add_node("review", review)
builder.add_edge(START, "review")
builder.add_edge("review", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "report-1"}}

paused = graph.invoke(
    {"report": "Revenue grew 12%.", "status": "pending"},
    config
)
print(paused["__interrupt__"])

snapshot = graph.get_state(config)
print(snapshot.values, snapshot.next)

result = graph.invoke(Command(resume=True), config)
print(result["status"])  # approved

for snapshot in graph.get_state_history(config):
    print(snapshot.values, snapshot.next)
```

**Critical notes:**

- `interrupt()` pauses execution and exposes its payload to the caller.
- Both `resume=True` and `resume=False` continue execution.
- The resume value becomes the return value of `interrupt()`.
- **Your code** maps that value to `"approved"` or `"rejected"`.
- Resume with the same thread/checkpointer.
- The interrupted node restarts from its beginning.
- Side effects before `interrupt()` can therefore repeat.
- `snapshot.values` contains saved state.
- `snapshot.next` contains pending node names.
- An empty `snapshot.next` means no pending work, not necessarily business success.
- `get_state_history()` returns checkpoints newest first.
- Reading state or history does not execute the graph.

## 6. Update State and Route in the Same Node

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class State(TypedDict):
    approved: bool
    status: str

def decide(state):
    if state["approved"]:
        return Command(update={"status": "approved"}, goto="finish")
    return Command(update={"status": "rejected"}, goto=END)

def finish(state):
    print(state["status"])
    return {}

builder = StateGraph(State)
builder.add_node("decide", decide)
builder.add_node("finish", finish)
builder.add_edge(START, "decide")
builder.add_edge("finish", END)

graph = builder.compile()
print(graph.invoke({"approved": True, "status": "pending"}))
```

**Critical notes:**

- `Command(update=..., goto=...)` updates state and chooses the next destination.
- Return it **from a node**.
- `Command(resume=...)` serves a different purpose: pass it **to the graph** to resume an interrupt.
- `goto` does not cancel static outgoing edges.
- Do not add an unconditional `"decide" → "finish"` edge here.
- Plain `Command(update=..., goto=...)` does not require a checkpointer.

## 7. Retry a Failing Node

```python
from itertools import count
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    revenue: int

attempts = count(1)

def fetch_revenue(state):
    if next(attempts) < 3:
        raise TimeoutError("Service unavailable")
    return {"revenue": 120_000_000}

builder = StateGraph(State)
builder.add_node(
    "fetch_revenue",
    fetch_revenue,
    retry_policy=RetryPolicy(
        max_attempts=3,
        retry_on=TimeoutError
    )
)
builder.add_edge(START, "fetch_revenue")
builder.add_edge("fetch_revenue", END)

graph = builder.compile()
print(graph.invoke({"revenue": 0}))
```

**Critical notes:**

- `max_attempts=3` means **one initial attempt + two retries**.
- The node must raise an exception matching `retry_on`.
- Returning an error dictionary does not trigger retries.
- The failing node is retried, not the entire graph from `START`.
- External side effects can repeat; retries do not undo them.
- If all attempts fail, the exception propagates.
- The counter only simulates failures.
- A retry policy does not itself impose an execution timeout.

## 8. Dynamic Parallel Work with Send

```python
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    companies: list[str]
    results: Annotated[list[str], add]

def dispatch(state):
    return [
        Send("review_company", {"company": company})
        for company in state["companies"]
    ]

def review_company(state):
    return {"results": [f"{state['company']}: reviewed"]}

builder = StateGraph(State)
builder.add_node("review_company", review_company)
builder.add_conditional_edges(START, dispatch)
builder.add_edge("review_company", END)

graph = builder.compile()
result = graph.invoke({
    "companies": ["Acme", "Globex"],
    "results": []
})
print(sorted(result["results"]))
```

**Critical notes:**

- Register one worker node; execute it multiple times.
- Each `Send` specifies a destination and that worker's input.
- The worker receives the custom payload, not automatically the entire parent state.
- The reducer combines the workers' returned results.
- Return singleton lists containing only each worker's new result.
- One worker reaching `END` does not cancel the other workers.
- Do not depend on parallel completion order.
- `sorted()` here only makes the displayed output predictable.

## Practice Priority

Rebuild patterns **1–5 without looking**, then explain:

- Why concurrent writes need a reducer.
- How a thread ID connects calls to saved state.
- How the tool loop decides when to stop.
- Why code before an interrupt can execute again.

Then practice patterns **6–8**.

# Pydantic v2 — Must-Memorize Interview Snippets

Practice snippets 1–5 first, then aliases and discriminated unions. Each code block stands on its own.

## 1. Define, validate, and serialize a request

```python
from pydantic import BaseModel, ConfigDict, Field

class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    top_k: int = Field(default=5, ge=1, le=20)

request = SearchRequest.model_validate({"question": "What was revenue?"})
print(request.model_dump())
# {'question': 'What was revenue?', 'top_k': 5}
```

- Use `SearchRequest(question="What was revenue?")` when passing fields directly.
- Use `SearchRequest.model_validate(data)` when you already have a dictionary. Both forms validate the input.
- `extra="forbid"` rejects unexpected keys. Add `strict=True` to the integer field to reject `"3"` as input.

## 2. Clean a field before checking its constraints

```python
from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    question: str = Field(min_length=1)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value
```

- `mode="before"` receives raw input. Trimming `"   "` first lets `min_length=1` reject the empty string.
- Use the default `after` mode when your function needs the already parsed value.
- Return the field value you want stored.

## 3. Validate a rule involving two fields

```python
from pydantic import BaseModel, model_validator

class ReportRequest(BaseModel):
    start_year: int
    end_year: int

    @model_validator(mode="after")
    def check_year_range(self):
        if self.end_year < self.start_year:
            raise ValueError("end_year must be >= start_year")
        return self
```

An `after` model validator receives `self` after the fields validate. Remember **`return self`** here. A field validator returns the field value.

## 4. Validate nested objects and give a list a default

```python
from pydantic import BaseModel, Field

class Source(BaseModel):
    filename: str
    page: int

class Answer(BaseModel):
    text: str
    sources: list[Source] = Field(default_factory=list)

answer = Answer.model_validate({
    "text": "Revenue grew by 12%.",
    "sources": [{"filename": "annual_report.pdf", "page": 3}],
})
print(answer.sources[0].page)  # 3
```

Each supplied source dictionary becomes a `Source`. When `sources` is omitted, Pydantic calls `list()` to create a fresh list. Pass `list` without parentheses.

## 5. Read structured validation errors

```python
from pydantic import BaseModel, Field, ValidationError

class SearchRequest(BaseModel):
    top_k: int = Field(ge=1, le=20)

try:
    SearchRequest.model_validate({"top_k": 0})
except ValidationError as exc:
    for error in exc.errors():
        print(error["loc"], error["type"], error["msg"])
```

- `loc` is the path to the failure. `("sources", 0, "page")` identifies `page` on the first source.
- `type` is the error code your program can check.
- `msg` is the readable explanation.

## 6. Map an external field name to a Python attribute

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    top_k: int = Field(alias="topK")

request = SearchRequest.model_validate({"topK": 3})
print(request.top_k)                     # 3
print(request.model_dump(by_alias=True))  # {'topK': 3}
```

The payload uses `topK`. Python accesses `top_k`. Pass `by_alias=True` to export `topK`.

## 7. Select a payload shape using a discriminator

```python
from typing import Literal
from pydantic import BaseModel, Field

class FileSource(BaseModel):
    kind: Literal["file"]
    filename: str

class WebSource(BaseModel):
    kind: Literal["web"]
    url: str

class SearchRequest(BaseModel):
    source: FileSource | WebSource = Field(discriminator="kind")
```

Pydantic reads `source.kind` to choose the model. A source with `kind="file"` must provide `filename`. A source with `kind="web"` must provide `url`.

For recall practice, start from a requirement such as “reject a question containing only spaces” or “reject an end year earlier than the start year.” Choose the validator and write the snippet from memory.

# FastAPI + Requests: Must-Know Interview Snippets

Memorize the structure and understand each line.

Each server example is a separate `main.py`; run it with:

```bash
fastapi dev main.py
```

Client examples need the corresponding server running.

## 1. GET endpoint: path parameters + query parameters

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/companies/{company_id}/reports/{year}")
def get_report(
    company_id: int,
    year: int,
    top_k: int = Query(default=3, ge=1, le=10),
):
    return {
        "company_id": company_id,
        "year": year,
        "top_k": top_k,
    }
```

Example request:

```text
/companies/42/reports/2024?top_k=5
```

**Remember:**

- Placeholders in the route are path parameters.
- `top_k` is a query parameter with a default of `3`.
- `ge=1, le=10` means 1–10 inclusive.
- Invalid input produces `422`.

## 2. POST endpoint: validated body + response model

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

class QuestionResponse(BaseModel):
    question: str

@app.post("/questions", response_model=QuestionResponse)
def ask_question(payload: QuestionRequest):
    return {
        "question": payload.question,
        "internal_note": "Do not expose",
    }
```

**Remember:**

- `payload: QuestionRequest` validates the incoming JSON body.
- Access fields using `payload.question`.
- `response_model` validates and filters outgoing data: `internal_note` is excluded.
- Invalid request → `422`.
- Invalid data returned by your handler → server error.

## 3. Raise a meaningful API error

```python
from fastapi import FastAPI, HTTPException, Path

app = FastAPI()
companies = {42: "Acme"}

@app.get("/companies/{company_id}")
def get_company(company_id: int = Path(gt=0)):
    if company_id not in companies:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return {"company": companies[company_id]}
```

**Remember:**

- `raise HTTPException(...)` stops execution.
- `0` fails input validation → `422`.
- `999` passes validation but fails the company lookup → `404`.
- Returning an error dictionary alone would still use the default `200`.

## 4. Call an API: request → status check → JSON

### GET with query parameters

Targets the endpoint in example 1.

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/companies/42/reports/2024",
    params={"top_k": 5},
    timeout=5,
)

response.raise_for_status()
data = response.json()
print(data)
```

### POST with a JSON body

Targets the endpoint in example 2.

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/questions",
    json={"question": "What was revenue in 2024?"},
    timeout=5,
)

response.raise_for_status()
data = response.json()
print(data)
```

**Remember:**

- `params=` sends query parameters.
- `json=` sends a JSON body.
- Set a timeout.
- Check HTTP status before parsing the response.
- Successfully parsing JSON does not prove the HTTP request succeeded.

## 5. Handle client failures separately

```python
import requests
from requests.exceptions import (
    Timeout, ConnectionError, HTTPError, JSONDecodeError,
)

try:
    response = requests.get(
        "http://127.0.0.1:8000/companies/42",
        timeout=(2, 3),
    )
    response.raise_for_status()
    print(response.json())

except Timeout:
    print("Timed out")

except ConnectionError:
    print("Could not connect")

except HTTPError as error:
    print("HTTP error:", error.response.status_code)

except JSONDecodeError:
    print("Response was not valid JSON")
```

**Remember:**

- Network failure, HTTP failure, and JSON parsing failure are separate problems.
- `timeout=(2, 3)` specifies connection/read timeouts.
- It is not a five-second overall deadline.
- `error.response.status_code` gives the status associated with an `HTTPError`.

## 6. Depends + bearer-token authentication

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer

app = FastAPI()
bearer = HTTPBearer(auto_error=False)

def get_current_user(auth=Depends(bearer)):
    if auth is None or auth.credentials != "demo-token":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "demo-user"

@app.get("/me")
def read_user(user=Depends(get_current_user)):
    return {"user": user}
```

The caller sends `headers={"Authorization": "Bearer demo-token"}` in its Requests call.

**Remember:**

- `Depends(get_current_user)` passes the function to FastAPI.
- FastAPI calls it and injects its returned value into `user`.
- Do not write `Depends(get_current_user())`.
- Check `auth is None` before accessing `auth.credentials`.
- The fixed token is a learning example.
- `HTTPBearer` extracts credentials; your authentication logic must validate them.

## 7. Call another API from async code

```python
import httpx

async def fetch_company(url):
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

**Remember:**

- Inside an async endpoint, use `company = await fetch_company(url)`.
- `async with` manages the client's lifetime.
- `await client.get(...)` allows other tasks to run during network waits.
- This function resumes after the response is available.
- `.json()` needs no `await` because the response body is already loaded.
- Calling `fetch_company(url)` without awaiting or scheduling it only creates a coroutine object.
- Calling blocking `requests.get()` directly inside `async def` blocks the event-loop thread.

## 8. Reuse a Session + configure bounded retries

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

retries = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods={"GET"},
    raise_on_status=False,
)

with requests.Session() as session:
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    for _ in range(3):
        response = session.get(
            "http://127.0.0.1:8000/companies/42",
            timeout=(2, 3),
        )
        response.raise_for_status()
        print(response.json())
```

**Remember:**

- Keep the Session outside the loop to reuse connections.
- Each loop iteration makes a fresh request.
- A Session does not make Requests asynchronous.
- `total=2` permits up to two retries per request: three attempts.
- `allowed_methods` restricts status/read retries; connection-error retries have separate semantics.
- `raise_on_status=False` returns the final HTTP response after status retries are exhausted.
- `response.raise_for_status()` then checks that final response.
- Before retrying a POST, consider whether the first attempt already created something.

## Practice priority

Write **1–7 from a blank file** until they feel familiar.

For **8**, understand the settings and recognize the adapter recipe. The particular retry counts and delays depend on the application.