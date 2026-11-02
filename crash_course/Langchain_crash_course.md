# Langchain crash course

## 1. Model calls and messages

### Important notes

- `init_chat_model(...)` configures the model client. `model.invoke(messages)` sends the request to the hosted model.
- `SystemMessage` supplies instructions; `HumanMessage` supplies the user's input.
- The response is an `AIMessage`. `response.text` gives its text; `response.usage_metadata` exposes usage information when available. The underlying `content` can be a string or a list of content blocks.

```bash
python -m pip install -U "langchain[openai]"
```

```python
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage

model = init_chat_model("openai:gpt-5-nano")

messages = [
    SystemMessage(content="Summarize the supplied report excerpt in one sentence."),
    HumanMessage(content="Revenue increased 10%, while operating profit fell 5%."),
]

response = model.invoke(messages)

print(response.text)
print(response.usage_metadata)
```

```python
print(response)       # Inspect the entire message object.
print(response.text)  # Extract only the generated text.
```

## 2. ChatPromptTemplate and ChatPromptValue

### Important notes

- `ChatPromptTemplate` stores reusable message templates and placeholders such as `{report_text}`.
- `prompt.invoke({...})` fills the placeholders and returns a `ChatPromptValue` containing the completed messages. This formatting step does not call the model.
- `prompt_value.to_messages()` exposes those messages; `model.invoke(prompt_value)` sends them to the model.
- Input keys must match the placeholders exactly, including capitalization.

```python
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

model = init_chat_model("openai:gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the supplied report excerpt in one sentence."),
    ("human", "{report_text}"),
])

prompt_value = prompt.invoke({
    "report_text": "Revenue increased 10%, while operating profit fell 5%."
})

response = model.invoke(prompt_value)

print(response.text)
```

```python
print(prompt_value.to_messages())
```


### Matching input keys

```python
# Wrong: the template expects "report_text".
prompt.invoke({"text": "Revenue increased 10%."})

# Correct:
prompt.invoke({"report_text": "Revenue increased 10%."})
```

## 3. ChatOpenAI versus init_chat_model

### Important notes

- `ChatOpenAI(model="gpt-5-nano")` selects the OpenAI integration directly.
- `init_chat_model("openai:gpt-5-nano")` is a common initialization helper that selects the provider from the configuration.
- Both examples configure a model client; `.invoke(...)` sends the model request. The remaining examples use `ChatOpenAI` directly.

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-5-nano")
```

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5-nano")
```

```python
response = model.invoke(prompt_value)
```

## 4. LCEL — composing a chain with |

### Important notes

- `chain = prompt | model` connects the steps; it does not execute them. `chain.invoke(...)` executes the sequence.
- Each step's output becomes the next step's input: input dictionary, then `ChatPromptValue`, then `AIMessage`.
- The company's input key is `company`, matching `{company}`. The literal label `Company:` in the prompt can have different capitalization.
- Both `ChatPromptTemplate([...])` and `ChatPromptTemplate.from_messages([...])` are valid forms used in our examples.

### Separate steps

```python
prompt_value = prompt.invoke({"report_text": "Revenue increased 10%."})
response = model.invoke(prompt_value)
```

### Composed steps

```python
chain = prompt | model

response = chain.invoke({"report_text": "Revenue increased 10%."})
```

### Complete example

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model

response = chain.invoke({
    "report_text": "Revenue increased 10%, while operating profit fell 5%."
})

print(response.text)
```

### Company and report exercise — corrected code

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the supplied excerpt in one sentence."),
    ("human", "Company:{company}\nReport:{report_text}")
])

chain = prompt | model

response = chain.invoke({
    "company": "Acme",
    "report_text": "Revenue grew 12%"
})

print(response.text)
```

## 5. StrOutputParser

### Important notes

- `StrOutputParser()` extracts the model's text, so the chain returns a Python `str`.
- Use `print(response)` after this parser. Calling `response.text` raises an error because the response is already a string.
- The parser does not make another model call. The returned string does not carry the original message's usage metadata or tool-call information.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the supplied excerpt in one sentence."),
    ("human", "Company:{company}\nReport:{report_text}")
])

chain = prompt | model | StrOutputParser()

response = chain.invoke({
    "company": "Acme",
    "report_text": "Revenue grew 12%"
})

