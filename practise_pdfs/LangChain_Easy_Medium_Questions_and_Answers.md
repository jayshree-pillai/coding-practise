# LangChain: Easy–Medium Questions and Answers

Reviewed all **60 questions** and their supplied answer keys. This edition retains **52 easy-to-medium questions**, clarifies ambiguous wording, and places each answer directly below its choices. Original set and question numbers are preserved under each heading. No new question topics have been added.

**Easy** questions test one basic interface or operation. **Medium** questions combine a few concepts or apply a clearly stated rule. Eight questions requiring deeper security, approval, or evaluation design were excluded.

Start with [Part 1: Foundations](#part-1-foundations), then [Part 2: Chains, tools, and retrieval](#part-2-chains-tools-and-retrieval), then [Part 3: Applied decisions](#part-3-applied-decisions).

## Running the examples

Each answer's main Python example includes its own imports and setup. Run it independently as a Python script. Local lookups, scripted models, and teaching embeddings are identified where used; they make the data flow visible without requiring a provider account.

Install the packages into the same Python environment that runs your examples:

```bash
python -m pip install langchain langchain-core langchain-community langchain-openai langchain-text-splitters pydantic numpy
```

All **52 local answer examples were executed and checked against their displayed output**. They were checked with Python 3.12, LangChain 1.4.7, langchain-core 1.7.3, langchain-community 0.4.2, langchain-openai 1.7.3, langchain-text-splitters 1.1.3, Pydantic 2.14.2, and NumPy 2.5.4.

Question 28 also includes an optional **live API** example for `create_agent`. That extra block requires the stated environment variables and was syntax-checked, not run against a provider. Every question can be studied using its local example.

## Part 1: Foundations

### 1. A missing prompt variable (Easy)

*Source: LangChain-E-M-Set3, Q01.*

A chat prompt contains `"Explain {concept} to a {audience}."`. A chain runs that prompt first, then a chat model. You invoke it with only `{"concept": "embeddings"}`. There is no default audience or error handler. What happens?

- **A.** LangChain asks the model to infer the missing audience.
- **B.** The model receives the literal placeholder `{audience}`.
- **C.** LangChain substitutes an empty string for the audience.
- **D.** Prompt formatting fails before the model is called.

**Answer: D — the required `audience` variable is missing.**

The prompt must produce its messages before the next step can run. LangChain does not automatically infer or invent a missing variable, so A–C do not describe this call.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    "Explain {concept} to a {audience}."
)
# Scripted local stand-in; no provider is contacted.
model = FakeListChatModel(responses=["An embedding is a numeric representation."])
chain = prompt | model

try:
    chain.invoke({"concept": "embeddings"})
except KeyError:
    print("Prompt formatting failed: audience is required.")

# Supplying both variables allows the complete chain to run.
reply = chain.invoke({"concept": "embeddings", "audience": "new engineer"})
print(reply.text)
```

Expected output:

```text
Prompt formatting failed: audience is required.
An embedding is a numeric representation.
```

The successful reply is configured in the fake model; it is not evidence of model reasoning.

### 2. Fill a stable prompt value with `partial` (Easy)

*Source: LangChain-E-M-Set3, Q02.*

A prompt contains `"Explain {concept} to a {audience}."`. You create `ready = base.partial(audience="new engineer")`. Which invocation supplies the remaining required value?

- **A.** `ready.invoke({"concept": "vector search"})`
- **B.** `ready.invoke({"audience": "vector search"})`
- **C.** `ready.invoke({"input": "vector search"})`
- **D.** `ready.invoke({})`

**Answer: A — `audience` is already filled; `concept` still needs a value.**

Think of `partial` as filling in part of a template ahead of time. B supplies the wrong field, C uses a field the prompt does not request, and D supplies no concept.

```python
from langchain_core.prompts import ChatPromptTemplate

base = ChatPromptTemplate.from_template(
    "Explain {concept} to a {audience}."
)
ready = base.partial(audience="new engineer")

print(ready.input_variables)
prompt_value = ready.invoke({"concept": "vector search"})
print(prompt_value.to_messages()[0].content)
```

Expected output:

```text
['concept']
Explain vector search to a new engineer.
```

Here `ready.invoke(...)` formats a prompt. It does not call a model.

### 3. The result of a chat model call (Easy)

*Source: LangChain-E-M-Set3, Q03.*

A standard LangChain chat model produces a plain text reply through `model.invoke(...)`. There is no output parser. What is the returned object?

- **A.** A `Document`, with the reply in `page_content`.
- **B.** A plain Python string, with all metadata discarded.
- **C.** An `AIMessage`, containing the reply and potentially response metadata.
- **D.** A list of `AIMessageChunk` objects.

**Answer: C — an ordinary chat-model `invoke` call returns an `AIMessage`.**

For this text-only reply, `.content` contains the text and `.text` extracts the text. A confuses retrieved documents with chat messages. B would require extracting or parsing the text. D describes neither the single result nor the normal streaming interface.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

# Scripted model used only to demonstrate the return type.
model = FakeListChatModel(responses=["Find documents with similar meaning."])
response = model.invoke("Give one use of embeddings.")

print(type(response).__name__)
print(response.content)
print(response.text)
```

Expected output:

```text
AIMessage
Find documents with similar meaning.
Find documents with similar meaning.
```

### 4. Load source text into `Document` objects (Easy)

*Source: LangChain-E-M-Set3, Q04.*

You have text files and content in a supported remote service. Which LangChain component primarily reads those sources and represents their content as `Document` objects?

- **A.** An embedding model.
- **B.** A suitable document loader for each source.
- **C.** A chat prompt template.
- **D.** An output parser.

**Answer: B — document loaders turn source content into `Document` objects.**

A loader reads a source. A `Document` holds its text in `page_content` and associated information in `metadata`. An embedding model converts text into vectors; a prompt formats model input; an output parser processes model output.

This example creates a temporary text file so it can run without your own files. It requires `langchain-community`.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_community.document_loaders import TextLoader

with TemporaryDirectory() as folder:
    path = Path(folder) / "guide.txt"
    path.write_text("Reset your password from Settings.", encoding="utf-8")

    loader = TextLoader(str(path), encoding="utf-8")
    documents = loader.load()

    print(type(documents).__name__)
    print(type(documents[0]).__name__)
    print(documents[0].page_content)
    print(Path(documents[0].metadata["source"]).name)
```

Expected output:

```text
list
Document
Reset your password from Settings.
guide.txt
```

### 5. Put retrieved text into a user message (Easy)

*Source: LangChain-E-M-Set3, Q05.*

You have `doc = Document(page_content="The service opens at 09:00.")`. You want its text to become one user message. Which expression does that?

- **A.** `Document(page_content=doc.page_content, metadata={"role": "user"})`
- **B.** `HumanMessage(content=doc.page_content)`
- **C.** `AIMessage(content=doc.page_content)`
- **D.** `HumanMessage(content=doc)`

**Answer: B — extract the document's text and place it in a `HumanMessage`.**

A remains a `Document`; changing metadata does not change its type. C gives the text the assistant role. D passes the whole document object where this message needs text or supported content blocks.

```python
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

doc = Document(page_content="The service opens at 09:00.")
message = HumanMessage(content=doc.page_content)

print(type(doc).__name__)
print(type(message).__name__)
print(message.content)
```

Expected output:

```text
Document
HumanMessage
The service opens at 09:00.
```

### 6. Understand embedding output shapes (Easy)

*Source: LangChain-E-M-Set3, Q06.*

An embedding model produces vectors of length `d`. What do these successful calls return: `embed_query("reset password")` and `embed_documents(["Guide A", "Guide B"])`?

- **A.** One relevance score, then a ranked list of the two strings.
- **B.** A list containing one vector, then one averaged vector.
- **C.** One vector of `d` numbers, then a list containing two such vectors.
- **D.** Two lists of `Document` objects.

**Answer: C — one input query gives one vector; two documents give two vectors.**

The nesting is the key: query → `list[float]`; documents → `list[list[float]]`. Embedding does not itself rank documents, average the entire batch, or create `Document` objects.

The fake embedding model below is only for testing shapes. Its vectors do not provide meaningful semantic similarity.

```python
from langchain_core.embeddings import DeterministicFakeEmbedding

embeddings = DeterministicFakeEmbedding(size=4)

query_vector = embeddings.embed_query("reset password")
document_vectors = embeddings.embed_documents(["Guide A", "Guide B"])

print("Query vector length:", len(query_vector))
print("Number of document vectors:", len(document_vectors))
print("Document vector lengths:", [len(vector) for vector in document_vectors])
```

Expected output:

```text
Query vector length: 4
Number of document vectors: 2
Document vector lengths: [4, 4]
```

### 7. Retrieval gives documents (Easy)

*Source: LangChain-E-M-Set3, Q07.*

A normal LangChain retriever successfully runs `retriever.invoke("How do I rotate a service key?")`. What should you expect as its result?

- **A.** A list of relevant `Document` objects; composing an answer is a separate step.
- **B.** An `AIMessage`; read its `.content` for the final answer.
- **C.** One JSON-encoded answer string.
- **D.** Only vectors, with the original text unavailable.

**Answer: A — retrieval returns source documents.**

You can inspect each document's `page_content`. A model can then use that text to compose an answer, if your application needs one. Retrieval alone does not guarantee an answer message, JSON, or vectors-only output.

This small test retriever always returns one canned document. It demonstrates the interface, not search quality.

```python
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

class DemoRetriever(BaseRetriever):
    def _get_relevant_documents(self, query, *, run_manager):
        return [Document(page_content="Create a new key, then revoke the old key.")]

retriever = DemoRetriever()
result = retriever.invoke("How do I rotate a service key?")

print(type(result).__name__)
print(type(result[0]).__name__)
print(result[0].page_content)
```

Expected output:

```text
list
Document
Create a new key, then revoke the old key.
```

### 8. Why adjacent chunks overlap (Easy)

*Source: LangChain-E-M-Set3, Q08.*

A sentence near a chunk boundary depends on text immediately before that boundary. Why might you configure a modest `chunk_overlap`?

- **A.** To guarantee search never returns similar chunks.
- **B.** To guarantee every chunk answers every future question.
- **C.** To change the embedding vector dimension.
- **D.** To retain some neighboring context, while accepting repeated text.

**Answer: D — overlap repeats some text across adjacent chunks.**

This can help preserve context around a split. It does not guarantee retrieval quality or complete answers, and it does not change embedding dimensions.

The short character example makes the repeated part easy to see. `separators=[""]` forces character-level splitting here.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=6,
    chunk_overlap=2,
    length_function=len,
    separators=[""],
)

chunks = splitter.split_text("ABCDEFGHIJ")
print(chunks)
print("Shared text:", chunks[0][-2:])
print("Second chunk begins with:", chunks[1][:2])
```

Expected output:

```text
['ABCDEF', 'EFGHIJ']
Shared text: EF
Second chunk begins with: EF
```

### 9. Install the provider integration (Easy)

*Source: LangChain-E-M-Set3, Q09.*

Your active Python environment has `langchain-core`, but `from langchain_openai import ChatOpenAI` fails with `ModuleNotFoundError: No module named 'langchain_openai'`. What directly fixes this missing-module problem?

- **A.** Install `langchain-openai` into that same Python environment.
- **B.** Set `OPENAI_API_KEY`; Python will install the integration automatically.
- **C.** Change the model name.
- **D.** Create a prompt template to register provider packages.