print(response)
```

### Inspecting the return type

```python
print(type(response))  # <class 'str'>
print(response.text)   # AttributeError: a string has no .text attribute
```

## 6. Structured output with Pydantic

### Important notes

- `Report` defines the requested fields and their types. `model.with_structured_output(Report)` configures structured output using that schema.
- In this example, the chain returns a Pydantic `Report` instance. Read fields with `response.company` and `response.revenue_growth_percent`.
- Do not append `StrOutputParser()` to this example; the desired result is the structured object.
- Schema validation checks structure and types, not factual accuracy. The prompt explicitly requests `12` for `12%` so the percentage unit is clear.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

class Report(BaseModel):
    company: str
    revenue_growth_percent: float

model = ChatOpenAI(model="gpt-5-nano")

structured_model = model.with_structured_output(Report)

prompt = ChatPromptTemplate([
    ("system", "Extract the company and revenue growth. Use 12 for 12%."),
    ("human", "{report_text}")
])

chain = prompt | structured_model

response = chain.invoke({
    "report_text": "Acme's revenue grew 12%."
})

print(response.company)
print(response.revenue_growth_percent)
```

### Example output

```text
Acme
12.0
```

## 7. RunnableLambda

### Important notes

- `RunnableLambda(prepare_input)` wraps an ordinary Python function so it can be a chain step. Pass the function itself, without calling it.
- `prepare_input` strips the input string and returns the dictionary expected by the prompt.
- The first step determines the chain's input here: call it with a string. The next step receives `{"report_text": ...}`.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

def prepare_input(text):
    return {"report_text": text.strip()}

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the supplied report in one sentence."),
    ("human", "{report_text}")
])

chain = RunnableLambda(prepare_input) | prompt | model | StrOutputParser()

response = chain.invoke("  Acme's revenue grew 12%.  ")

print(response)
```

### prepare_input — input and output

```python
# Receives:
"  Acme's revenue grew 12%.  "

# Returns:
{"report_text": "Acme's revenue grew 12%."}
```

## 8. RunnableParallel

### Important notes

- Both branches receive the same input dictionary and can run concurrently; one branch does not consume the other's result.
- `summary` and `risks` are the output keys chosen when constructing `RunnableParallel`.
- This example makes two model calls. A successful `.invoke()` returns after both branches finish, with a dictionary containing their string results.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

model = ChatOpenAI(model="gpt-5-nano")

summary_prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

risks_prompt = ChatPromptTemplate([
    ("system", "List only the risks explicitly mentioned in the report."),
    ("human", "{report_text}")
])

summary_chain = summary_prompt | model | StrOutputParser()
risks_chain = risks_prompt | model | StrOutputParser()

parallel = RunnableParallel(
    summary=summary_chain,
    risks=risks_chain
)

response = parallel.invoke({
    "report_text": "Acme's revenue grew 12%. A major customer may leave."
})

print(response["summary"])
print(response["risks"])
```

### Example response

```text
{
    "summary": "Acme's revenue grew 12%, but a major customer may leave.",
    "risks": "Potential loss of a major customer."
}
```

## 9. RunnablePassthrough.assign

### Important notes

- `RunnablePassthrough.assign(...)` requires dictionary input. It retains the original fields and adds the computed result.
- `summary=summary_chain` runs the summary chain on that input and stores its output under `summary`.
- Changing the keyword to `answer` changes the output key. Assigning an existing key replaces that key's value.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "Company: {company}\nReport: {report_text}")
])

summary_chain = prompt | model | StrOutputParser()

chain = RunnablePassthrough.assign(summary=summary_chain)

response = chain.invoke({
    "company": "Acme",
    "report_text": "Revenue grew 12%."
})

print(response)
```

### Example response

```text
{
    "company": "Acme",
    "report_text": "Revenue grew 12%.",
    "summary": "Acme's revenue grew 12%."
}
```

### Choosing the added key

```python
chain = RunnablePassthrough.assign(answer=summary_chain)
```

## 10. batch

### Important notes

- `.batch(reports)` runs the same chain for multiple inputs and returns a list of results.
- Results stay in input order even if requests finish in a different order.
- `max_concurrency=2` limits simultaneous work. These three inputs still produce three logical model calls.
- This is client-side batching, separate from a provider's discounted Batch API.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model | StrOutputParser()

reports = [
    {"report_text": "Acme's revenue grew 12%."},
    {"report_text": "Beta's operating profit fell 5%."},
    {"report_text": "Gamma opened two new offices."}
]

results = chain.batch(reports, config={"max_concurrency": 2})

for result in results:
    print(result)
```