**Answer: A — the integration package must be installed.**

The distribution name used by pip has a hyphen; the Python import uses an underscore. Credentials, model names, and prompts do not install Python modules.

Install using the interpreter that runs your application:

```bash
python -m pip install langchain-openai
```

Then verify the import:

```python
from langchain_openai import ChatOpenAI

print(ChatOpenAI.__name__)
```

Expected output:

```text
ChatOpenAI
```

This example only imports the class. It does not instantiate a model, require a key, or make an API call.

### 10. Few-shot examples change the prompt (Easy)

*Source: LangChain-E-M-Set3, Q10.*

You add three labeled examples to a `FewShotPromptTemplate` for classification. What does formatting this prompt change?

- **A.** The provider's global classifier for every customer.
- **B.** The model weights through immediate fine-tuning.
- **C.** The context supplied for inference; it does not update model weights.
- **D.** The model into a deterministic lookup table.

**Answer: C — the examples become part of the prompt text.**

The model can use examples as guidance when you later invoke it. Creating or formatting this prompt does not train the model, change other customers' calls, or guarantee correct classification.

```python
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

examples = [
    {"text": "Great service", "label": "positive"},
    {"text": "Terrible service", "label": "negative"},
    {"text": "The package arrived", "label": "neutral"},
]
example_prompt = PromptTemplate.from_template("Text: {text}\nLabel: {label}")

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Text: {text}\nLabel:",
    input_variables=["text"],
    example_separator="\n\n",
)

print(prompt.format(text="Loved it"))
```

Expected output:

```text
Text: Great service
Label: positive

Text: Terrible service
Label: negative

Text: The package arrived
Label: neutral

Text: Loved it
Label:
```

No model has been called yet; the final label is intentionally blank.

### 11. Keep JSON braces literal in a prompt (Medium)

*Source: LangChain-E-M-Set3, Q11.*

A `PromptTemplate` uses its default f-string template format. You want this rendered text when `query="check service"`: `Example: {"status": "ok"}. Query: check service`. Which template is correct?

- **A.** `Example: [{"status": "ok"}]. Query: {query}`
- **B.** `Example: {"status": "ok"}. Query: {query}`
- **C.** `Example: {{"status": "ok"}}. Query: {{query}}`
- **D.** `Example: {{"status": "ok"}}. Query: {query}`

**Answer: D — double the literal JSON braces, but keep the variable braces single.**

`{{` and `}}` render as literal braces. `{query}` is a placeholder. A and B leave the JSON braces unescaped. C also escapes `query`, so it would print `{query}` instead of substituting its value.

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    'Example: {{"status": "ok"}}. Query: {query}'
)

print(prompt.input_variables)
print(prompt.format(query="check service"))
```

Expected output:

```text
['query']
Example: {"status": "ok"}. Query: check service
```

### 12. Apply one runnable to every list item (Medium)

*Source: LangChain-E-M-Set3, Q12.*

A runnable strips whitespace and uppercases one string. What does its `.map().invoke([" red", "blue "])` return?

- **A.** `"REDBLUE"`
- **B.** `["RED", "BLUE"]`
- **C.** `[["RED"], ["BLUE"]]`
- **D.** An error because the function receives the entire list.

**Answer: B — `map()` applies the runnable to each item and collects the outputs.**

The function receives `" red"` in one call and `"blue "` in another. Each returns one string. There is no concatenation, extra list around each string, or whole-list call to `strip()`.

```python
from langchain_core.runnables import RunnableLambda

def normalize(text):
    return text.strip().upper()

one_text = RunnableLambda(normalize)
many_texts = one_text.map()

print(one_text.invoke(" red"))
print(many_texts.invoke([" red", "blue "]))
```

Expected output:

```text
RED
['RED', 'BLUE']
```

### 13. Branches use the first matching condition (Medium)

*Source: LangChain-E-M-Set3, Q13.*

A `RunnableBranch` checks these conditions in order: first `n > 0` returns `"positive"`; then `n > 10` returns `"large"`; its default returns `"other"`. What does invoking it with `12` return?

- **A.** `"large"`
- **B.** `"positive"`
- **C.** `["positive", "large"]`
- **D.** `"other"`

**Answer: B — the first condition is already true.**

The branch does not choose the most specific condition or collect every match. Since `12 > 0`, it uses the first result. To prioritize `"large"`, you would put the `n > 10` condition first.

```python
from langchain_core.runnables import RunnableBranch

router = RunnableBranch(
    (lambda n: n > 0, lambda n: "positive"),
    (lambda n: n > 10, lambda n: "large"),
    lambda n: "other",
)

print(router.invoke(12))
print(router.invoke(-2))
```

Expected output:

```text
positive
other
```

### 14. Keep successful batch results alongside errors (Medium)

*Source: LangChain-E-M-Set3, Q14.*

A runnable computes `12 / n` independently for each input. You run `.batch([3, 0, 4], return_exceptions=True)`. What does the returned list contain?

- **A.** `[4.0, 0.0, 3.0]`, replacing the failure with zero.
- **B.** Nothing; the entire call raises instead of returning results.
- **C.** Only `[4.0, 3.0]`, dropping the failed item.
- **D.** `4.0`, a `ZeroDivisionError` object, and `3.0`, in input order.

**Answer: D — the failed item's exception is returned in its position.**

`return_exceptions=True` makes errors inspectable alongside successful outputs. It does not invent a replacement value or remove the failed input's position.

```python
from langchain_core.runnables import RunnableLambda

divide = RunnableLambda(lambda n: 12 / n)
results = divide.batch([3, 0, 4], return_exceptions=True)

for result in results:
    if isinstance(result, Exception):
        print(type(result).__name__)
    else:
        print(result)
```

Expected output:

```text
4.0
ZeroDivisionError
3.0
```

### 15. Request three results from a vector-store retriever (Medium)

*Source: LangChain-E-M-Set3, Q15.*

A vector store supports standard similarity search and contains enough documents. There are no filters or score thresholds. Which construction requests three matching documents per query?

- **A.** `store.as_retriever(search_kwargs={"k": 3})`
- **B.** `store.as_retriever(search_type="top_3")`
- **C.** `store.as_retriever(search_kwargs={"chunk_size": 3})`
- **D.** `store.as_retriever(tags=["k=3"])`

**Answer: A — `k` is the requested result count, passed through `search_kwargs`.**

`"top_3"` is not the standard search type. `chunk_size` concerns splitting text, and tags label execution rather than configure the result count.

The fake embeddings below make the demo run offline. They demonstrate the result count, not meaningful relevance ranking.

```python
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore

embeddings = DeterministicFakeEmbedding(size=8)
store = InMemoryVectorStore(embedding=embeddings)
store.add_documents([
    Document(page_content="Reset your password in Settings."),
    Document(page_content="Create a service key in the developer console."),
    Document(page_content="Download invoices from Billing."),
    Document(page_content="Invite teammates from the Team page."),
])

retriever = store.as_retriever(search_kwargs={"k": 3})
matches = retriever.invoke("How do I reset my password?")

print("Results:", len(matches))
print("All are documents:", all(isinstance(item, Document) for item in matches))
```

Expected output:

```text
Results: 3
All are documents: True
```

### 16. Combine streamed text chunks (Easy)

*Source: LangChain-E-M-Set3, Q16.*

Two plain text `AIMessageChunk` objects contain `"Hello "` and `"there"`. Which expression produces one combined `AIMessageChunk` containing `"Hello there"`?

- **A.** `[first, second]`
- **B.** `str(first) + str(second)`
- **C.** `first + second`
- **D.** `second`

**Answer: C — adding compatible message chunks combines them.**

A creates a list of two chunks. B concatenates string representations and returns a Python string. D drops the first chunk. C preserves a message-chunk object with the combined content.

```python
from langchain_core.messages import AIMessageChunk

first = AIMessageChunk(content="Hello ")
second = AIMessageChunk(content="there")
combined = first + second

print(type(combined).__name__)
print(combined.content)
```

Expected output:

```text
AIMessageChunk
Hello there
```

### 17. Attach execution metadata separately from prompt input (Medium)

*Source: LangChain-E-M-Set3, Q17.*

You want a chain run to carry structured metadata `experiment="trial-7"` for tracing. It should not be added to the model's prompt. The chain has no custom code that copies execution configuration into prompt text. Which call expresses this?

- **A.** `chain.invoke({"question": "What is recall?", "experiment": "trial-7"})`
- **B.** `chain.invoke({"question": "[experiment=trial-7] What is recall?"})`
- **C.** `chain.invoke({"question": "What is recall?"}, config={"metadata": {"experiment": "trial-7"}})`
- **D.** `chain.invoke({"question": "What is recall?"}, config={"run_name": "trial-7"})`

**Answer: C — use `config["metadata"]` for structured run metadata.**

A supplies an ordinary input field, which is not automatically promoted to tracing metadata. B changes the prompt text. D sets a run name rather than the requested metadata field. Configuring a tracing destination is a separate concern.

This local runnable prints its input and configuration separately; it does not upload a trace.

```python
from langchain_core.runnables import RunnableLambda

def inspect_call(inputs, config):
    print("Input:", inputs)
    print("Metadata:", config["metadata"])
    return inputs["question"]

chain = RunnableLambda(inspect_call)
result = chain.invoke(
    {"question": "What is recall?"},
    config={"metadata": {"experiment": "trial-7"}},
)
print("Returned question:", result)
```

Expected output:

```text
Input: {'question': 'What is recall?'}
Metadata: {'experiment': 'trial-7'}
Returned question: What is recall?
```

### 18. What a fake-model test actually proves (Medium)

*Source: LangChain-E-M-Set3, Q18.*

A test uses `FakeListChatModel(responses=["6"])` after a prompt asking it to compute `3 + 3`. The test passes because the reply is `"6"`. What is the strongest supported conclusion?

- **A.** The real provider model is reliable at arithmetic.
- **B.** This prompt-to-model pipeline can return the configured fake response; real arithmetic quality remains untested.
- **C.** The fake calculated the sum and can generalize to unseen sums.
- **D.** The prompt wording caused the answer to be `"6"`.

**Answer: B — this is a test of the pipeline using a scripted response.**

The fake returns the response you supplied. It does not solve arithmetic. A real model was never called, and the test does not establish why a real model would answer a certain way.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate

fake = FakeListChatModel(responses=["6"])
prompt = ChatPromptTemplate.from_template("Compute {task}.")
chain = prompt | fake

print(chain.invoke({"task": "3 + 3"}).text)
print(chain.invoke({"task": "100 + 200"}).text)
```

Expected output:

```text
6
6
```

The second answer makes the distinction visible: the same configured response is returned even for a different sum.

### 19. Character limits are not token limits (Medium)

*Source: LangChain-E-M-Set3, Q19.*

A `RecursiveCharacterTextSplitter` uses `chunk_size=500`, `chunk_overlap=40`, and `length_function=len`. What unit does that length function measure for Python strings?

- **A.** Tokens for whichever downstream model is called later.
- **B.** Tokens, because every LangChain `chunk_size` is measured in tokens.
- **C.** Whitespace-separated words.
- **D.** String characters; token budgeting needs a suitable tokenizer-based measure.

**Answer: D — Python's `len(text)` measures string length, not model tokens.**