### Result order

```python
results[0]  # Acme's summary
results[1]  # Beta's summary
results[2]  # Gamma's summary
```

## 11. ainvoke

### Important notes

- `.ainvoke(...)` returns a coroutine. `await chain.ainvoke(...)` obtains the completed response.
- Awaiting allows the event loop to run other scheduled work while this call waits; it does not inherently make one model request faster.
- Use `await` inside `async def`. `asyncio.run(main())` is the script entry point used in this example.

```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model | StrOutputParser()

async def main():
    response = await chain.ainvoke({
        "report_text": "Acme's revenue grew 12%."
    })
    print(response)

asyncio.run(main())
```

### Missing await

```python
response = chain.ainvoke({"report_text": "Revenue grew 12%."})
# response is a coroutine, not the generated answer.
```

### With await — inside an async function

```python
response = await chain.ainvoke({"report_text": "Revenue grew 12%."})
```

## 12. abatch

### Important notes

- `await chain.abatch(reports)` processes multiple inputs asynchronously and returns their results in input order.
- `config={"max_concurrency": 2}` limits concurrent work in this example.
- Two consecutive `await chain.ainvoke(...)` statements run sequentially: the second starts after the first finishes. Use `abatch` for the concurrent batch shown here.

```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model | StrOutputParser()

async def main():
    reports = [
        {"report_text": "Acme's revenue grew 12%."},
        {"report_text": "Beta's operating profit fell 5%."},
        {"report_text": "Gamma opened two new offices."}
    ]

    results = await chain.abatch(
        reports,
        config={"max_concurrency": 2}
    )

    for result in results:
        print(result)

asyncio.run(main())
```

### Sequential awaits — inside an async function

```python
first = await chain.ainvoke(reports[0])
second = await chain.ainvoke(reports[1])
```

### Async batch — inside an async function

```python
results = await chain.abatch(reports)
```

## 13. stream

### Important notes

- `.stream(...)` yields output progressively, letting you display it before the full answer finishes.
- With `StrOutputParser()` in the chain, each chunk is a string. A chunk is not guaranteed to be a complete word.
- `answer += chunk` accumulates the full answer; `print(chunk, end="", flush=True)` displays each chunk as it arrives.
- The chunks belong to the same model request. Streaming directly from the model produces message chunks rather than the parser's strings.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model | StrOutputParser()

answer = ""

for chunk in chain.stream({
    "report_text": "Acme's revenue grew 12%, while operating profit fell 5%."
}):
    answer += chunk
    print(chunk, end="", flush=True)

print()
```

## 14. astream

### Important notes

- Use `async for chunk in chain.astream(...)` inside an async function.
- Do not put `await` before `chain.astream(...)`; `async for` consumes its asynchronous iterator.
- With the string parser, chunks are strings. Accumulation and printing work as in the synchronous streaming example.
- `asyncio.run(main())` starts the event loop for this script. An async web framework already manages its event loop.

```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-5-nano")

prompt = ChatPromptTemplate([
    ("system", "Summarize the report in one sentence."),
    ("human", "{report_text}")
])

chain = prompt | model | StrOutputParser()

async def main():
    answer = ""

    async for chunk in chain.astream({
        "report_text": "Acme's revenue grew 12%, while profit fell 5%."
    }):
        answer += chunk
        print(chunk, end="", flush=True)

    print()

asyncio.run(main())
```

### Streaming syntax comparison

```python
# Synchronous streaming
for chunk in chain.stream(data):
    ...

# Asynchronous streaming, inside an async function
async for chunk in chain.astream(data):
    ...
```

## 15. Defining and invoking a tool with @tool

### Important notes

- `@tool` turns the function into a LangChain tool. The function name becomes the tool name, the docstring supplies its description, and input annotations define its argument schema.
- `get_revenue.invoke({...})` executes the Python tool directly. This example makes no model call.
- The sample lookup returns `120000000` for Acme in 2025, or `None` when the company/year pair is absent.
- `.name`, `.description`, and `.args` let you inspect the tool's interface.

```python
from langchain.tools import tool

@tool
def get_revenue(company: str, year: int):
    """Look up annual revenue in USD, or return None if unavailable."""
    data = {
        ("Acme", 2024): 100_000_000,
        ("Acme", 2025): 120_000_000
    }
    return data.get((company, year))

result = get_revenue.invoke({
    "company": "Acme",
    "year": 2025
})

print(result)  # 120000000
```

### Inspecting the tool

```python
print(get_revenue.name)
print(get_revenue.description)
print(get_revenue.args)
```

## 16. bind_tools — a tool request and tool execution

### Important notes

- `model.bind_tools([get_revenue])` makes the tool's schema available to the model; it does not execute the function.
- `model_with_tools.invoke(...)` calls the model. A returned item in `response.tool_calls` is a request containing a tool name, arguments, and a call ID.
- `get_revenue.invoke(call["args"])` is the line that actually executes the Python tool.
- The model can return no tool calls, and its text can be empty when it requests a tool. The `[0]` example assumes the illustrated tool request exists; preserve the `AIMessage` to retain its tool-call information.

```python
from langchain.tools import tool
from langchain_openai import ChatOpenAI

@tool
def get_revenue(company: str, year: int):
    """Look up annual revenue in USD, or return None if unavailable."""
    data = {
        ("Acme", 2024): 100_000_000,
        ("Acme", 2025): 120_000_000
    }
    return data.get((company, year))

model = ChatOpenAI(model="gpt-5-nano")

model_with_tools = model.bind_tools([get_revenue])

# Calls the model. It does not execute the Python tool.
response = model_with_tools.invoke(
    "Use get_revenue to find Acme's revenue for 2025."
)

print(response.tool_calls)
```

### Example tool-call request

```text
[
    {
        "name": "get_revenue",
        "args": {"company": "Acme", "year": 2025},
        "id": "call_abc123",
        "type": "tool_call"
    }
]
```

### Executing the requested tool — assuming the request shown above

```python
call = response.tool_calls[0]

# This executes the Python tool.
revenue = get_revenue.invoke(call["args"])

print(revenue)  # 120000000
```

### Direct tool invocation

```python
result = get_revenue.invoke({"company": "Acme", "year": 2025})
```

### Alternative model prompt

```python
response = model_with_tools.invoke(
    "What was Acme's revenue for 2025?"
)
```

## 17. ToolMessage — sending the tool's result back to the model

Your Python code fetched `120000000`. The model has not received that result yet. A `ToolMessage` carries it back, linked to the original request.

Using `get_revenue` and `model_with_tools` from the previous example:

```python
from langchain.messages import HumanMessage, ToolMessage

messages = [
    HumanMessage("Use get_revenue to find Acme's revenue for 2025.")
]

# 1. Ask the model. It returns a tool-call request.
response = model_with_tools.invoke(messages)
messages.append(response)

# 2. Execute the requested tool and record its result.
for call in response.tool_calls:
    result = get_revenue.invoke(call["args"])

    messages.append(
        ToolMessage(
            content=str(result),
            tool_call_id=call["id"]
        )
    )

# 3. Send the conversation, including the result, back to the model.
final_response = model_with_tools.invoke(messages)

print(final_response.text)
```

For this example, assume one tool request followed by a text answer:

```text
Acme's revenue for 2025 was $120 million.
```

### Three lines to understand

- **`messages.append(response)`** preserves the model's original tool request.
- **`content=str(result)`** carries the tool's output: `"120000000"`.
- **`tool_call_id=call["id"]`** identifies which request this result answers. The IDs must match.

### Important notes

- This example has two model calls and one Python tool execution. Creating or appending the `ToolMessage` does not call the model; the second `.invoke(messages)` sends the updated conversation.
- The second model call can also request another tool. This example assumes it answers after receiving the result; a complete execution loop handles repeated requests.

## 18. A tool-execution loop

The previous example made two model calls. Now we repeat the exchange whenever the model requests another tool, sending each result back before continuing.

Reuse `get_revenue` and `model_with_tools`:

```python
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

load_dotenv()


# 1. Define two tools using sample data.
@tool
def get_revenue(company: str, year: int):
    """Look up a company's annual revenue in USD."""
    data = {
        ("Acme", 2025): 120_000_000
    }
    return data.get((company, year), "Revenue unavailable")