The splitter does not discover a later model and automatically change units. Words, characters, and tokens are different counts. Here the overlap is measured with the same character-based length function.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=40,
    length_function=len,
    separators=[""],  # Makes the toy split predictable.
)

text = "A" * 520
chunks = splitter.split_text(text)

print("Original character count:", len(text))
print("Chunk character counts:", [len(chunk) for chunk in chunks])
```

Expected output:

```text
Original character count: 520
Chunk character counts: [500, 60]
```

The second chunk has 40 repeated characters plus the remaining 20. This output says nothing about the model's token count.

### 20. Process lazily loaded documents one at a time (Medium)

*Source: LangChain-E-M-Set3, Q20.*

A loader's `lazy_load()` genuinely yields documents incrementally. `process(doc)` finishes each document without retaining it. Which approach avoids building a list of every loaded document before processing starts?

- **A.** Iterate directly: `for doc in loader.lazy_load(): process(doc)`.
- **B.** First run `docs = list(loader.lazy_load())`, then process `docs`.
- **C.** First run `docs = loader.load()`, then process `docs`.
- **D.** First run `docs = [doc for doc in loader.lazy_load()]`, then process `docs`.

**Answer: A — consume the iterator directly.**

B and D turn the iterator into a complete list. The standard `load()` interface in C also returns a list. Direct iteration allows loading and processing to alternate, under the assumptions in the question.

```python
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

class DemoLoader(BaseLoader):
    def lazy_load(self):
        for number in range(1, 4):
            print(f"Loading {number}")
            yield Document(page_content=f"Document {number}")

def process(doc):
    print(f"Processing {doc.page_content}")

loader = DemoLoader()
for doc in loader.lazy_load():
    process(doc)
```

Expected output:

```text
Loading 1
Processing Document 1
Loading 2
Processing Document 2
Loading 3
Processing Document 3
```

## Part 2: Chains, tools, and retrieval

### 21. Extracting one field from a dictionary (Medium)

*Source: LangChain-M-Set1, Q01.*

Your chain receives `{"question": "What changed?"}`. Before formatting the prompt, you want this dictionary:

```text
{
    "context": "Acme revenue grew 12% in 2025.",
    "question": "What changed?"
}
```

The `context` branch already works. The `question` branch currently uses `RunnablePassthrough()`, so its value becomes the **whole input dictionary**: `{"question": "What changed?"}`. Which replacement extracts just the question string?

- **A.** Replace the document formatter with `StrOutputParser()`.
- **B.** Replace the entire preparation step with `RunnablePassthrough()`.
- **C.** Replace the `question` branch with `itemgetter("question")`.
- **D.** Keep the branches unchanged and pass a bare string to the chain.

**Answer: C — `itemgetter("question")` selects that field's value.**

Both branches receive the same original input. `RunnablePassthrough()` returns that entire input; `itemgetter("question")` returns `input["question"]`.

This is a problem with the shape of the data. A normal string template might stringify the nested dictionary instead of raising an error. Either way, it does not produce the clean question text you intended.

**Complete example — local lookup, no model or API key:**

```python
from operator import itemgetter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel

reports = {
    "What changed?": [
        Document(page_content="Acme revenue grew 12% in 2025.")
    ]
}

def retrieve(question):
    return reports.get(question, [])  # string -> list of Documents

def format_docs(documents):
    return "\n".join(doc.page_content for doc in documents)

retriever = RunnableLambda(retrieve)
prepare = RunnableParallel(
    context=itemgetter("question") | retriever | format_docs,
    question=itemgetter("question"),
)

input_data = {"question": "What changed?"}
prepared = prepare.invoke(input_data)
print(prepared)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use this evidence: {context}"),
    ("human", "{question}"),
])
prompt_value = (prepare | prompt).invoke(input_data)
print(prompt_value.to_messages()[-1].content)
```

**Expected output:**

```text
{'context': 'Acme revenue grew 12% in 2025.', 'question': 'What changed?'}
What changed?
```

**Read these three lines:** `itemgetter` extracts the string; `retriever` returns documents; `format_docs` turns those documents into context text. The separate `question` branch keeps the original question string.

**Other choices:** A changes the wrong branch. B loses the retrieved context. D breaks the branches that access the `"question"` dictionary key.

### 22. Making one assigned field depend on another (Medium)

*Source: LangChain-M-Set1, Q02.*

The only input is `{"amount": 100}`. You want to add `tax=10.0`, then calculate `total=110.0` using that tax. Why does the following need a change?

```python
step = RunnablePassthrough.assign(
    tax=lambda x: x["amount"] * 0.10,
    total=lambda x: x["amount"] + x["tax"],
)
```

- **A.** Put `tax` in one `.assign()` and `total` in a second `.assign()` after it.
- **B.** Keeping `tax` before `total` in the same call guarantees the dependency.
- **C.** Increase `max_concurrency` so `total` can see `tax`.
- **D.** Replace `.assign()` with two parallel branches reading the original input.

**Answer: A — the second assignment needs the first assignment's output.**

Every function inside one `.assign()` receives that stage's input. Here that input contains `amount`, but not `tax`. Keyword order does not make sibling calculations sequential.

```python
from langchain_core.runnables import RunnablePassthrough

add_tax = RunnablePassthrough.assign(
    tax=lambda data: data["amount"] * 0.10
)
add_total = RunnablePassthrough.assign(
    total=lambda data: data["amount"] + data["tax"]
)

input_data = {"amount": 100}
print(input_data)
print(add_tax.invoke(input_data))
print((add_tax | add_total).invoke(input_data))
```

**Expected output:**

```text
{'amount': 100}
{'amount': 100, 'tax': 10.0}
{'amount': 100, 'tax': 10.0, 'total': 110.0}
```

**Remember:** `.assign()` keeps existing fields and adds computed ones. It can also replace an existing field with the same name. Ordinary Python is sufficient for a one-off dictionary edit; `.assign()` is useful when this edit must be a stage in a runnable chain.

**Other choices:** B changes presentation order, not dependencies. C changes scheduling, not available data. D still gives both branches the input without `tax`.

### 23. Reading sequential and parallel data flow (Easy)

*Source: LangChain-M-Set1, Q03.*

What does this complete program print?

```python
from langchain_core.runnables import RunnableLambda

chain = RunnableLambda(lambda number: number * 2) | {
    "a": RunnableLambda(lambda number: number + 1),
    "b": RunnableLambda(lambda number: number * 2),
}
print(chain.invoke(3))
```

- **A.** `14`
- **B.** `{"a": 7, "b": 14}`
- **C.** `{"a": 4, "b": 6}`
- **D.** `{"a": 7, "b": 12}`

**Answer: D — the first stage produces `6`, and both branches receive `6`.**

The mapping after `|` becomes a `RunnableParallel`. It collects named outputs; it does not run `a` and then feed `a` into `b`.

**The same calculation, with the intermediate value visible:**

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel

double = RunnableLambda(lambda number: number * 2)
branches = RunnableParallel(
    a=lambda number: number + 1,
    b=lambda number: number * 2,
)

intermediate = double.invoke(3)
print(intermediate)
print(branches.invoke(intermediate))
```

**Expected output:**

```text
6
{'a': 7, 'b': 12}
```

**Other choices:** A incorrectly treats the mapping as sequential operations. B incorrectly sends `7` into branch `b`. C incorrectly sends the original `3` into both branches.

### 24. Preserving streaming through a text transform (Medium)

*Source: LangChain-M-Set1, Q04.*

A chain already streams text chunks. You append `RunnableLambda(lambda text: text.upper())`, a normal function that accepts one complete string. Now the client receives one combined result. Uppercasing these ASCII chunks is safe to do separately. What change preserves incremental output?

- **A.** Replace the model provider immediately.
- **B.** Use a generator transform that uppercases and yields each incoming chunk.
- **C.** Increase batch concurrency.
- **D.** Replace `.stream()` with `.invoke()`.

**Answer: B — the final stage must also process a stream incrementally.**

This ordinary `RunnableLambda` waits for the preceding chunks to be combined before calling its function. `RunnableGenerator` can consume and emit chunks as they arrive.

**Complete offline example — the source is a scripted chunk generator:**

```python
from langchain_core.runnables import RunnableGenerator, RunnableLambda

def emit_chunks(inputs):
    for _ in inputs:
        yield "revenue "
        yield "grew "
        yield "12%"

def uppercase_chunks(chunks):
    for chunk in chunks:
        yield chunk.upper()

source = RunnableGenerator(emit_chunks)
buffered = source | RunnableLambda(lambda text: text.upper())
streaming = source | RunnableGenerator(uppercase_chunks)

print(list(buffered.stream("start")))
print(list(streaming.stream("start")))
```

**Expected output:**

```text
['REVENUE GREW 12%']
['REVENUE ', 'GREW ', '12%']
```

**Remember:** Not every transform is safe per chunk. For example, replacing a phrase that may span chunk boundaries needs additional buffering. This example deliberately uses a transform valid for the supplied chunks.

**Other choices:** A ignores the stage that introduced buffering. C affects independent requests. D collects a completed answer rather than exposing incremental chunks.

### 25. Matching completed batch results to inputs (Medium)

*Source: LangChain-M-Set1, Q05.*

You submit documents at indices `0`, `1`, and `2` to `.batch_as_completed()`. They finish in the order `2`, `0`, `1`. Each yielded item is `(input_index, result)`. How should you associate each label with its document?

- **A.** Use the returned `input_index` to find the original document.
- **B.** Zip the original documents with results in arrival order.
- **C.** Sort the labels alphabetically before matching them.
- **D.** Treat the first arrival as document `0`.

**Answer: A — completion order and input identity are different things.**

Store each result at its returned input index. The following example uses a local labeling function, so it needs no model. Completion order can vary; the final association stays correct.

```python
from langchain_core.runnables import RunnableLambda

documents = [
    {"id": "doc-0", "text": "Revenue increased."},
    {"id": "doc-1", "text": "Hiring increased."},
    {"id": "doc-2", "text": "Revenue decreased."},
]

def label_document(document):
    if "Revenue" in document["text"]:
        return "finance"
    return "people"

labeler = RunnableLambda(label_document)
results = [None] * len(documents)

for input_index, label in labeler.batch_as_completed(documents):
    results[input_index] = {
        "id": documents[input_index]["id"],
        "label": label,
    }

for result in results:
    print(result)
```

**Expected output:**

```text
{'id': 'doc-0', 'label': 'finance'}
{'id': 'doc-1', 'label': 'people'}
{'id': 'doc-2', 'label': 'finance'}
```

**Other choices:** B and D assume completion order equals input order. C cannot recover document identity from label text.

### 26. Executing a tool request (Medium)

*Source: LangChain-M-Set1, Q06.*

You register a local Python tool using `model.bind_tools([lookup_invoice])`. Calling the bound model returns an `AIMessage` with a tool call for invoice `INV-7`, but your Python function has not run. What must happen before the model can use the invoice data?

- **A.** Lower the model's temperature.
- **B.** Bind the same tool a second time.
- **C.** Execute the requested tool, return its result in a `ToolMessage`, and call the model again; an agent loop can manage these steps.
- **D.** Add `StrOutputParser()` to execute the function named in the response.

**Answer: C — a tool request is data describing a call; your application or agent executes it.**