@tool
def get_employee_count(company: str, year: int):
    """Look up a company's year-end employee count."""
    data = {
        ("Acme", 2025): 500
    }
    return data.get((company, year), "Employee count unavailable")


# 2. Tell the model which tools are available.
model = ChatOpenAI(model="gpt-5-nano")

model_with_tools = model.bind_tools([
    get_revenue,
    get_employee_count,
])


# 3. Map each tool's NAME to its actual tool OBJECT.
tools_by_name = {
    "get_revenue": get_revenue,
    "get_employee_count": get_employee_count,
}


# 4. Start the conversation.
messages = [
    SystemMessage(
        content="Use the tools to look up requested figures. Do not guess."
    ),
    HumanMessage(
        content=(
            "Use both tools to find Acme's revenue and employee count "
            "for 2025. Then report both figures."
        )
    ),
]


# 5. Repeat model calls and tool execution until we get a final answer.
for _ in range(5):
    response = model_with_tools.invoke(messages)
    messages.append(response)

    # No tool requests: the model has finished.
    if not response.tool_calls:
        print("Final answer:", response.text)
        break

    # Execute EVERY tool requested in this response.
    for call in response.tool_calls:
        print("Requested tool:", call["name"])
        print("Arguments:", call["args"])

        # Choose the correct tool using its name.
        selected_tool = tools_by_name[call["name"]]

        # Run that tool with the requested arguments.
        result = selected_tool.invoke(call["args"])
        print("Tool result:", result)

        # Add the result so the next model call can read it.
        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=call["id"],
            )
        )

else:
    raise RuntimeError("No final answer within 5 model calls.")
```

### Three lines to understand

- **`for _ in range(5)`** allows at most five model calls. It prevents the loop from continuing indefinitely.
- **`if not response.tool_calls:`** checks whether the model has stopped requesting tools. We print its response and `break`.
- **`messages.append(ToolMessage(...))`** records each result so the next model call receives the updated conversation.

### Important notes

- The final **`else` belongs to the outer `for`**. Python runs it only if the loop exhausts all five iterations without hitting `break`.
- **Five model calls does not mean five tool executions:** one model response can request multiple tool calls.

## 19. create_agent — let LangChain manage the tool loop

It handles model calls, executes requested tools, and sends their results back to the model.

```python
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
#Your .env file should contain OPENAI_API_KEY=your_key_here.
load_dotenv()


# 1. Define the two tools.
@tool
def get_revenue(company: str, year: int):
    """Look up a company's annual revenue in USD."""
    print(f"Running get_revenue({company}, {year})")

    data = {
        ("Acme", 2025): 120_000_000
    }
    return data.get((company, year), "Revenue unavailable")


@tool
def get_employee_count(company: str, year: int):
    """Look up a company's year-end employee count."""
    print(f"Running get_employee_count({company}, {year})")

    data = {
        ("Acme", 2025): 500
    }
    return data.get((company, year), "Employee count unavailable")


# 2. Create the model.
model = ChatOpenAI(model="gpt-5-nano")


# 3. Create an agent with BOTH tools.
agent = create_agent(
    model=model,
    tools=[get_revenue, get_employee_count],
    system_prompt=(
        "Use the tools to look up requested figures. "
        "Do not guess. Report the results concisely."
    ),
)


# 4. Run the agent. It manages tool requests and execution.
result = agent.invoke({
    "messages": [
        HumanMessage(
            content=(
                "Use both tools to find Acme's revenue and employee count "
                "for 2025. Then report both figures."
            )
        )
    ]
})


# 5. Read the final assistant message.
final_message = result["messages"][-1]
print("Final answer:", final_message.text)
```

### Example output

```text
Acme's revenue for 2025 was $120 million.
```

### Three lines to understand

- **`create_agent(model=model, tools=[get_revenue], ...)`** configures the agent with its model, tools, and instructions. You do not need a separate `bind_tools()` call.
- **`agent.invoke({"messages": [...]})`** runs the model-and-tool loop. **Here, requested tools actually execute.** One invocation can involve multiple model calls.
- **`result["messages"][-1].text`** reads the last message's text. The agent returns a **state dictionary** containing the conversation's messages.

### Important notes

- The model still decides whether to request a tool; the agent executes it when requested.