For a local Python tool, `.bind_tools()` advertises its schema. It does not execute the function when the model proposes the call. Provider-hosted built-in tools are a separate mechanism.

**Complete offline example — a scripted stand-in requests a tool, then reads its actual result:**

```python
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up an invoice's payment status by its ID."""
    invoices = {"INV-7": "paid"}
    return invoices.get(invoice_id, "not found")

# This is a deterministic teaching stand-in, not a real chat model.
def scripted_model(messages):
    if isinstance(messages[-1], ToolMessage):
        return AIMessage(content=f"Invoice INV-7 is {messages[-1].content}.")
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "lookup_invoice",
            "args": {"invoice_id": "INV-7"},
            "id": "call-1",
            "type": "tool_call",
        }],
    )

model_with_tools = RunnableLambda(scripted_model)
allowed_tools = {lookup_invoice.name: lookup_invoice}
messages = [HumanMessage(content="Is invoice INV-7 paid?")]

for _ in range(3):
    response = model_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        print(response.content)
        break

    for call in response.tool_calls:
        selected_tool = allowed_tools[call["name"]]
        # Passing the complete tool-call dictionary returns a ToolMessage.
        tool_result = selected_tool.invoke(call)
        messages.append(tool_result)
        print(tool_result.type, tool_result.tool_call_id, tool_result.content)
else:
    raise RuntimeError("Tool-loop limit reached")
```

**Expected output:**

```text
tool call-1 paid
Invoice INV-7 is paid.
```

**Read these three operations:** append the model's tool request; execute the selected tool and append its result; invoke the model again with both messages. `tool_call_id` connects the result to the request.

**Other choices:** A changes generation settings. B repeats registration. D returns text; it is not a tool dispatcher.

### 27. Separating schema validation from factual accuracy (Medium)

*Source: LangChain-M-Set1, Q07.*

A source says `Revenue: 125. Figures are in thousands of EUR.` Your application requires revenue in **individual currency units**. An extracted Pydantic object contains `revenue=125.0` and `currency="USD"`. Its types validate. What additional check catches the mistake?

- **A.** Parse the same JSON again without comparing it with the source.
- **B.** Change every field to a string.
- **C.** Accept the object because Pydantic validated it.
- **D.** Compare its amount, scale, and currency with the supporting source.

**Answer: D — the correct normalized amount is `125000.0 EUR`.**

A schema containing only `float` and `str` permits both the correct and incorrect values. It does not read the source and establish whether those values are true.

```python
from pydantic import BaseModel

class Revenue(BaseModel):
    revenue: float
    currency: str

source_text = "Revenue: 125. Figures are in thousands of EUR."
# Facts read from this example's source; not generated by the extractor.
source_facts = {"printed_amount": 125.0, "scale": 1000, "currency": "EUR"}

extracted = Revenue(revenue=125.0, currency="USD")
expected_amount = source_facts["printed_amount"] * source_facts["scale"]

errors = []
if extracted.revenue != expected_amount:
    errors.append("Incorrect amount or scale")
if extracted.currency != source_facts["currency"]:
    errors.append("Incorrect currency")

print(errors)
corrected = Revenue(revenue=expected_amount, currency=source_facts["currency"])
print(corrected.model_dump())
```

**Expected output:**

```text
['Incorrect amount or scale', 'Incorrect currency']
{'revenue': 125000.0, 'currency': 'EUR'}
```

The source facts are explicit so you can inspect the comparison. A real extractor must preserve supporting evidence and apply suitable checks; merely adding an `evidence` string field would not prove correctness either.

**Other choices:** A repeats structural work. B weakens the schema. C confuses valid types with accurate facts.

### 28. Choosing tool-based structured output (Medium)

*Source: LangChain-M-Set1, Q08.*

Your approved chat model supports tool calling but does **not** support provider-native structured responses. You are using `create_agent` and want a validated `Revenue` Pydantic object. Which configuration fits these capabilities?

- **A.** Force `ProviderStrategy(Revenue)`.
- **B.** Use `ToolStrategy(Revenue)` with validation-error handling.
- **C.** Set `response_format=None` and assume the last message is a `Revenue` object.
- **D.** Describe the desired fields in a tool docstring and skip validation.

**Answer: B — `ToolStrategy` obtains structured data through tool calling.**

You pass the strategy as `create_agent(..., response_format=...)`. On success, read the Pydantic object from `result["structured_response"]`. `handle_errors=True` lets the agent send schema-validation feedback back to the model; it does not guarantee factual accuracy or eventual success.

**Offline part — inspect the strategy and validate example data:**

```python
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field, ValidationError

class Revenue(BaseModel):
    amount: float = Field(ge=0)
    currency: str

strategy = ToolStrategy(Revenue, handle_errors=True)
print(type(strategy).__name__)

valid = Revenue.model_validate({"amount": 125000, "currency": "EUR"})
print(valid.model_dump())

try:
    Revenue.model_validate({"amount": -10, "currency": "EUR"})
except ValidationError:
    print("Negative amount rejected")
```

**Expected output:**

```text
ToolStrategy
{'amount': 125000.0, 'currency': 'EUR'}
Negative amount rejected
```

**Complete live-agent version:** This block makes an API call. Install `langchain-openai` and set `OPENAI_API_KEY` and `TOOL_CALLING_MODEL` in your process environment. The latter must name an OpenAI model available to your account that supports tool calling. Even if your chosen model also supports native structured output, specifying `ToolStrategy` explicitly demonstrates this mechanism. This example does not automatically load a `.env` file.

```python
# LIVE_API_REQUIRED
import os
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class Revenue(BaseModel):
    amount: float = Field(ge=0, description="Amount in individual currency units")
    currency: str = Field(description="Three-letter currency code")

model = ChatOpenAI(model=os.environ["TOOL_CALLING_MODEL"])
agent = create_agent(
    model=model,
    tools=[],
    response_format=ToolStrategy(Revenue, handle_errors=True),
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Extract: revenue was 125000 EUR."}]},
    config={"recursion_limit": 10},
)
revenue = result["structured_response"]
print(type(revenue).__name__)
print(revenue.model_dump())
```

**Expected shape on a successful extraction** (a live model's output is not guaranteed):

```text
Revenue
{'amount': 125000.0, 'currency': 'EUR'}
```

**Other choices:** A requests an unsupported capability in the stated scenario. C disables the structured-output contract. D gives guidance without the required validation.

### 29. Inserting chat history as separate messages (Easy)

*Source: LangChain-M-Set1, Q09.*

`history` contains a `HumanMessage` followed by an `AIMessage`. You want to preserve these as two messages with their original roles. What belongs between the system message and the new question in the prompt?

- **A.** `("system", "{history}")`
- **B.** `MessagesPlaceholder("history")`
- **C.** `("human", "{history}")` with history serialized into JSON.
- **D.** One human message containing the history and new question together.

**Answer: B — `MessagesPlaceholder` inserts the supplied messages individually.**

```python
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

history = [
    HumanMessage(content="Which company are we discussing?"),
    AIMessage(content="Acme."),
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer briefly."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

prompt_value = prompt.invoke({
    "history": history,
    "question": "What was its revenue?",
})

for message in prompt_value.to_messages():
    print(f"{message.type}: {message.content}")
```

**Expected output:**

```text
system: Answer briefly.
human: Which company are we discussing?
ai: Acme.
human: What was its revenue?
```

**Remember:** `prompt.invoke(...)` returns a `ChatPromptValue` here. `.to_messages()` gives you the actual message list. A placeholder preserves roles; inserting a list into `{history}` inside one text template does not.

**Other choices:** A changes the history into system content. C and D turn separate turns into one block of human text.

### 30. Keeping the original question after a search rewrite (Medium)

*Source: LangChain-M-Set1, Q10.*

The user asks, `Compare Acme revenue in 2024 and 2025.` A query rewriter creates the search string `Acme revenue 2024 2025`. Retrieval works, but the answer no longer performs the comparison. Which data flow keeps the user's task intact?

- **A.** Keep the original question for the answering prompt; use the rewritten string only to search.
- **B.** Replace the original question everywhere with the search string.
- **C.** Raise the answer model's temperature.
- **D.** Treat all rewritten searches as new instructions from the user.

**Answer: A — search terms and the user's requested task have different jobs.**

The prompt needs the word “Compare.” Keep `question` unchanged and add a separate `search_query` field.

```python
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

def rewrite_for_search(question):
    # Scripted rewrite for this one teaching example.
    return "Acme revenue 2024 2025"

def search(query):
    index = {
        "Acme revenue 2024 2025": [
            Document(page_content="2024 revenue: 100 million EUR."),
            Document(page_content="2025 revenue: 112 million EUR."),
        ]
    }
    return index.get(query, [])

prepare = (
    RunnablePassthrough.assign(
        search_query=lambda data: rewrite_for_search(data["question"])
    )
    | RunnablePassthrough.assign(
        context=lambda data: "\n".join(
            doc.page_content for doc in search(data["search_query"])
        )
    )
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use the supplied evidence."),
    ("human", "Question: {question}\nEvidence:\n{context}"),
])

input_data = {"question": "Compare Acme revenue in 2024 and 2025."}
prepared = prepare.invoke(input_data)
print(prepared["search_query"])
print(prompt.invoke(prepared).to_messages()[-1].content)
```

**Expected output:**

```text
Acme revenue 2024 2025
Question: Compare Acme revenue in 2024 and 2025.
Evidence:
2024 revenue: 100 million EUR.
2025 revenue: 112 million EUR.
```

**Other choices:** B continues to discard the comparison instruction. C cannot restore missing input. D promotes internal search strings into user instructions.

### 31. Using compatible query and document embeddings (Medium)

*Source: LangChain-M-Set1, Q11.*

An index stores document vectors from embedding model A. You switch only query embeddings to unrelated model B. Both produce 1,536 numbers per vector, but retrieval becomes poor. What should you check first?

- **A.** Increase the number of results indefinitely.
- **B.** Assume equal vector length guarantees compatibility.
- **C.** Check whether query and document embeddings belong to compatible embedding spaces.
- **D.** Add zeros to both vectors until they have more dimensions.

**Answer: C — matching vector length does not give the coordinates matching meanings.**

Use the compatible query encoder for the existing index, or rebuild the document index for the new embedding model. Some systems deliberately use different, jointly trained query/document encoders; the requirement is compatibility.

**Small numerical example — these are hand-chosen teaching vectors, not outputs of real embedding models:**

```python
# Both document vectors have two dimensions.
document_vectors = {
    "Revenue report": [1.0, 0.0],
    "Staffing report": [0.0, 1.0],
}

def dot_product(left, right):
    return sum(a * b for a, b in zip(left, right))

def nearest_document(query_vector):
    return max(
        document_vectors,
        key=lambda name: dot_product(query_vector, document_vectors[name]),
    )

# Same question: "What was revenue?"
query_from_compatible_model = [1.0, 0.0]
query_from_unrelated_model = [0.0, 1.0]

print(nearest_document(query_from_compatible_model))
print(nearest_document(query_from_unrelated_model))
```

**Expected output:**

```text
Revenue report
Staffing report
```

All vectors have the same length; the second query still points at the wrong document. The example uses unit vectors, for which dot-product ranking also matches cosine-similarity ranking.

**Other choices:** A may return more irrelevant material without fixing compatibility. B mistakes dimensionality for meaning. D changes length without aligning the coordinates.

### 32. Keeping source and page information for citations (Medium)

*Source: LangChain-M-Set1, Q12.*

Retrieved documents have text, a stable evidence ID, a source ID, and a page number. Your formatter sends only their text to the model. Later, the model invents page numbers. What should you change?

- **A.** Treat retrieval position `1`, `2`, `3` as the source page number.
- **B.** Ask the model to infer page numbers from the writing style.
- **C.** Give all documents the same evidence ID.
- **D.** Send evidence IDs with the text, preserve an ID-to-source/page mapping, and check returned IDs.

**Answer: D — keep provenance in your application and give the model usable evidence labels.**

Let the model cite a supplied ID such as `[report-2025:p7:revenue]`. Your code resolves that ID to the real source and page. Do not ask the model to reconstruct metadata that was discarded.

```python
from langchain_core.documents import Document

documents = [Document(
    page_content="Revenue grew 12%.",
    metadata={
        "evidence_id": "report-2025:p7:revenue",
        "source_id": "report-2025.pdf",
        "page": 7,  # This example stores displayed page numbers, starting at 1.
    },
)]

evidence_map = {
    doc.metadata["evidence_id"]: doc.metadata
    for doc in documents
}
context = "\n".join(
    f"[{doc.metadata['evidence_id']}] {doc.page_content}"
    for doc in documents
)
print(context)

def render_citation(evidence_id):
    if evidence_id not in evidence_map:
        raise ValueError("Unknown evidence ID")
    source = evidence_map[evidence_id]
    return f"{source['source_id']}, page {source['page']}"

# Simulated citation ID returned by an answer model.
print(render_citation("report-2025:p7:revenue"))
try:
    render_citation("invented-id")
except ValueError as error:
    print(error)
```

**Expected output:**

```text
[report-2025:p7:revenue] Revenue grew 12%.
report-2025.pdf, page 7
Unknown evidence ID
```

**Remember:** A valid ID proves that the cited evidence exists in the supplied set. Checking whether it actually supports the answer is a separate factual check. Confirm your loader's page-number convention before displaying citations.

**Other choices:** A confuses rank with page. B guesses missing information. C makes distinct sources indistinguishable.

### 33. Reducing duplicate search results with MMR (Medium)

*Source: LangChain-M-Set1, Q13.*

You ask for different causes of revenue growth. Ordinary similarity search returns two nearly identical passages about higher prices, missing a relevant passage about new customers. Your vector store supports maximal marginal relevance (MMR). Which experiment addresses this repetition?

- **A.** Subtract the same number from every similarity score and keep the ranking.
- **B.** Keep the duplicated evidence and ask the model to invent another cause.
- **C.** Give MMR fewer candidates than the number of results you want.
- **D.** Fetch a broader candidate pool and let MMR select a relevant, less repetitive subset.

**Answer: D — MMR balances similarity to the query with diversity among selected results.**

`fetch_k` controls how many candidates MMR considers. `k` controls how many documents it returns. For this interface, a smaller `lambda_mult` gives diversity more weight.

**Complete offline example — deliberately chosen vectors make the behavior visible. This is not a real embedding model. Requires NumPy in addition to `langchain-core`.**

```python
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

class TeachingEmbeddings(Embeddings):
    def embed_documents(self, texts):
        vectors = {
            "Higher prices increased revenue.": [1.0, 0.0],
            "Price increases raised revenue.": [0.99, 0.01],
            "New customers increased revenue.": [0.6, 0.8],
        }
        return [vectors[text] for text in texts]

    def embed_query(self, text):
        return [1.0, 0.0]

store = InMemoryVectorStore(embedding=TeachingEmbeddings())
store.add_documents([
    Document(page_content="Higher prices increased revenue."),
    Document(page_content="Price increases raised revenue."),
    Document(page_content="New customers increased revenue."),
])

similarity = store.as_retriever(search_kwargs={"k": 2})
diverse = store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 2, "fetch_k": 3, "lambda_mult": 0.3},
)

query = "What caused revenue growth?"
print([doc.page_content for doc in similarity.invoke(query)])
print([doc.page_content for doc in diverse.invoke(query)])
```

**Expected output:**

```text
['Higher prices increased revenue.', 'Price increases raised revenue.']
['Higher prices increased revenue.', 'New customers increased revenue.']
```

**Remember:** The toy vectors demonstrate selection behavior. MMR does not guarantee that all causes are found or that diverse results are useful; inspect relevance as well as variety.

**Other choices:** A preserves the ranking. B fabricates evidence. C gives the selector too few alternatives.

### 34. Interpreting distance scores correctly (Easy)

*Source: LangChain-M-Set1, Q14.*

Your FAISS search is explicitly configured to return **squared Euclidean distances**, not similarity scores or probabilities. It returns `A=0.12`, `B=0.65`, `C=1.40`. A filter keeps scores `>= 0.80` as “best matches.” What is wrong?

- **A.** Smaller distance means closer; this filter keeps only the farthest result, C.
- **B.** Larger distance always means more relevant.
- **C.** The scores must sum to one because they are probabilities.
- **D.** Calling through a retriever automatically makes these scores probabilities.

**Answer: A — lower is better under this stated distance contract.**

```python
distances = {"A": 0.12, "B": 0.65, "C": 1.40}

wrong = [name for name, distance in distances.items() if distance >= 0.80]
correct_direction = [
    name for name, distance in distances.items()
    if distance <= 0.80
]
nearest_first = sorted(distances, key=distances.get)

print(wrong)
print(correct_direction)
print(nearest_first)
```

**Expected output:**

```text
['C']
['A', 'B']
['A', 'B', 'C']
```

The number `0.80` is only an illustration. A useful threshold needs evaluation on your queries. Do not assume every vector-store method uses the same metric, direction, or normalization.

**Other choices:** B reverses distance meaning. C mistakes distances for probabilities. D assumes an automatic conversion that the question does not provide.

### 35. Keeping table headers and units with a chunk (Medium)

*Source: LangChain-M-Set1, Q15.*

A PDF table has columns `Year` and `Revenue (EUR thousands)`. Fixed character splitting produces a retrieved chunk containing only `2025 | 125`. The answer model mistakes this for 125 EUR. Which ingestion change targets the problem?

- **A.** Increase overlap until almost the entire PDF appears in every chunk.
- **B.** Preserve the relevant headers and units with each table segment, plus source metadata.
- **C.** Remove headers because they repeat.
- **D.** Ask the model to guess the missing unit.

**Answer: B — the cell needs its header to retain its meaning.**

The following code starts from already extracted table rows. It demonstrates how to represent them as useful documents; it is not a PDF table-extraction implementation.

```python
from langchain_core.documents import Document

# Values extracted from one PDF table, including its header.
rows = [
    {"year": 2024, "revenue": 100},
    {"year": 2025, "revenue": 125},
]
revenue_header = "Revenue (EUR thousands)"

chunks = []
for row in rows:
    chunks.append(Document(
        page_content=(
            f"Year: {row['year']}\n"
            f"{revenue_header}: {row['revenue']}"
        ),
        metadata={"source": "annual-report.pdf", "page": 7},
    ))

print(chunks[1].page_content)
print(chunks[1].metadata)
```

**Expected output:**

```text
Year: 2025
Revenue (EUR thousands): 125
{'source': 'annual-report.pdf', 'page': 7}
```

Now the retrieved row includes the information needed to interpret 125 as 125,000 EUR. Larger tables may use several rows per chunk; the principle is to keep the relevant structural context.

**Other choices:** A adds duplication without specifically preserving table relationships. C removes essential meaning. D replaces source evidence with a guess.

### 36. Knowing what a reranker can and cannot recover (Medium)

*Source: LangChain-M-Set1, Q16.*

A retriever supplies 20 candidate documents. A reranker selects the best 5 **from those 20**. The passage needed to answer the question is missing from all 20. What should you improve first?

- **A.** Raise generation temperature to reconstruct the missing passage.
- **B.** Select 10 from the same 20; this necessarily recovers the missing passage.
- **C.** Improve candidate retrieval so the required passage can reach the reranker.
- **D.** Change citation display order.

**Answer: C — a reranker cannot select a document outside its input set.**

**Offline illustration — the tiny ranking function is a teaching stand-in, not a trained reranking model:**

```python
from langchain_core.documents import Document

corpus = [
    Document(page_content="Office hours", metadata={"id": "hours"}),
    Document(page_content="Contact details", metadata={"id": "contact"}),
    Document(page_content="Refund window is 30 days.", metadata={"id": "refund"}),
]

def rerank(candidates, query, k):
    # Simple keyword score; only candidates can appear in the result.
    ordered = sorted(
        candidates,
        key=lambda doc: query.lower() in doc.page_content.lower(),
        reverse=True,
    )
    return ordered[:k]

bad_candidates = corpus[:2]  # The needed passage never reached the reranker.
print([doc.metadata["id"] for doc in rerank(bad_candidates, "refund", k=2)])

# Improved retrieval searches the complete corpus for the requested topic.
better_candidates = [
    doc for doc in corpus if "refund" in doc.page_content.lower()
]
print([doc.metadata["id"] for doc in rerank(better_candidates, "refund", k=1)])
```

**Expected output:**

```text
['hours', 'contact']
['refund']
```

Selecting every bad candidate still cannot return `refund`. Investigate whether the document was indexed and whether the retrieval query and candidate depth can find it.

**Other choices:** A does not supply evidence. B only expands selection within the same incomplete set. D changes presentation, not retrieval.

### 37. Giving tools clear purposes and validated arguments (Medium)

*Source: LangChain-M-Set1, Q17.*

An agent confuses two tools: one searches today's policy and the other searches the policy effective on a historical date. Both descriptions say only “Search policies,” and dates accept any string. Which improvement addresses both problems?

- **A.** Repeat “Search policies” several times.
- **B.** Rename the tools `tool_a` and `tool_b`.
- **C.** Explain their distinct time scopes and validate identifiers and date arguments.
- **D.** Add more tools with the same vague description.

**Answer: C — descriptions guide selection; input schemas validate the call's arguments.**

```python
from datetime import date
from pydantic import BaseModel, Field, ValidationError
from langchain_core.tools import tool

class CurrentPolicyInput(BaseModel):
    policy_id: str = Field(pattern=r"^POL-\d+$", description="ID such as POL-7")

class ArchivedPolicyInput(CurrentPolicyInput):
    as_of: date = Field(description="Historical effective date, YYYY-MM-DD")

@tool(args_schema=CurrentPolicyInput)
def search_current_policy(policy_id: str) -> str:
    """Get the policy currently in force. Use for questions about today's rules."""
    policies = {"POL-7": "Current refund window: 30 days."}
    return policies.get(policy_id, "Policy not found")

@tool(args_schema=ArchivedPolicyInput)
def search_archived_policy(policy_id: str, as_of: date) -> str:
    """Get policy rules effective on a historical date. Use for past-date questions."""
    snapshots = {("POL-7", "2024-01-01"): "Historical refund window: 14 days."}
    return snapshots.get((policy_id, as_of.isoformat()), "Snapshot not found")

print(search_current_policy.invoke({"policy_id": "POL-7"}))
print(search_archived_policy.invoke({
    "policy_id": "POL-7", "as_of": "2024-01-01"
}))

try:
    search_archived_policy.invoke({"policy_id": "POL-7", "as_of": "last year"})
except ValidationError:
    print("Invalid date rejected")
```

**Expected output:**

```text
Current refund window: 30 days.
Historical refund window: 14 days.
Invalid date rejected
```

**Remember:** The annotations here are functional: they define and validate tool inputs. A date schema rejects malformed dates; it does not prove the model selected the right historical date. The example archive contains only one explicit snapshot.

**Other choices:** A repeats the ambiguity. B removes useful names. D creates more indistinguishable choices.

### 38. Awaiting a chain in an async handler (Medium)

*Source: LangChain-M-Set1, Q18.*

An `async def` request handler directly calls a network-blocking `chain.invoke(...)`. The provider supports an async integration. Other requests stall while this call waits. What is the appropriate change?

- **A.** Keep `.invoke()` and request longer answers.
- **B.** Use `await chain.ainvoke(...)` and check custom stages for blocking code.
- **C.** Call `chain.ainvoke(...)` without awaiting or scheduling it.
- **D.** Add a busy loop that waits for `.invoke()` to finish.

**Answer: B — use the async interface and let the event loop make progress while I/O waits.**

The example below isolates the handler logic without requiring a web framework. `asyncio.sleep()` simulates nonblocking network waiting; it is not a real model call.

```python
import asyncio
from langchain_core.runnables import RunnableLambda

async def fetch_revenue(company):
    await asyncio.sleep(0.01)  # Simulated asynchronous I/O
    revenues = {"Acme": 125, "Beta": 90}
    return {"company": company, "revenue": revenues[company]}

chain = RunnableLambda(fetch_revenue)

async def handle_request(company):
    result = await chain.ainvoke(company)
    return result

async def main():
    results = await asyncio.gather(
        handle_request("Acme"),
        handle_request("Beta"),
    )
    print(results)

asyncio.run(main())
```

**Expected output:**

```text
[{'company': 'Acme', 'revenue': 125}, {'company': 'Beta', 'revenue': 90}]
```

Run this as a Python script. In a notebook already running an event loop, use `await main()` instead of `asyncio.run(main())`. If a custom stage must use blocking synchronous I/O, move it off the event-loop thread, for example with `await asyncio.to_thread(blocking_function, argument)`. Merely declaring that stage `async` does not make its blocking calls asynchronous.

**Other choices:** A can increase waiting time. C creates a coroutine without obtaining its result. D occupies the event loop instead of yielding.

### 39. Turning JSON text into a validated Boolean field (Easy)

*Source: LangChain-M-Set1, Q19.*

The model returns the text `{"approved": false}`. `StrOutputParser()` gives you that text as a Python string. A downstream function needs `{"approved": False}` as a dictionary containing a real Boolean. What should you do?

- **A.** Return `True` whenever the string contains the word `approved`.
- **B.** Pass the string directly because JSON-looking text is already a dictionary.
- **C.** Use `bool(text)` to read the approval decision.
- **D.** Parse the JSON and validate the required field before passing the dictionary.

**Answer: D — serialized JSON text and a Python dictionary are different values.**

This example uses Pydantic's `model_validate_json()` to parse and validate in one step. `StrictBool` rejects a string such as `"false"` as the approval value.

```python
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, StrictBool

class Approval(BaseModel):
    approved: StrictBool

response = AIMessage(content='{"approved": false}')
text = StrOutputParser().invoke(response)
print(isinstance(text, str))
print(bool(text))  # Tests whether the entire string is nonempty.

validated = Approval.model_validate_json(text)
payload = validated.model_dump()
print(payload)
print(type(payload["approved"]).__name__)
```

**Expected output:**

```text
True
True
{'approved': False}
bool
```

**Other choices:** A tests for a field name, not its value. B confuses an encoding with the decoded object. C tests string emptiness, so even the text `"false"` is truthy.

### 40. Making retrieval mandatory before an answer (Medium)

*Source: LangChain-M-Set1, Q20.*

An internal Q&A app must search its approved knowledge base before answering **every** question. If it finds no supporting evidence, it must say so. Which flow directly enforces that requirement?

- **A.** Always retrieve first, check for evidence, then generate an answer or return an insufficient-evidence message.
- **B.** Let an agent decide whether search is needed.
- **C.** Generate an answer first and search only to add citations.
- **D.** Count any tool call as a knowledge-base search.

**Answer: A — make required retrieval part of the program's control flow.**

An optional model decision cannot guarantee a mandatory step. A small fixed chain is sufficient for this requirement.

**Complete offline example — the answering function returns the supplied evidence as a deterministic stand-in for generation:**

```python
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

events = []
knowledge_base = {
    "What is the refund window?": [
        Document(page_content="The refund window is 30 days.")
    ]
}

def retrieve(question):
    events.append("retrieve")
    return knowledge_base.get(question, [])

def generate_answer(question, documents):
    events.append("generate")
    # Scripted answer for this example; uses the retrieved text.
    return documents[0].page_content

def answer_or_decline(data):
    if not data["documents"]:
        return "I found no supporting evidence in the approved knowledge base."
    return generate_answer(data["question"], data["documents"])

chain = (
    RunnablePassthrough.assign(
        documents=lambda data: retrieve(data["question"])
    )
    | RunnableLambda(answer_or_decline)
)

print(chain.invoke({"question": "What is the refund window?"}))
print(chain.invoke({"question": "What is next year's revenue?"}))
print(events)
```

**Expected output:**

```text
The refund window is 30 days.
I found no supporting evidence in the approved knowledge base.
['retrieve', 'generate', 'retrieve']
```

Both requests searched; only the supported request reached generation. In a real application, replace the scripted answer function with your prompt/model stage and evaluate evidence relevance, not merely whether the result list is nonempty.

**Other choices:** B keeps search discretionary. C creates an answer before consulting evidence. D does not ensure the approved knowledge base was consulted.

## Part 3: Applied decisions

### 41. Put the parser inside the fallback boundary (Medium)

*Source: LangChain-M-H-Set2, Q06.*

Your primary chain is `prompt_a | model_a | parser_a`. Sometimes the model returns text that `parser_a` cannot parse. You want that parsing error to trigger a fallback that uses its **own prompt, model, and parser**. Both complete chains accept the original dictionary input. Assume the parsing error is included in the fallback's handled exceptions.

Which composition meets those requirements?

- **A.** `prompt_a | model_a.with_fallbacks([model_b]) | parser_a`
- **B.** `(prompt_a | model_a | parser_a).with_fallbacks([prompt_b | model_b | parser_b])`
- **C.** `prompt_a | (model_a | parser_a).with_fallbacks([model_b])`
- **D.** `(prompt_a | model_a).with_fallbacks([prompt_b | model_b]) | parser_a`

**Answer: B — wrap the complete primary chain and supply a complete fallback chain.**

The error must happen **inside** the runnable protected by `with_fallbacks`. Here, that runnable includes `parser_a`. The fallback then receives the original input dictionary, so `prompt_b` can build a different prompt.

A and D leave the parser outside the protected block. C includes the parser, but its fallback is just `model_b`: it receives the already formatted primary prompt and does not use the required alternate prompt and parser.

**Runnable example — offline.** The two model functions are deliberate stubs. One returns a bad amount; the other returns valid JSON. The prompts, parser, exception, and fallback behavior are real LangChain components.

```python
from pydantic import BaseModel
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

class Revenue(BaseModel):
    revenue: float

prompt_a = ChatPromptTemplate.from_template("Extract revenue: {report}")
prompt_b = ChatPromptTemplate.from_template(
    "Return a numeric revenue field in JSON. Report: {report}"
)

def bad_model(prompt_value):
    # Deliberately invalid for the float field in Revenue.
    return AIMessage(content='{"revenue": "unknown"}')

def backup_model(prompt_value):
    print("Backup prompt:", prompt_value.to_messages()[0].content)
    return AIMessage(content='{"revenue": 12.0}')

parser_a = PydanticOutputParser(pydantic_object=Revenue)
parser_b = PydanticOutputParser(pydantic_object=Revenue)

primary = prompt_a | RunnableLambda(bad_model) | parser_a
backup = prompt_b | RunnableLambda(backup_model) | parser_b

chain = primary.with_fallbacks(
    [backup], exceptions_to_handle=(OutputParserException,)
)
result = chain.invoke({"report": "Revenue was 12 dollars."})
print(result.revenue)
```

Expected output:

```text
Backup prompt: Return a numeric revenue field in JSON. Report: Revenue was 12 dollars.
12.0
```

**Three lines to understand:** `primary` defines everything that can trigger this fallback; `[backup]` defines the alternate complete path; `chain.invoke(...)` supplies the same original dictionary to the backup when the primary fails.

### 42. Check capabilities before choosing the cheapest model (Medium)

*Source: LangChain-M-H-Set2, Q07.*

A request requires both tool calling and structured output. Your application has three model choices with different capabilities and costs. You must preserve both requirements. What should the routing code do first?

- **A.** Pick a model randomly and let the output parser supply any missing capability.
- **B.** Pick the cheapest model whenever the prompt is short.
- **C.** Pick the cheapest model and remove whichever requirements it cannot support.
- **D.** Keep only models that support every required capability, then choose the cheapest eligible model.

**Answer: D — eligibility first, cost second.**

A short prompt can still require tool calling. A parser cannot add a capability that the chosen provider does not offer. Removing a requirement changes the requested behavior.

**Runnable example — offline, ordinary Python.** The names and costs below are fictional configuration data, not claims about any real model.

```python
models = [
    {"name": "basic", "cost_units": 1, "capabilities": {"text"}},
    {
        "name": "balanced",
        "cost_units": 3,
        "capabilities": {"text", "tools", "structured_output"},
    },
    {
        "name": "premium",
        "cost_units": 8,
        "capabilities": {"text", "tools", "structured_output"},
    },
]

required = {"tools", "structured_output"}
eligible = [
    model for model in models
    if required.issubset(model["capabilities"])
]

if not eligible:
    raise ValueError("No model supports all required capabilities.")

selected = min(eligible, key=lambda model: model["cost_units"])
print("Eligible:", [model["name"] for model in eligible])
print("Selected:", selected["name"])
```

Expected output:

```text
Eligible: ['balanced', 'premium']
Selected: balanced
```

`required.issubset(...)` asks whether **all** required features are present. `min(...)` compares cost only after that check. In an actual application, populate the capability configuration from the integrations and models you have verified.

### 43. Calculate latency when two retrievers run in parallel (Medium)

*Source: LangChain-M-H-Set2, Q08.*

Two independent retrievers take **800 ms** and **1,400 ms**. Run them concurrently with `RunnableParallel`. The next stage must wait for **both results**, then reranking takes **300 ms**. After reranking, the model takes another **500 ms** to produce its first token. Ignore overhead and resource contention.

What is the ideal total time to the first token?

- **A.** **2,200 ms:** `max(800, 1400) + 300 + 500`.
- **B.** **3,000 ms:** `800 + 1400 + 300 + 500`.
- **C.** **1,400 ms:** the later stages take no additional time.
- **D.** **800 ms:** the chain automatically ignores the slower result.

**Answer: A — the retrieval stage takes as long as its slowest branch.**

Both branches begin concurrently, but the next stage needs both results. The dependent stages still take additional time. B is the sequential calculation. C omits reranking and generation. D changes the stated requirement to use both retrieval results.

**Runnable example — offline timing simulation.** Delays are divided by ten so the example finishes quickly. The retrievers and later stages are stubs; `RunnableParallel` performs the actual concurrent execution.

```python
from time import sleep
from langchain_core.runnables import RunnableLambda, RunnableParallel

def retrieve_policy(question):
    sleep(0.08)  # Represents 800 ms at one-tenth scale.
    return ["Policy evidence for: " + question]

def retrieve_finance(question):
    sleep(0.14)  # Represents 1,400 ms.
    return ["Finance evidence for: " + question]

def rerank_stub(results):
    # This runs only after both retrieval branches have returned.
    sleep(0.03)  # Represents 300 ms.
    return results["policy"] + results["finance"]

def first_token_stub(documents):
    assert len(documents) == 2
    sleep(0.05)  # Represents 500 ms.
    return "The"

retrieval = RunnableParallel(
    policy=RunnableLambda(retrieve_policy),
    finance=RunnableLambda(retrieve_finance),
)
chain = retrieval | RunnableLambda(rerank_stub) | RunnableLambda(first_token_stub)

print("First token:", chain.invoke("What changed?"))
print("Ideal latency:", max(800, 1400) + 300 + 500, "ms")
```

Expected output:

```text
First token: The
Ideal latency: 2200 ms
```

The printed latency comes from the stated assumptions, not a benchmark of your machine. Parallelism reduces waiting time here; both retrieval operations still run.

### 44. Keep an unknown amount separate from zero (Medium)

*Source: LangChain-M-H-Set2, Q09.*

Your extraction schema uses `debt_amount: float = 0.0`. If a report does not disclose debt, the default becomes zero. But downstream code interprets zero as **confirmed no debt**.

Which schema change preserves the difference between “not disclosed” and “confirmed zero”?

- **A.** Use `-1.0` for missing debt without telling downstream consumers.
- **B.** Keep the zero default and ask the model to be more confident.
- **C.** Permit an explicit unknown value such as `None`, retain supporting evidence, and make consumers handle unknown separately.
- **D.** Remove the field and let consumers substitute zero when it is missing.

**Answer: C — `None` can represent unknown; `0.0` remains an actual amount.**

A creates an undocumented convention. B does not fix the schema's meaning. D recreates the same zero default elsewhere.

**Runnable example — offline.** This demonstrates a Pydantic schema that could be passed to a structured-output chain. It does not invoke a model.

```python
from pydantic import BaseModel

class DebtResult(BaseModel):
    debt_amount: float | None
    evidence: str | None

unknown = DebtResult(debt_amount=None, evidence=None)
confirmed_zero = DebtResult(
    debt_amount=0.0,
    evidence="The company had no outstanding debt at year-end.",
)

def describe_debt(result):
    if result.debt_amount is None:
        return "Debt was not disclosed."
    return f"Reported debt: {result.debt_amount:.2f}"

print(describe_debt(unknown))
print(describe_debt(confirmed_zero))
print(confirmed_zero.evidence)
```

Expected output:

```text
Debt was not disclosed.
Reported debt: 0.00
The company had no outstanding debt at year-end.
```

Use `is None`, not `if not result.debt_amount`: both `None` and `0.0` are falsy in Python. In this schema, both keys must be supplied, but either value may be `None`. Schema validation checks the data shape; checking that the evidence supports the amount is a separate step.

### 45. Apply a supplied reciprocal-rank formula (Medium)

*Source: LangChain-M-H-Set2, Q10.*

Two retrievers return ranked results. To combine their rankings, use this exact formula, where rank starts at 1:

`score(document) = 1 / (60 + rank_in_list_1) + 1 / (60 + rank_in_list_2)`

Document **A** is ranked **1 and 6**. Document **B** is ranked **2 and 2**. A higher combined score ranks first. Which result is correct?

- **A.** You cannot calculate the result without the retrievers' raw similarity scores.
- **B.** A wins because being first in either list always wins.
- **C.** They tie because both documents appear in both lists.
- **D.** B wins: its score is approximately `0.03226`, versus A's `0.03154`.

**Answer: D — substitute the ranks into the given formula.**

A uses `1/61 + 1/66`; B uses `1/62 + 1/62`. This calculation needs ranks, not raw similarity scores. Being first in one list is not an automatic win, and appearing in two lists does not imply equal scores.

**Runnable example — offline, ordinary Python.**

```python
ranks = {
    "A": [1, 6],
    "B": [2, 2],
}

def reciprocal_rank_score(document_ranks):
    return sum(1 / (60 + rank) for rank in document_ranks)

scores = {
    document: reciprocal_rank_score(document_ranks)
    for document, document_ranks in ranks.items()
}

for document, score in scores.items():
    print(f"{document}: {score:.5f}")

winner = max(scores, key=scores.get)
print("Winner:", winner)
```

Expected output:

```text
A: 0.03154
B: 0.03226
Winner: B
```

You do not need to memorize this constant or derive a ranking algorithm to answer the question. Read the supplied scoring rule and implement it accurately.

### 46. Retrieve both facts needed for a date comparison (Medium)

*Source: LangChain-M-H-Set2, Q11.*

The user asks: “Did Acme's acquisition happen before its credit downgrade?” The acquisition date and downgrade date are recorded in different reports. Your current search repeatedly retrieves only acquisition reports.

Which change directly supplies the missing information?

- **A.** Allow the model to write a longer answer while giving it the same evidence.
- **B.** Retrieve the acquisition date and downgrade date separately, keep their sources, then compare the dates.
- **C.** Answer using only the acquisition date if its similarity score is high.
- **D.** Shorten the query to `Acme` and reuse the same acquisition-only results.

**Answer: B — a comparison needs both dates.**

The first retrieval supplies one fact; the second supplies the other. Neither a longer response nor a high similarity score can supply the missing date. D does not address the evidence gap.

**Runnable example — offline.** This tiny index uses exact metadata filtering, not embeddings. The event dates have already been extracted into metadata; the example focuses on retrieving the two required pieces of evidence and comparing them.

```python
from datetime import date
from langchain_core.documents import Document

reports = [
    Document(
        page_content="Acme completed the acquisition on February 10, 2025.",
        metadata={
            "company": "Acme", "event": "acquisition",
            "date": "2025-02-10", "source": "acquisition-report.txt",
        },
    ),
    Document(
        page_content="Acme's credit was downgraded on March 5, 2025.",
        metadata={
            "company": "Acme", "event": "downgrade",
            "date": "2025-03-05", "source": "credit-report.txt",
        },
    ),
]

def retrieve_event(company, event):
    matches = [
        doc for doc in reports
        if doc.metadata["company"] == company
        and doc.metadata["event"] == event
    ]
    if len(matches) != 1:
        raise ValueError(f"Need one unambiguous source for {event}.")
    return matches[0]

acquisition = retrieve_event("Acme", "acquisition")
downgrade = retrieve_event("Acme", "downgrade")

acquisition_date = date.fromisoformat(acquisition.metadata["date"])
downgrade_date = date.fromisoformat(downgrade.metadata["date"])

print("Acquisition came first:", acquisition_date < downgrade_date)
print("Acquisition source:", acquisition.metadata["source"])
print("Downgrade source:", downgrade.metadata["source"])
```

Expected output:

```text
Acquisition came first: True
Acquisition source: acquisition-report.txt
Downgrade source: credit-report.txt
```

`date.fromisoformat` turns the stored ISO strings into date objects. If either fact is missing or ambiguous, this example raises an error instead of inventing a comparison.

### 47. Choose the policy that applied on the requested date (Medium)

*Source: LangChain-M-H-Set2, Q12.*

The user asks which policy applied on **March 1, 2025**. Retrieval returns these two versions:

- Version 1 applied from January 1 through March 31, 2025, inclusive. Its similarity score is `0.82`.
- Version 2 applies starting April 1, 2025. Its similarity score is `0.95`.

Assume the effective-date metadata is correct. Which rule should choose the evidence?

- **A.** Always use the higher similarity score.
- **B.** Always use the newest version, even for historical dates.
- **C.** Use the version whose effective dates include March 1, and cite that version.
- **D.** Average the requirements from both versions.

**Answer: C — Version 1 applied on the requested date.**

A similarity score indicates relevance to the query; it does not establish when a policy applied. The newest version does not automatically apply to past dates, and averaging rules can invent a policy that never existed.

**Runnable example — offline.** The code selects from already retrieved documents. It demonstrates date filtering without depending on a vector database's filter syntax.

```python
from datetime import date
from langchain_core.documents import Document

documents = [
    Document(
        page_content="Version 1: expense claims require a receipt.",
        metadata={
            "source": "policy-v1.txt", "score": 0.82,
            "effective_from": "2025-01-01",
            "effective_through": "2025-03-31",
        },
    ),
    Document(
        page_content="Version 2: expense claims require a receipt and approval.",
        metadata={
            "source": "policy-v2.txt", "score": 0.95,
            "effective_from": "2025-04-01",
            "effective_through": None,
        },
    ),
]

requested_date = date(2025, 3, 1)

def applies_on(document, day):
    metadata = document.metadata
    start = date.fromisoformat(metadata["effective_from"])
    end_text = metadata["effective_through"]
    end = date.fromisoformat(end_text) if end_text else date.max
    return start <= day <= end

applicable = [doc for doc in documents if applies_on(doc, requested_date)]
if len(applicable) != 1:
    raise ValueError("No single applicable policy version was found.")

selected = applicable[0]
print(selected.page_content)
print("Source:", selected.metadata["source"])
```

Expected output:

```text
Version 1: expense claims require a receipt.
Source: policy-v1.txt
```

The important comparison is `start <= day <= end`. This example uses inclusive end dates explicitly, so March 31 belongs to Version 1 and April 1 belongs to Version 2.

### 48. Remove chunks that disappeared from a revised source (Medium)

*Source: LangChain-M-H-Set2, Q13.*

The old version of `policy.txt` produced chunk IDs `policy:0`, `policy:1`, and `policy:2`. A complete new version produces only `policy:0` and `policy:1`.

Your update operation inserts new IDs and replaces matching IDs, but **does not delete absent IDs**. After the update, retrieval still finds obsolete `policy:2`. What additional operation fixes this?

- **A.** Track which IDs belong to the source and delete old IDs missing from its complete new version.
- **B.** Keep inserting copies of the new chunks under random IDs.
- **C.** Force the new source to produce three chunks even if its content is shorter.
- **D.** Leave the old chunk in place and change only the answer prompt.

**Answer: A — insertion and replacement do not imply deletion.**

The stale ID is in the old set but not the new set. B creates duplicates, C confuses chunk count with freshness, and D leaves the stale retrieval result available.

**Runnable example — offline, ordinary Python.** A dictionary represents the chunk records so the update behavior is visible. This is a complete refresh of one source, not a partial batch and not a vector-store API implementation.

```python
index = {
    "policy:0": {"source": "policy.txt", "text": "Old introduction"},
    "policy:1": {"source": "policy.txt", "text": "Old requirement"},
    "policy:2": {"source": "policy.txt", "text": "Obsolete exception"},
    "other:0": {"source": "other.txt", "text": "Unrelated document"},
}

new_chunks = {
    "policy:0": {"source": "policy.txt", "text": "New introduction"},
    "policy:1": {"source": "policy.txt", "text": "New requirement"},
}

old_ids = {
    chunk_id for chunk_id, chunk in index.items()
    if chunk["source"] == "policy.txt"
}
new_ids = set(new_chunks)

index.update(new_chunks)  # Inserts/replaces; does not remove policy:2.
print("Stale chunk after update:", "policy:2" in index)

stale_ids = old_ids - new_ids
for chunk_id in stale_ids:
    del index[chunk_id]

print("Deleted:", sorted(stale_ids))
print("Remaining:", sorted(index))
```

Expected output:

```text
Stale chunk after update: True
Deleted: ['policy:2']
Remaining: ['other:0', 'policy:0', 'policy:1']
```

`old_ids - new_ids` is the cleanup set. Restricting `old_ids` to `policy.txt` preserves the unrelated source. For a real store, call its supported delete operation for those stale IDs after confirming that the complete source refresh succeeded.

### 49. Compare systems using the stated error costs (Medium)

*Source: LangChain-M-H-Set2, Q14.*

Two systems are tested on the same 100 questions:

- A: 80 correct answers, 10 wrong answers, 10 abstentions.
- B: 65 correct answers, 4 wrong answers, 31 abstentions.

An **abstention** means the system declines to answer. The agreed cost is **10 per wrong answer**, **1 per abstention**, and **0 per correct answer**. Lower total cost is better. Which system wins **on this test set**?

- **A.** A, because more correct answers always wins regardless of the cost rule.
- **B.** B, because its cost is 71 versus A's 110.
- **C.** A, because its cost is 20 when every unsuccessful answer costs 1.
- **D.** They tie because each system answered the same test set.

**Answer: B — use the specified weights.**

A costs `10 × 10 + 10 = 110`. B costs `4 × 10 + 31 = 71`. B's extra abstentions cost less than its reduction in wrong answers saves. A and C ignore the cost rule; D confuses equal sample size with equal results.

**Runnable example — offline, ordinary Python.**

```python
results = {
    "A": {"correct": 80, "wrong": 10, "abstain": 10},
    "B": {"correct": 65, "wrong": 4, "abstain": 31},
}

def total_cost(result):
    return 10 * result["wrong"] + result["abstain"]

costs = {name: total_cost(result) for name, result in results.items()}

for name, cost in costs.items():
    print(f"{name}: {cost}")

print("Lower-cost system:", min(costs, key=costs.get))
```

Expected output:

```text
A: 110
B: 71
Lower-cost system: B
```

This establishes which system wins under this rule on these 100 questions. It does not establish performance on new questions; use a separate representative test set before generalizing.

### 50. Check critical cases separately from overall accuracy (Medium)

*Source: LangChain-M-H-Set2, Q15.*

A baseline and candidate are evaluated on the **same 1,000 examples**:

- Baseline: passes 900 of 990 ordinary cases and all 10 critical cases.
- Candidate: passes 940 of 990 ordinary cases and 6 of the same 10 critical cases.

The release rule says: **do not release if any critical case that passed before now fails**. What is the correct decision under that rule?

- **A.** Combine both systems' successes and report that as the candidate's score.
- **B.** Release because total accuracy improved from 91.0% to 94.6%.
- **C.** Delete the critical examples from the evaluation.
- **D.** Block the release and investigate the four critical regressions.

**Answer: D — the candidate violates the explicit release rule.**

All ten critical cases passed before, so the candidate's four critical failures are regressions. B ignores that rule. A fabricates a score for a system that was not tested, and C removes the cases that the rule specifically protects.

**Runnable example — offline, ordinary Python.** The lists are already-scored test results: `True` means pass. Positions in each pair of lists refer to the same examples.

```python
baseline_ordinary = [True] * 900 + [False] * 90
candidate_ordinary = [True] * 940 + [False] * 50
baseline_critical = [True] * 10
candidate_critical = [True] * 6 + [False] * 4

baseline_all = baseline_ordinary + baseline_critical
candidate_all = candidate_ordinary + candidate_critical

baseline_accuracy = sum(baseline_all) / len(baseline_all)
candidate_accuracy = sum(candidate_all) / len(candidate_all)

critical_regressions = sum(
    old_passed and not new_passed
    for old_passed, new_passed in zip(baseline_critical, candidate_critical)
)
release_allowed = critical_regressions == 0

print(f"Baseline accuracy: {baseline_accuracy:.1%}")
print(f"Candidate accuracy: {candidate_accuracy:.1%}")
print("Critical regressions:", critical_regressions)
print("Release allowed:", release_allowed)
```

Expected output:

```text
Baseline accuracy: 91.0%
Candidate accuracy: 94.6%
Critical regressions: 4
Release allowed: False
```

`old_passed and not new_passed` identifies a regression on an individual paired example. Overall accuracy and the critical-case rule answer different questions; calculate both.

### 51. Test the features used when replacing a model (Medium)

*Source: LangChain-M-H-Set2, Q18.*

You replace one chat model with a cheaper model through the same LangChain interface. A basic `model.invoke("Hello")` succeeds. Your real application also uses tool calls, streaming, and structured output.

What additional work is needed before calling the replacement compatible with your application?

- **A.** Remove tests for features that the cheaper model fails.
- **B.** Assume having the same `invoke` method guarantees the same behavior.
- **C.** Compare only token prices.
- **D.** Test the actual tool, streaming, and schema contracts, plus representative task quality, latency, and failures.

**Answer: D — the shared interface does not prove that every required behavior works.**

A basic greeting exercises only one path. A removes evidence of incompatibility, B confuses method names with behavior, and C ignores application requirements.

**Runnable example — offline.** `FakeListChatModel` is a LangChain test utility that returns supplied responses. Here it deliberately represents an incompatible candidate: basic text and streaming work, but tool binding and structured output are unsupported. This tests the checking code; it does not establish any real provider's capabilities.

```python
from pydantic import BaseModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessageChunk
from langchain_core.tools import tool

candidate = FakeListChatModel(responses=["READY"])

@tool
def double_number(value: int) -> int:
    """Return twice the supplied integer."""
    return 2 * value

class Quantity(BaseModel):
    value: int

# A text call alone succeeds.
print("Basic text:", candidate.invoke("Hello").text)

def check_tools():
    response = candidate.bind_tools([double_number]).invoke(
        "Use double_number with value 6."
    )
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call["name"] == "double_number"
    assert call["args"] == {"value": 6}
    assert double_number.invoke(call["args"]) == 12

def check_streaming():
    chunks = list(candidate.stream("Reply READY."))
    assert chunks and all(isinstance(chunk, AIMessageChunk) for chunk in chunks)
    assert "".join(chunk.text for chunk in chunks).strip()

def check_structured_output():
    result = candidate.with_structured_output(Quantity).invoke(
        "The quantity is 12. Extract the quantity."
    )
    assert isinstance(result, Quantity)
    assert result.value == 12

checks = {
    "Tools": check_tools,
    "Streaming": check_streaming,
    "Structured output": check_structured_output,
}
all_passed = True
for name, check in checks.items():
    try:
        check()
    except (NotImplementedError, AssertionError) as error:
        print(f"{name}: FAIL ({type(error).__name__})")
        all_passed = False
    else:
        print(f"{name}: PASS")

print("All capability checks passed:", all_passed)
```

Expected output:

```text
Basic text: READY
Tools: FAIL (NotImplementedError)
Streaming: PASS
Structured output: FAIL (NotImplementedError)
All capability checks passed: False
```

Each check exercises a behavior, not just the existence of a method. `NotImplementedError` means this test model does not implement that feature. For an actual replacement, run equivalent checks with the real candidate and baseline, then compare representative task quality, latency, and failure handling. This small example checks chunk shape and nonempty streamed text, not first-token latency or production quality.

### 52. Keep a tool summary and chart data in different fields (Medium)

*Source: LangChain-M-H-Set2, Q20.*

A tool produces a short revenue summary for the model and detailed rows for a chart in your application. The model needs the summary; the application needs the original rows. Which `ToolMessage` layout fits this requirement?

- **A.** Put the summary in `content` and the chart data in `artifact`.
- **B.** Put everything in `content` and add a comment saying “chart data is UI-only.”
- **C.** Put everything in `artifact` and expect the model to read the summary automatically.
- **D.** Delete the rows and ask the model to recreate them later from the summary.

**Answer: A — `content` is the model-facing result; `artifact` holds additional application data.**

B still places the rows in the model-facing content. C leaves the model without the summary in its message content. D throws away exact data that the application already has.

**Runnable example — offline.** The tool below calculates a summary from real in-memory rows. `response_format="content_and_artifact"` means the function returns a pair: `(content, artifact)`.

```python
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

revenue_by_company = {
    "Acme": [
        {"month": "January", "revenue": 100},
        {"month": "February", "revenue": 120},
        {"month": "March", "revenue": 130},
    ]
}

@tool(response_format="content_and_artifact")
def get_revenue_summary(company: str):
    """Return a revenue summary and the underlying chart rows."""
    rows = revenue_by_company[company]
    total = sum(row["revenue"] for row in rows)
    summary = f"{company}'s total revenue was {total}."
    chart_data = {"company": company, "rows": rows}
    return summary, chart_data

# A complete ToolCall supplies the ID needed for a ToolMessage result.
tool_call = {
    "type": "tool_call",
    "id": "call_1",
    "name": "get_revenue_summary",
    "args": {"company": "Acme"},
}
result = get_revenue_summary.invoke(tool_call)

assert isinstance(result, ToolMessage)
print("Model content:", result.content)
print("Chart rows:", result.artifact["rows"])
print("Matched call:", result.tool_call_id)
```

Expected output:

```text
Model content: Acme's total revenue was 350.
Chart rows: [{'month': 'January', 'revenue': 100}, {'month': 'February', 'revenue': 120}, {'month': 'March', 'revenue': 130}]
Matched call: call_1
```

**Three lines to understand:** the decorator declares the two-part return format; `return summary, chart_data` supplies those two parts; `.invoke(tool_call)` returns a `ToolMessage` linked to that call. Application code can read `result.artifact`; the artifact is not automatically included as model-facing message content.

## Sources

Questions were selected from these supplied question sets and checked against their accompanying answer keys:

- **Set 3:** `LangChain-E-M-Set3-Questions.pdf` and `LangChain-E-M-Set3-Answers.pdf` — 20 retained.
- **Set 1:** `LangChain-M-Set1-Questions.pdf` and `LangChain-M-Set1-Answers.pdf` — 20 retained.
- **Set 2:** `LangChain-M-H-Set2-Questions.pdf` and `LangChain-M-H-Set2-Answers.pdf` — 12 retained.

Official references used to check API behavior:

- [Models and tool calling](https://docs.langchain.com/oss/python/langchain/models)
- [Messages and tool artifacts](https://docs.langchain.com/oss/python/langchain/messages)
- [Agent structured output and ToolStrategy](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Tool definitions and argument schemas](https://docs.langchain.com/oss/python/langchain/tools)
- [Runnable composition, batching, streaming, and fallbacks](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/base.py)
- [Passthrough and assign implementation](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/runnables/passthrough.py)
- [Chat prompts and message placeholders](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/prompts/chat.py)
- [In-memory vector store and MMR](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/vectorstores/in_memory.py)
- [Document loaders](https://reference.langchain.com/python/langchain-core/document_loaders/base/BaseLoader)
- [Recursive text splitting](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)
- [Pydantic validation](https://docs.pydantic.dev/latest/concepts/models/)
- [Async Python and thread offloading](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)
