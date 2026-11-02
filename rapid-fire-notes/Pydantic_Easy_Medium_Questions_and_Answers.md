# Pydantic: Easy–Medium Questions and Answers

60 questions for FDE / Applied AI coding interview practice. Answers appear directly below the choices, followed by a complete runnable example, its observed output, and a plain explanation of the data flow.

## Scope and verification

Reviewed every question and answer-key entry in all six supplied PDFs:

- Set 1: `Python-Pydantic-M-Set1-Questions.pdf` and `Python-Pydantic-M-Set1-Answers.pdf`.
- Set 2: `Python-Pydantic-M-H-Set2-Questions.pdf` and `Python-Pydantic-M-H-Set2-Answers.pdf`.
- Set 3: `Pydantic-E-M-Set3-Questions.pdf` and `Pydantic-E-M-Set3-Answers.pdf`.

All 60 questions were retained after judging the difficulty of what each question actually asks. Even the questions in the original Medium–Hard set test a focused Easy–Medium concept under explicit assumptions. No question required a Hard treatment, and no original answer-key letter needed correction. Each heading preserves its original set and question number and states its assessed difficulty.

The original Python fundamentals and concurrency questions in Sets 1 and 2 are included alongside Pydantic. No additional question topics were introduced. Ambiguous stems, missing helpers, unstated writer behavior, and unclear input/output types have been clarified.

**Verification:** All 60 Python examples were run independently as saved files in fresh Python processes and their standard output was compared with the output shown below. Expected failures are caught explicitly. Tested with **Python 3.12.14** and **Pydantic 2.14.1** on November 1, 2026. API contracts were also checked against official Python and Pydantic documentation.

Install the tested Pydantic version once:

```bash
python -m pip install "pydantic==2.14.1"
```

Copy each Python block into its own `.py` file and run it independently. Every block contains its own imports, models, helper functions, setup, and sample data; Python-only examples need no Pydantic imports. Async examples use `asyncio.run(...)` as their entry point. The process-pool example includes the main guard needed when running its saved file.

No API keys or external services are needed. Evidence, SDK writes, connection release, worker-capacity arithmetic, and deployment events are simulated where stated. Real local validation, asyncio control flow, file handling, and the process pool were executed; no production rollout, remote transaction, fleet-wide limit, or multicore speedup was tested. Each example explains its own limits.

For practice, predict the value **and its Python type** before reading the output. Follow what enters a function or validator, what it returns, and what the next step receives.

---

## Set 1 - Q01: A list default is shared across calls (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `01`.

A function is defined once as `collect(doc_id, ids=[])`. Its body calls `ids.append(doc_id)` and returns `ids`. In the same process, you print `collect("A")`, then print `collect("B")`, without supplying `ids` either time. Every omitted argument should start a fresh list. What does the **second** print show, and which change fixes that behavior?

A. `['B']`; keep the existing default because it creates a list on each call.

B. `['A', 'B']`; use `ids=None` and create a list inside the function when `ids is None`.

C. `['A', 'B']`; keep the list default and return a copy of it.

D. `['A']`; replace `append(doc_id)` with `extend([doc_id])`.

**Answer: B.**

**Why it works:** The list in the function signature is created when Python defines the function, not whenever you call it. Both omitted arguments use that same list. A `None` default lets the body create a fresh list for each omitted argument.

**Why the other choices fail:**

- **A:** The original default is reused, so the second call still sees A.
- **C:** Copying the result does not reset the original default list, which the next call still mutates.
- **D:** Both append and extend mutate that same list; the second call adds B rather than removing it.

**Standalone example — tested locally; no API key required.**

```python
def collect(doc_id, ids=[]):
    ids.append(doc_id)
    return ids


def collect_fixed(doc_id, ids=None):
    if ids is None:
        ids = []
    ids.append(doc_id)
    return ids


print("original first:", collect("A"))
print("original second:", collect("B"))
print("original shared default:", collect.__defaults__[0])
print("fixed first:", collect_fixed("A"))
print("fixed second:", collect_fixed("B"))
```

**Expected output — observed locally:**

```text
original first: ['A']
original second: ['A', 'B']
original shared default: ['A', 'B']
fixed first: ['A']
fixed second: ['B']
```

**Follow the key lines slowly:**

1. Python creates the original `[]` when it executes the `def` statement. `collect.__defaults__[0]` lets this example inspect that actual default object.
2. The first call appends A. The second appends B to the same list, so its result is `["A", "B"]`.
3. In `collect_fixed`, `if ids is None` checks specifically whether a list was omitted. It also preserves an explicitly supplied empty list rather than replacing it just because it is false-like.
4. `ids = []` runs inside each omitted-argument call. The fixed calls therefore return `["A"]` and `["B"]` independently.


---

## Set 1 - Q02: A dictionary copy still shares its nested list (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `02`.

Start with `template = {"tags": ["base"]}`. Set `request = template.copy()`, then run `request["tags"].append("urgent")`. What does `print(template["tags"])` show, and what is the smallest extra copy that isolates the tags in this exact dictionary-with-one-list structure?

A. `['base', 'urgent']`; replace `template.copy()` with `dict(template)` only.

B. `['base']`; `dict.copy()` already isolates the nested list.

C. `['base', 'urgent']`; copy the nested list with `request['tags'] = template['tags'].copy()` before appending.

D. `['base']`; replace append with `request['tags'] += ['urgent']`.

**Answer: C.**

**Why it works:** The outer dictionaries are separate, but the shallow copy initially stores a reference to the same tags list. Copying that one list is enough for this stated structure.

**Why the other choices fail:**

- **A:** `dict(template)` is another shallow copy; it still shares the nested list.
- **B:** A shallow dictionary copy does not copy objects stored inside it.
- **D:** List `+=` mutates the shared list here, so the template changes too.

**Standalone example — tested locally; no API key required.**

```python
template = {"tags": ["base"]}
request = template.copy()
print("different dictionaries:", request is not template)
print("same nested list:", request["tags"] is template["tags"])
request["tags"].append("urgent")
print("original template tags:", template["tags"])

# Start fresh so the corrected version is easy to compare.
template = {"tags": ["base"]}
request = template.copy()
request["tags"] = template["tags"].copy()
print("same nested list after fix:", request["tags"] is template["tags"])
request["tags"].append("urgent")
print("fixed template tags:", template["tags"])
print("fixed request tags:", request["tags"])
```

**Expected output — observed locally:**

```text
different dictionaries: True
same nested list: True
original template tags: ['base', 'urgent']
same nested list after fix: False
fixed template tags: ['base']
fixed request tags: ['base', 'urgent']
```

**Follow the key lines slowly:**

1. `template.copy()` creates a new outer dictionary. The first `True` confirms that those dictionary objects differ.
2. Both `tags` entries still point to one list, which the second `True` makes visible. Appending through either dictionary changes that list.
3. The corrected example starts with a fresh template, then replaces only the request's `tags` entry with a copied list.
4. The final lists differ: the template keeps `["base"]`; the request contains `["base", "urgent"]`. This one nested copy is sufficient only because the question specifies this simple structure.


---

## Set 1 - Q03: A dict.get fallback is evaluated before the lookup (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `03`.

The cache is `{"q": 7}` and the key is `"q"`. `fetch()` prints `fetch` and returns `9`. You evaluate `print(cache.get(key, fetch()))`. What is printed, and which replacement avoids fetching on a cache hit while also preserving a cached `None` value?

A. `fetch`, then `7`; use `cache[key] if key in cache else fetch()`.

B. Only `7`; `dict.get` evaluates its default only after a miss.

C. `fetch`, then `7`; use `cache.get(key) or fetch()`.

D. `fetch`, then `9`; evaluating the fallback overwrites the cache.

**Answer: A.**

**Why it works:** Python evaluates `fetch()` before calling `get`, even when the key exists. A conditional expression evaluates only its selected branch, and checking membership distinguishes a present `None` from a missing key.

**Why the other choices fail:**

- **B:** `get` receives an already computed default value, not a deferred function call.
- **C:** `None` is false-like, so `or fetch()` would replace that valid cached value.
- **D:** Computing the default neither changes the dictionary nor makes `get` ignore a present key.

**Standalone example — tested locally; no API key required.**

```python
cache = {"q": 7, "nullable": None}


def fetch():
    print("fetch")
    return 9


key = "q"
print("original expression:")
print(cache.get(key, fetch()))
print("cache after original:", cache)

print("corrected lookups:")
for key in ["q", "nullable", "missing"]:
    value = cache[key] if key in cache else fetch()
    print(key, "->", value)
```

**Expected output — observed locally:**

```text
original expression:
fetch
7
cache after original: {'q': 7, 'nullable': None}
corrected lookups:
q -> 7
nullable -> None
fetch
missing -> 9
```

**Follow the key lines slowly:**

1. When Python reaches `cache.get(key, fetch())`, it evaluates the arguments first. That is why `fetch` appears before `7`.
2. The cache still holds `7` for q and `None` for nullable; the original expression never assigns into it.
3. For q, the membership check is true and the expression reads `cache[key]`. For nullable it also reads the cache, preserving `None`.
4. Only missing selects the `else fetch()` branch. Its fetch output appears immediately before `missing -> 9`.


---

## Set 1 - Q04: A generator is consumed by validation (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `04`.

A small in-memory batch creates `rows = ({"id": i} for i in [1, 2, 3])`. All IDs are positive. It then runs `assert all(row["id"] > 0 for row in rows)` and calls `persist(list(rows))`. `persist` stores exactly the records it receives. What does it receive, and which fix preserves both complete validation and those same records? Assume assertions are enabled for the original code.

A. An empty list; call `iter(rows)` before persisting to restart it.

B. All three rows; `all()` checks generators without consuming them.

C. Only the last row; `all()` leaves its final successful item available.

D. An empty list; materialize the generator once, then validate and persist that list.

**Answer: D.**

**Why it works:** Because all checks pass, `all` consumes this one-shot generator to exhaustion. A list created first can be iterated again for validation and persistence.

**Why the other choices fail:**

- **A:** Calling `iter` on this generator returns the same exhausted iterator, not a fresh data source.
- **B:** `all` must obtain each item from the generator to check it.
- **C:** The final successful item was consumed too; it is not put back.

**Standalone example — tested locally; no API key required.**

```python
def persist(records):
    # Simulated persistence: display the exact batch instead of writing a database.
    print("persist receives:", records)


rows = ({"id": i} for i in [1, 2, 3])
valid = all(row["id"] > 0 for row in rows)
print("original validation:", valid)
persist(list(rows))

# Materialize once, before validation.
rows = list({"id": i} for i in [1, 2, 3])
print("materialized rows:", rows)
valid = all(row["id"] > 0 for row in rows)
print("fixed validation:", valid)
if not valid:
    raise ValueError("Every ID must be positive")
persist(rows)
```

**Expected output — observed locally:**

```text
original validation: True
persist receives: []
materialized rows: [{'id': 1}, {'id': 2}, {'id': 3}]
fixed validation: True
persist receives: [{'id': 1}, {'id': 2}, {'id': 3}]
```

**Follow the key lines slowly:**

1. The first `rows` is a generator. It produces each dictionary only as validation asks for it.
2. Every check succeeds, so `all(...)` requests all three rows and exhausts the generator. Converting it to a list afterward gives `[]`.
3. The fixed `list(...)` stores the three dictionaries before validation. Iterating over this list does not destroy its contents.
4. The explicit `if not valid` rejects a bad batch before persistence. This avoids relying on an assertion as application validation; for the stated valid inputs, the same three rows reach the simulated persistence function.


---

## Set 1 - Q05: Callbacks look up a shared loop binding later (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `05`.

Three callbacks are created in a loop over `["A", "B", "C"]`. Each is registered with `callbacks.append(lambda: name)`. They are called only after the loop ends using `[fn() for fn in callbacks]`. What list results, and which edit makes each callback retain its own partition name?

A. `['C', 'C', 'C']`; register `lambda name=name: name`.

B. `['A', 'B', 'C']`; the existing lambdas capture each value automatically.

C. `['A', 'A', 'A']`; reverse the source names before registration.

D. `['C', 'C', 'C']`; rename the loop variable from `name` to `partition`.

**Answer: A.**

**Why it works:** The original lambdas look up the same binding when called. The loop has left that binding equal to C. A lambda default is evaluated at creation time, so each fixed callback retains its iteration's string.

**Why the other choices fail:**

- **B:** These callbacks do not automatically take a snapshot of each loop value.
- **C:** The original result contains C, and reversing the loop would merely change the shared final value.
- **D:** Renaming the variable leaves the same late-lookup behavior.

**Standalone example — tested locally; no API key required.**

```python
callbacks = []
for name in ["A", "B", "C"]:
    callbacks.append(lambda: name)

print("name after loop:", name)
print("original callbacks:", [fn() for fn in callbacks])

fixed_callbacks = []
for name in ["A", "B", "C"]:
    fixed_callbacks.append(lambda name=name: name)

print("captured defaults:", [fn.__defaults__[0] for fn in fixed_callbacks])
print("fixed callbacks:", [fn() for fn in fixed_callbacks])
```

**Expected output — observed locally:**

```text
name after loop: C
original callbacks: ['C', 'C', 'C']
captured defaults: ['A', 'B', 'C']
fixed callbacks: ['A', 'B', 'C']
```

**Follow the key lines slowly:**

1. Creating a lambda does not call it. The three original functions execute only after the loop has finished.
2. At that time the shared loop name is C, so every original callback returns C.
3. In `lambda name=name: name`, the expression on the right of `=` is evaluated while that lambda is created. Its value becomes that function's default parameter.
4. The displayed defaults are A, B, and C. Calling each fixed function without arguments uses its own default, giving the intended list.


---

## Set 1 - Q06: Force strict pairing to finish before writes start (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `06`.

`ids=["d1", "d2", "d3"]`, but the embedding response contains only `vectors=[[0.1], [0.2]]`. The next line is `write(pairs)`. This writer accepts any iterable and writes each pair as soon as it receives it; it does not validate the whole batch first. The request must fail **before `write` is called** when counts differ. Which assignment to `pairs` guarantees that for these finite lists?

A. `pairs = zip(ids, vectors, strict=True)`

B. `pairs = list(zip(ids, vectors))`

C. `pairs = list(zip(ids, vectors, strict=True))`

D. `pairs = list(zip(ids[:len(vectors)], vectors))`

**Answer: C.**

**Why it works:** `strict=True` detects unequal lengths when the zip iterator is consumed. Wrapping it in `list` consumes the whole iterator during the assignment, so the mismatch raises before execution can call the writer.

**Why the other choices fail:**

- **A:** Creating a strict zip is lazy. The writer could write earlier pairs before consuming enough items to discover the mismatch.
- **B:** Ordinary zip silently stops at the shorter input and loses the third ID.
- **D:** Slicing hides the missing vector by discarding an ID instead of rejecting the batch.

**Standalone example — tested locally; no API key required.**

```python
ids = ["d1", "d2", "d3"]
vectors = [[0.1], [0.2]]
writes = []


def write(pairs):
    # Simulated database writes: each pair is recorded immediately.
    for pair in pairs:
        writes.append(pair)


print("input counts:", len(ids), len(vectors))
print("ordinary zip:", list(zip(ids, vectors)))

# Lazy strict pairing detects the mismatch only while write consumes it.
try:
    pairs = zip(ids, vectors, strict=True)
    write(pairs)
except ValueError:
    print("lazy strict error:", "ValueError")
print("writes before lazy failure:", writes)

writes.clear()
# Eager strict pairing must complete before the writer can be called.
try:
    pairs = list(zip(ids, vectors, strict=True))
    write(pairs)
except ValueError:
    print("eager strict error:", "ValueError")
print("writes after eager validation:", writes)
```

**Expected output — observed locally:**

```text
input counts: 3 2
ordinary zip: [('d1', [0.1]), ('d2', [0.2])]
lazy strict error: ValueError
writes before lazy failure: [('d1', [0.1]), ('d2', [0.2])]
eager strict error: ValueError
writes after eager validation: []
```

**Follow the key lines slowly:**

1. The input counts, 3 and 2, show the incomplete response before any pairing.
2. Ordinary zip produces two pairs without raising. That is silent truncation, not a successful complete batch.
3. The lazy strict zip raises only when the writer requests the missing third pair. The simulated writer has already recorded two pairs by then.
4. In the corrected version, `list(...)` consumes strict zip before the assignment succeeds. Its `ValueError` skips the following `write(pairs)` line.
5. The final empty writes list confirms that eager validation prevented all simulated database writes. No database service is contacted.


---

## Set 1 - Q07: TypedDict does not validate an incoming dictionary (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `07`.

A webhook produces the plain empty dictionary `{}`. The code defines `class Request(TypedDict)` with required field `query: str`, assigns `payload: Request = {}`, then evaluates `payload["query"]`. Run this code directly, without a static type checker enforcing annotations. What happens, and where should required-field validation occur?

A. The annotation inserts an empty string; check only whether that string is nonempty later.

B. The assignment raises a runtime typing-validation error.

C. The access returns `None`; treat the field as optional downstream.

D. The access raises `KeyError`; validate the payload at the runtime boundary before required-field access.

**Answer: D.**

**Why it works:** `TypedDict` describes an expected dictionary shape for static analysis. It does not alter this empty dictionary or intercept the assignment at runtime. Accessing its missing key raises `KeyError`.

**Why the other choices fail:**

- **A:** An annotation does not insert missing dictionary values.
- **B:** A static checker can flag this assignment, but Python does not perform that shape validation while running it.
- **C:** Dictionary subscription raises for a missing key; it is not the same as `payload.get("query")`.

**Standalone example — tested locally; no API key required.**

```python
from typing import TypedDict
from pydantic import BaseModel, ValidationError


class Request(TypedDict):
    query: str


# Intentionally violates the static annotation to show runtime behavior.
payload: Request = {}
print("raw payload:", payload)
try:
    print(payload["query"])
except KeyError as error:
    print("raw access error:", type(error).__name__, error.args[0])


class ValidatedRequest(BaseModel):
    query: str


try:
    ValidatedRequest.model_validate(payload)
except ValidationError as error:
    detail = error.errors()[0]
    print("boundary error location:", detail["loc"])
    print("boundary error type:", detail["type"])

valid = ValidatedRequest.model_validate({"query": "Revenue?"})
print("validated query:", valid.query)
```

**Expected output — observed locally:**

```text
raw payload: {}
raw access error: KeyError query
boundary error location: ('query',)
boundary error type: missing
validated query: Revenue?
```

**Follow the key lines slowly:**

1. At runtime, `payload` is still the plain empty dictionary printed on the first line. The `Request` annotation did not populate it.
2. `payload["query"]` asks for a required key using dictionary subscription, which raises `KeyError` because that key is absent.
3. `ValidatedRequest.model_validate(payload)` is a real Pydantic runtime check. It rejects the missing field before the application reads `valid.query`.
4. The error location identifies query and the type is `missing`. Supplying a real query succeeds and creates a model whose validated query is available as an attribute.


---

## Set 1 - Q08: A return in finally can suppress a failure (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `08`.

`send()` always raises `ConnectionError`. The function `submit()` runs `send()` in a `try` block, followed by `return "ok"`; its `finally` block executes `return "done"`. What does the caller observe, and which change preserves the original exception while still allowing cleanup?

A. `ConnectionError`; `finally` cannot affect an exception that is propagating.

B. The string `"done"`; remove the return from `finally` and perform cleanup there.

C. The string `"ok"`; that return executes before the failure.

D. `ConnectionError`; move `return "done"` into an exception handler to preserve it.

**Answer: B.**

**Why it works:** The `finally` block runs while Python is leaving the `try`. Returning there replaces the pending exception with a normal result. Cleanup without a return allows the original exception to continue to the caller.

**Why the other choices fail:**

- **A:** A return in finally can suppress a pending exception.
- **C:** `send()` raises before execution reaches `return "ok"`.
- **D:** Returning from an exception handler handles the error and returns normally; it does not propagate that exception.

**Standalone example — tested locally; no API key required.**

```python
def send():
    # Simulated failing send: no network request is made.
    raise ConnectionError("Simulated connection failure")


def submit():
    try:
        send()
        return "ok"
    finally:
        return "done"  # Intentional bug: suppresses the send failure.


def cleanup():
    print("cleanup ran")


def submit_fixed():
    try:
        send()
        return "ok"
    finally:
        cleanup()  # No return here: preserve the pending exception.


print("original caller receives:", submit())
try:
    submit_fixed()
except ConnectionError as error:
    print("fixed caller receives:", type(error).__name__)
    print("failure message:", str(error))
```

**Expected output — observed locally:**

```text
original caller receives: done
cleanup ran
fixed caller receives: ConnectionError
failure message: Simulated connection failure
```

**Follow the key lines slowly:**

1. The local `send` helper always raises the stated exception. It is simulated and performs no network operation.
2. The original function jumps to finally before it can return ok. Its return done suppresses that pending failure.
3. The corrected finally block calls `cleanup()` and falls through without returning.
4. The output shows cleanup before the caught `ConnectionError`. The caller can now observe the actual failure as well as receive the cleanup behavior.


---

## Set 1 - Q09: Raise a service exception with an explicit cause (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `09`.

A local retrieval helper raises `TimeoutError`. The service boundary must raise `RetrievalUnavailable("search failed")` to its caller and retain the original timeout as the **explicit cause**, available through `__cause__`. Which exception-handler body meets both requirements? Assume `RetrievalUnavailable` is a normal subclass of `Exception`.

A. `except TimeoutError as exc: raise exc`

B. `except TimeoutError as exc: raise RetrievalUnavailable("search failed") from None`

C. `except TimeoutError as exc: return RetrievalUnavailable("search failed")`

D. `except TimeoutError as exc: raise RetrievalUnavailable("search failed") from exc`

**Answer: D.**

**Why it works:** `raise ... from exc` raises the requested service exception and links the original timeout as its explicit cause. The caller gets a stable service-facing type while diagnostics retain the underlying failure.

**Why the other choices fail:**

- **A:** This raises TimeoutError rather than translating to the required service type.
- **B:** `from None` does not attach the timeout as the requested explicit cause.
- **C:** Returning an exception object is an ordinary return, not an exception raised to the caller.

**Standalone example — tested locally; no API key required.**

```python
class RetrievalUnavailable(Exception):
    pass


def retrieve():
    # Simulated timeout; no retrieval service is contacted.
    raise TimeoutError("Simulated search deadline expired")


def service_search():
    try:
        retrieve()
    except TimeoutError as exc:
        raise RetrievalUnavailable("search failed") from exc


try:
    service_search()
except RetrievalUnavailable as error:
    print("caller exception:", type(error).__name__)
    print("caller message:", str(error))
    print("explicit cause:", type(error.__cause__).__name__)
    print("cause message:", str(error.__cause__))
```

**Expected output — observed locally:**

```text
caller exception: RetrievalUnavailable
caller message: search failed
explicit cause: TimeoutError
cause message: Simulated search deadline expired
```

**Follow the key lines slowly:**

1. `retrieve()` raises a locally simulated `TimeoutError`, representing the lower-level failure.
2. The service catches that specific timeout as `exc` and constructs a different exception for its public boundary.
3. `from exc` attaches that exact original exception as `error.__cause__`; it does not replace or erase its message.
4. The caller catches `RetrievalUnavailable`. The four printed values show both the public type/message and the retained diagnostic type/message.


---

## Set 1 - Q10: Keep a file open while its lazy reader is active (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `10`.

A function `lines(path)` opens an existing text file in a `with open(path) as f` block and returns the generator expression `(line.strip() for line in f)` from inside that block. The caller waits until `lines()` has returned before calling `next()` on its result. What is the defect, and which change preserves lazy reading?

A. No defect; a generator expression automatically keeps the context manager open.

B. Iteration uses a closed file; make `lines` a generator that yields stripped lines inside the with block.

C. The file stays open forever; explicitly close it immediately before returning the expression.

D. Iteration starts at EOF; seek to position zero immediately before returning the expression.

**Answer: B.**

**Why it works:** Returning leaves the with block and closes the file before the generator expression reads it. Yielding from inside the function's with block keeps that block active while the function generator is being consumed.

**Why the other choices fail:**

- **A:** A reference to the file object does not prevent the context manager from closing it.
- **C:** The original with block already closes the file; closing it earlier does not fix later reading.
- **D:** Moving the file cursor does not make a closed file readable.

**Standalone example — tested locally; no API key required.**

```python
from pathlib import Path
from tempfile import TemporaryDirectory


def lines(path):
    with open(path, encoding="utf-8") as file:
        return (line.strip() for line in file)


def lines_fixed(path):
    with open(path, encoding="utf-8") as file:
        print("file open inside generator:", not file.closed)
        for line in file:
            yield line.strip()
    print("file closed after full consumption:", file.closed)


with TemporaryDirectory() as folder:
    path = Path(folder) / "evidence.txt"
    path.write_text("  alpha  \n  beta  \n", encoding="utf-8")
    broken = lines(path)
    print("original function has returned")
    try:
        next(broken)
    except ValueError as error:
        print("original iteration error:", type(error).__name__)

    result = lines_fixed(path)
    print("fixed generator created; body has not run yet")
    print("first line:", next(result))
    print("remaining lines:", list(result))
```

**Expected output — observed locally:**

```text
original function has returned
original iteration error: ValueError
fixed generator created; body has not run yet
file open inside generator: True
first line: alpha
file closed after full consumption: True
remaining lines: ['beta']
```

**Follow the key lines slowly:**

1. The example writes a real temporary two-line file, so the path and sample data are included. The surrounding temporary directory is cleaned up automatically.
2. The original `return` exits its with block. The caller then tries to read from the closed file and catches `ValueError`.
3. Calling `lines_fixed(path)` creates a generator without running its body. The next output confirms that opening starts only when the caller asks for a line.
4. The first `next(result)` enters the with block and yields alpha. The function is suspended inside that block, so the file remains open.
5. `list(result)` consumes beta and then finishes the loop. Only then does execution leave with and close the file, as the printed `True` shows. If a caller stops early instead, it should explicitly close that generator to ensure timely cleanup.

---

## Set 1 - Q11: Require a key while allowing null (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `11`.

A response must contain a `reason` key, but its value may be a string or JSON `null`. The model declares `reason: str | None` with **no default**. Under Pydantic 2 defaults, what happens for `Result()` and `Result(reason=None)`?

A. `Result()` fails; `Result(reason=None)` succeeds. This matches the contract.

B. Both succeed because `str | None` automatically supplies a `None` default.

C. Both fail because model fields cannot use a union containing `None`.

D. Only `Result()` succeeds because explicit `None` counts as a missing value.

**Answer: A.**

**Why it works:** The annotation allows `None` as a value, but does not supply a value when the key is missing. Presence and nullability are separate decisions.

**Why the other choices fail:**

- **B:** A nullable annotation does not create a default in Pydantic 2.
- **C:** Pydantic supports nullable unions such as `str | None`.
- **D:** An explicitly supplied `None` is an allowed value; it is not an omitted key.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError

class Result(BaseModel):
    reason: str | None

try:
    Result()
except ValidationError as error:
    first = error.errors()[0]
    print("Omitted key:", first["loc"], first["type"])

result = Result(reason=None)
print("Explicit value:", result.reason)
print("Serialized JSON:", result.model_dump_json())
```

**Expected output — captured from the local run:**

```text
Omitted key: ('reason',) missing
Explicit value: None
Serialized JSON: {"reason":null}
```

**Follow the key lines:**

1. `reason: str | None` permits either a string or `None`. There is no `= ...` default after the annotation.
2. The first constructor supplies no key. Validation reports `loc=('reason',)` and error type `missing`.
3. The second constructor supplies the key with value `None`, so validation succeeds.
4. `model_dump_json()` writes Python `None` as JSON `null`, while retaining the required key.


---

## Set 1 - Q12: Accept an integer without accepting a boolean (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `12`.

A model declares `retries: StrictInt`. The tool contract accepts the integer `3`, but must reject the string `"3"` and the boolean `True`. Which inputs pass validation?

A. `3` and `True`.

B. `3` and `"3"`.

C. Only `3`.

D. All three inputs.

**Answer: C.**

**Why it works:** `StrictInt` accepts the integer and rejects coercion from the string. It also rejects booleans even though Python considers `bool` a subclass of `int`.

**Why the other choices fail:**

- **A:** `StrictInt` deliberately rejects `True`; it is not interpreted as the integer `1`.
- **B:** The numeric string is rejected rather than converted to an integer.
- **D:** Both the string and the boolean violate this strict field contract.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, StrictInt, ValidationError

class RunConfig(BaseModel):
    retries: StrictInt

for value in [3, "3", True]:
    print("Input:", repr(value), "type:", type(value).__name__)
    try:
        config = RunConfig(retries=value)
        print("Accepted:", config.retries, type(config.retries).__name__)
    except ValidationError as error:
        first = error.errors()[0]
        print("Rejected:", first["loc"], first["type"])
```

**Expected output — captured from the local run:**

```text
Input: 3 type: int
Accepted: 3 int
Input: '3' type: str
Rejected: ('retries',) int_type
Input: True type: bool
Rejected: ('retries',) int_type
```

**Follow the key lines:**

1. The sample list contains three different Python values: an `int`, a `str`, and a `bool`.
2. `RunConfig(retries=value)` runs validation separately for each value.
3. The accepted object stores the integer `3`. The other two calls report `int_type` errors at `retries`.
4. This behavior follows the strict Pydantic field rule; ordinary Python subclass relationships do not make `True` valid here.


---

## Set 1 - Q13: Validate an invalid default (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `13`.

A model declares `budget: int = Field(default=-1, gt=0)`. Calling `Limits()` currently succeeds and stores `-1`. You must keep the requirement `budget > 0` and make that invalid default fail. Which smallest field change does this?

A. Replace `gt=0` with `ge=0`, making no other change.

B. Add `strict=True` only.

C. Add `validate_default=True`.

D. Use `Limits.model_construct()` instead of `Limits()`.

**Answer: C.**

**Why it works:** Defaults are not validated by default. `validate_default=True` sends the default through the field validation rules, where `-1` violates `gt=0`.

**Why the other choices fail:**

- **A:** This does not enable default validation and also changes the positive-only constraint.
- **B:** `-1` already has integer type. Strictness alone does not enable validation of defaults.
- **D:** `model_construct()` bypasses validation rather than enforcing the constraint.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field, ValidationError

class OriginalLimits(BaseModel):
    budget: int = Field(default=-1, gt=0)

class Limits(BaseModel):
    budget: int = Field(default=-1, gt=0, validate_default=True)

print("Original default:", OriginalLimits().budget)
try:
    Limits()
except ValidationError as error:
    first = error.errors()[0]
    print("Validated default:", first["loc"], first["type"])
    print("Rejected value:", first["input"])

print("Explicit positive value:", Limits(budget=5).budget)
```

**Expected output — captured from the local run:**

```text
Original default: -1
Validated default: ('budget',) greater_than
Rejected value: -1
Explicit positive value: 5
```

**Follow the key lines:**

1. `OriginalLimits()` demonstrates the starting behavior: the unvalidated default remains `-1`.
2. The corrected field keeps `gt=0` and adds `validate_default=True`.
3. Constructing `Limits()` now validates `-1` and reports `greater_than` at `budget`.
4. An explicit valid input, `budget=5`, still succeeds. Default validation adds a check; it does not remove the original constraint.


---

## Set 1 - Q14: Reject a misspelled input field (Easy)

**Original reference:** `Python-Pydantic-M-Set1`, question `14`.

A model declares `max_retries: int = 3` with default Pydantic configuration. Input `{"max_retires": 0}` uses a misspelled key, so the ordinary model ignores it and keeps `max_retries=3`. The service should reject unknown request keys. Which configuration enforces that policy?

A. `model_config = ConfigDict(extra="allow")`.

B. `model_config = ConfigDict(extra="forbid")`.

C. `model_config = ConfigDict(strict=True)` only.

D. Make `max_retries` nullable while keeping its default.

**Answer: B.**

**Why it works:** `extra="forbid"` rejects input keys absent from the declared fields, so the typo becomes an error instead of silently disappearing.

**Why the other choices fail:**

- **A:** Allowing extras retains the misspelled key; it does not reject it or turn it into `max_retries`.
- **C:** Strictness changes accepted value types, not the default policy for unknown keys.
- **D:** Allowing `None` changes field values, not the treatment of misspelled keys.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class OriginalConfig(BaseModel):
    max_retries: int = 3

class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_retries: int = 3

bad_input = {"max_retires": 0}
print("Input:", bad_input)
print("Default extra policy:", OriginalConfig.model_validate(bad_input).model_dump())
try:
    RunConfig.model_validate(bad_input)
except ValidationError as error:
    first = error.errors()[0]
    print("Forbid policy:", first["loc"], first["type"])

good_input = {"max_retries": 0}
print("Correct key:", RunConfig.model_validate(good_input).model_dump())
```

**Expected output — captured from the local run:**

```text
Input: {'max_retires': 0}
Default extra policy: {'max_retries': 3}
Forbid policy: ('max_retires',) extra_forbidden
Correct key: {'max_retries': 0}
```

**Follow the key lines:**

1. `bad_input` contains `max_retires`, while the declared field is `max_retries`.
2. The original model ignores that unknown key and uses its default value `3`.
3. `extra="forbid"` makes the same input fail with `extra_forbidden`, locating the actual misspelled key.
4. The correctly spelled key sets `max_retries` to `0`. This example tests key handling, not a separate positive-value constraint.


---

## Set 1 - Q15: Normalize shape before validating list items (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `15`.

A model declares `ids: list[int]`. Its `mode="before"` field validator returns the input unchanged if it is a list, otherwise wraps it as `[value]`. Normal Pydantic integer parsing then remains enabled. What happens for `Batch(ids="7")` and `Batch(ids=["7", "bad"])`?

A. The scalar becomes `[7]`; the mixed list fails integer-item validation.

B. The scalar becomes `["7"]`; a before validator disables later type validation.

C. The scalar becomes `[7]`; the mixed list silently drops `"bad"`.

D. The scalar fails because before validators run after list validation.

**Answer: A.**

**Why it works:** The before validator changes the input shape first. Pydantic then validates `list[int]`: `"7"` can become `7`, but `"bad"` cannot become an integer.

**Why the other choices fail:**

- **B:** A before validator returns input to the normal validation pipeline; it does not bypass item validation.
- **C:** The model rejects the invalid item instead of filtering it out.
- **D:** A before validator runs before the declared field type is parsed.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError, field_validator

class Batch(BaseModel):
    ids: list[int]

    @field_validator("ids", mode="before")
    @classmethod
    def as_list(cls, value):
        normalized = value if isinstance(value, list) else [value]
        print("Before validator:", repr(value), "->", normalized)
        return normalized

first = Batch(ids="7")
print("Stored IDs:", first.ids)
print("Stored item types:", [type(item).__name__ for item in first.ids])
try:
    Batch(ids=["7", "bad"])
except ValidationError as error:
    first_error = error.errors()[0]
    print("Mixed-list error:", first_error["loc"], first_error["type"])
    print("Invalid item:", repr(first_error["input"]))
```

**Expected output — captured from the local run:**

```text
Before validator: '7' -> ['7']
Stored IDs: [7]
Stored item types: ['int']
Before validator: ['7', 'bad'] -> ['7', 'bad']
Mixed-list error: ('ids', 1) int_parsing
Invalid item: 'bad'
```

**Follow the key lines:**

1. For the scalar input, the before validator prints `'7' -> ['7']`. It has changed the shape, not yet the item type.
2. `return normalized` passes that list to the declared `list[int]` validation. The stored value is `[7]`, with item type `int`.
3. For the mixed list, the validator returns both strings unchanged. Pydantic then attempts integer parsing for each item.
4. The error path `('ids', 1)` identifies the second list item. No partially accepted `Batch` is returned for that invalid input.


---

## Set 1 - Q16: Check a relationship after both fields are parsed (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `16`.

A `Window` has integer fields `start` and `end`, with the rule `end > start`. Inputs may be numeric strings. The relationship must be checked after both fields are parsed and must work regardless of which field is declared first. Which approach meets all requirements?

A. Set `gt=0` on `end`; positivity alone guarantees the relationship.

B. Use a before field validator on `end` to compare its raw input with `info.data["start"]`.

C. Reject invalid windows from an `end` serializer when `model_dump()` runs.

D. Use an after model validator that compares `self.end` and `self.start`, raises `ValueError` when invalid, and returns `self` when valid.

**Answer: D.**

**Why it works:** An after model validator sees the parsed model, including both integer fields. It can reject their invalid relationship before the model is used by application code.

**Why the other choices fail:**

- **A:** For example, `start=10` and `end=5` satisfy `end > 0` but violate `end > start`.
- **B:** The value is still raw and access to another field depends on field validation order.
- **C:** A serializer runs when producing output; it is too late to prevent an invalid model from entering business logic.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError, model_validator

class Window(BaseModel):
    # Deliberately declare end first to demonstrate order independence.
    end: int
    start: int

    @model_validator(mode="after")
    def check_order(self):
        print("Parsed fields:", self.start, self.end)
        print("Parsed types:", type(self.start).__name__, type(self.end).__name__)
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self

valid = Window(start="3", end="7")
print("Accepted window:", valid.model_dump())
try:
    Window(start="8", end="5")
except ValidationError as error:
    first = error.errors()[0]
    print("Invalid window:", first["loc"], first["type"])
```

**Expected output — captured from the local run:**

```text
Parsed fields: 3 7
Parsed types: int int
Accepted window: {'end': 7, 'start': 3}
Parsed fields: 8 5
Parsed types: int int
Invalid window: () value_error
```

**Follow the key lines:**

1. The declaration puts `end` before `start`; the check still reads both values from the complete parsed model.
2. `mode="after"` means `"3"` and `"7"` have become integers before `check_order` runs. The printed types show this.
3. The valid pair passes the comparison and returns `self`, allowing construction to finish.
4. For `start=8` and `end=5`, raising `ValueError` becomes a Pydantic `ValidationError`. The empty location tuple `()` means this rule concerns the model as a whole.


---

## Set 1 - Q17: Produce a JSON-ready dictionary (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `17`.

A model has `at: datetime` and `amount: Decimal`, holding `datetime(2026, 1, 1)` and `Decimal("12.50")`. An HTTP client expects a **dictionary of JSON-compatible values** and performs JSON encoding itself. No custom serializers or encoders are configured. Which expression supplies the required value?

A. `json.dumps(payload.model_dump())` with no custom encoder.

B. `payload.model_dump()`.

C. `payload.model_dump_json()`.

D. `payload.model_dump(mode="json")`.

**Answer: D.**

**Why it works:** JSON-mode dumping returns a dictionary and converts these values into JSON-compatible strings. It preserves the mapping shape the client needs.

**Why the other choices fail:**

- **A:** The standard JSON encoder cannot encode the Python `datetime` and `Decimal` values in the ordinary dump without extra handling.
- **B:** The default Python-mode dump retains Python `datetime` and `Decimal` objects.
- **C:** `model_dump_json()` returns already encoded JSON text, not the required dictionary.

**Standalone Python example — tested locally; no API key required.**

```python
import json
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class Payload(BaseModel):
    at: datetime
    amount: Decimal

payload = Payload(at=datetime(2026, 1, 1), amount=Decimal("12.50"))
python_values = payload.model_dump()
print("Python-mode types:", {key: type(value).__name__ for key, value in python_values.items()})

ready = payload.model_dump(mode="json")
print("JSON-ready dictionary:", ready)
print("JSON-ready types:", {key: type(value).__name__ for key, value in ready.items()})

# This is local encoding only, standing in for the client's encoding step.
encoded = json.dumps(ready, sort_keys=True)
print("Encoded body:", encoded)
print("model_dump_json return type:", type(payload.model_dump_json()).__name__)
```

**Expected output — captured from the local run:**

```text
Python-mode types: {'at': 'datetime', 'amount': 'Decimal'}
JSON-ready dictionary: {'at': '2026-01-01T00:00:00', 'amount': '12.50'}
JSON-ready types: {'at': 'str', 'amount': 'str'}
Encoded body: {"amount": "12.50", "at": "2026-01-01T00:00:00"}
model_dump_json return type: str
```

**Follow the key lines:**

1. The ordinary dump contains `datetime` and `Decimal` values. The first print shows their types without hiding them behind a JSON string.
2. `mode="json"` converts the date-time to an ISO-formatted string and the decimal to the string `"12.50"`.
3. `ready` is still a dictionary. The local `json.dumps` call demonstrates the encoding step an HTTP client would perform; no request is sent.
4. `model_dump_json()` produces a `str`. Supplying that text where a client expects a dictionary gives it the wrong input shape.


---

## Set 1 - Q18: Keep omitted and explicit-null PATCH values distinct (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `18`.

A PATCH model declares `note: str | None = None`. In the API contract, an omitted `note` means leave the stored note unchanged; an explicitly supplied `note=None` means clear it. Let `a = Patch()` and `b = Patch(note=None)`. Which dump option produces `{}` for `a` and `{"note": None}` for `b`?

A. `model_dump()` with no exclusion options.

B. `model_dump(exclude_none=True)`.

C. `model_dump(exclude_unset=True)`.

D. `model_dump(exclude_defaults=True)`.

**Answer: C.**

**Why it works:** `exclude_unset=True` uses whether a field was explicitly supplied. It omits the unsupplied field in `a` and retains the explicit clearing value in `b`.

**Why the other choices fail:**

- **A:** The ordinary dump includes `note=None` in both objects, losing the distinction.
- **B:** This removes `None` from both objects, losing the explicit request to clear the note.
- **D:** Both values equal the default, so both are excluded even when `None` was explicitly supplied.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel

class Patch(BaseModel):
    note: str | None = None

a = Patch()
b = Patch(note=None)
print("Stored values:", a.note, b.note)
print("Explicit fields a:", sorted(a.model_fields_set))
print("Explicit fields b:", sorted(b.model_fields_set))
print("Ordinary dumps:", a.model_dump(), b.model_dump())
print("exclude_none:", a.model_dump(exclude_none=True), b.model_dump(exclude_none=True))
print("exclude_unset:", a.model_dump(exclude_unset=True), b.model_dump(exclude_unset=True))
print("exclude_defaults:", a.model_dump(exclude_defaults=True), b.model_dump(exclude_defaults=True))
```

**Expected output — captured from the local run:**

```text
Stored values: None None
Explicit fields a: []
Explicit fields b: ['note']
Ordinary dumps: {'note': None} {'note': None}
exclude_none: {} {}
exclude_unset: {} {'note': None}
exclude_defaults: {} {}
```

**Follow the key lines:**

1. Both models store the same Python value, `None`. Looking only at `a.note` and `b.note` cannot reveal whether the client supplied the field.
2. `model_fields_set` records the explicitly supplied fields. It is empty for `a` and contains `note` for `b`.
3. `exclude_unset=True` preserves that presence information when creating the update dictionary.
4. The other three printed dump strategies show why value-based filtering does not express this PATCH contract. No stored record is modified in this local example.


---

## Set 1 - Q19: Use separate names for incoming and outgoing data (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `19`.

An `Event` model has one internal field, `request_id`. Its field configuration is `Field(validation_alias="request-id", serialization_alias="requestId")`. After `Event.model_validate({"request-id": "r1"})`, what does `model_dump(by_alias=True)` return?

A. `{"request_id": "r1"}`.

B. `{"requestId": "r1"}`.

C. `{"request-id": "r1"}`.

D. `{"request-id": "r1", "requestId": "r1"}`.

**Answer: B.**

**Why it works:** The input is read using `validation_alias`, and alias-enabled output uses `serialization_alias`. Both names refer to the same internal field.

**Why the other choices fail:**

- **A:** The internal Python name is used in the ordinary dump here, without `by_alias=True`.
- **C:** The validation alias chooses the incoming key; it does not override the configured serialization alias.
- **D:** Aliases do not create two separate fields or duplicate the value in output.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field

class Event(BaseModel):
    request_id: str = Field(
        validation_alias="request-id",
        serialization_alias="requestId",
    )

incoming = {"request-id": "r1"}
print("Incoming dictionary:", incoming)
event = Event.model_validate(incoming)
print("Internal attribute:", event.request_id)
print("Ordinary dump:", event.model_dump())
print("Alias-enabled dump:", event.model_dump(by_alias=True))
```

**Expected output — captured from the local run:**

```text
Incoming dictionary: {'request-id': 'r1'}
Internal attribute: r1
Ordinary dump: {'request_id': 'r1'}
Alias-enabled dump: {'requestId': 'r1'}
```

**Follow the key lines:**

1. `validation_alias="request-id"` tells validation where to find the incoming value.
2. Inside Python, the value is still accessed with `event.request_id`; no hyphenated Python attribute is created.
3. The ordinary dump uses the internal name `request_id` under the default configuration in this example.
4. `by_alias=True` asks serialization to use `requestId`. There is still just one output key for the one field.


---

## Set 1 - Q20: Read a nested validation error path (Medium)

**Original reference:** `Python-Pydantic-M-Set1`, question `20`.

A `Batch` model declares `items: list[Item]`, and each `Item` declares `qty: int`. Input is `{"items": [{"qty": 1}, {"qty": "bad"}]}`. The second item fails integer parsing. Which `loc` tuple in `ValidationError.errors()` identifies that failure? List positions are zero-based.

A. `("items", 1, "qty")`.

B. `("items", 2, "qty")`.

C. `("qty",)`.

D. `("items", "qty", "bad")`.

**Answer: A.**

**Why it works:** The path follows the input structure: outer field `items`, list index `1`, then the nested field `qty`.

**Why the other choices fail:**

- **B:** The second list element has index `1`, not `2`.
- **C:** This omits the outer field and list index needed to locate the failing item.
- **D:** The invalid value belongs in error data such as `input`; it is not a structural path component.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError

class Item(BaseModel):
    qty: int

class Batch(BaseModel):
    items: list[Item]

incoming = {"items": [{"qty": 1}, {"qty": "bad"}]}
print("Input:", incoming)
try:
    Batch.model_validate(incoming)
except ValidationError as error:
    print("Error count:", error.error_count())
    first = error.errors()[0]
    print("Location:", first["loc"])
    print("Error type:", first["type"])
    print("Invalid value:", repr(first["input"]))
```

**Expected output — captured from the local run:**

```text
Input: {'items': [{'qty': 1}, {'qty': 'bad'}]}
Error count: 1
Location: ('items', 1, 'qty')
Error type: int_parsing
Invalid value: 'bad'
```

**Follow the key lines:**

1. `items` is a list of nested `Item` models, so validation descends through the list and into each `qty` field.
2. The first item has integer `1` and passes. The second item contains `"bad"`, which cannot be parsed as an integer.
3. `errors()[0]` returns the structured description of that one failure. Its `loc` follows the dictionary key, list index, and nested key.
4. `type` describes the failure as `int_parsing`, while `input` records `"bad"` separately. There is no need to parse human-readable error-message text.

---

## Set 2 - Q01: Protect a read-modify-write across an await (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `01`.

Two coroutines share `count = 0` on one event loop. Each reads `old = count`, yields with `await asyncio.sleep(0)`, then assigns `count = old + 1`. Both are started together with `asyncio.gather`, using the default task factory. What final count results, and which change protects the whole operation?

A. The count is `1`; construct a new `asyncio.Lock()` inside each call.

B. The count is `2`; a single event-loop thread makes the whole coroutine atomic.

C. The count is `1`; use one shared `asyncio.Lock` around the read, await, and write.

D. The count is `2`; `gather` runs its arguments one at a time.

**Answer: C.**

- C: Both calls can read zero before either writes, so both write one. One shared lock makes the second call wait until the first has completed the protected operation.
- A: Two separately constructed locks do not exclude each other; both calls could enter their own lock.
- B: One thread still interleaves coroutines at an await. The entire function is not atomic.
- D: `gather` schedules the coroutines concurrently; argument order does not serialize them.

**Standalone example — tested locally; no API key required.** This is real local asyncio execution; no service is called. The await intentionally exposes the interleaving.

```python
import asyncio


async def main():
    count = 0
    reads = []

    async def unsafe_increment():
        nonlocal count
        old = count
        reads.append(old)
        await asyncio.sleep(0)
        count = old + 1

    await asyncio.gather(unsafe_increment(), unsafe_increment())
    print("Unprotected reads:", reads)
    print("Unprotected final count:", count)

    count = 0
    reads = []
    lock = asyncio.Lock()  # One shared lock, created outside either call.

    async def safe_increment():
        nonlocal count
        async with lock:
            old = count
            reads.append(old)
            await asyncio.sleep(0)
            count = old + 1

    await asyncio.gather(safe_increment(), safe_increment())
    print("Protected reads:", reads)
    print("Protected final count:", count)


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Unprotected reads: [0, 0]
Unprotected final count: 1
Protected reads: [0, 1]
Protected final count: 2
```

**Follow the key lines:**

1. The unprotected calls both save `old = 0`. `sleep(0)` gives the other scheduled coroutine a chance to run before the write.
2. Each then calculates `0 + 1`. The final result is one, even though two increments were requested.
3. The fixed version creates `lock` once in `main`. Both increment calls use that same object.
4. `async with lock` protects the whole read/await/write region. The second call reads one only after the first has written it, so the final count is two.
5. This is an in-process demonstration. A local asyncio lock does not coordinate separate worker processes. In real code, avoid placing slow I/O inside a lock when the operation can be redesigned.


---

## Set 2 - Q02: Give related tasks one cleanup scope (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `02`.

Three evidence-reading tasks belong to one request. One raises `ValueError`. The other two are still waiting and cooperate with cancellation. Before control leaves the task scope, both unfinished siblings must be cancelled and their cleanup awaited. Which construct provides this behavior directly?

A. Create the three tasks inside `async with asyncio.TaskGroup()`.

B. Use `await asyncio.gather(...)` with its default arguments.

C. Create three tasks and await only whichever fails first.

D. Use `asyncio.gather(..., return_exceptions=True)`.

**Answer: A.**

- A: A `TaskGroup` owns the tasks. A non-cancellation failure cancels unfinished siblings and waits for their completion before the scope exits; it then reports the grouped failure.
- B: Default `gather` propagates the first exception but does not automatically cancel all sibling awaitables as part of that failure policy.
- C: Observing one task does not cancel or await the other tasks.
- D: `return_exceptions=True` collects exceptions as results while letting the other tasks continue; it does not implement the required fail-and-cancel policy.

**Standalone example — tested locally; no API key required.** The evidence reads and failure are simulated with local events. TaskGroup cancellation and cleanup are real local behavior; no network request runs.

```python
import asyncio


async def main():
    both_started = asyncio.Event()
    started = []
    cleaned_up = []

    async def read_evidence(name):
        started.append(name)
        if len(started) == 2:
            both_started.set()
        try:
            await asyncio.Event().wait()  # Simulated unfinished I/O.
        finally:
            cleaned_up.append(name)

    async def fail_read():
        await both_started.wait()
        raise ValueError("Simulated bad evidence")

    failure_count = 0
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(read_evidence("A"))
            group.create_task(read_evidence("B"))
            group.create_task(fail_read())
    except* ValueError as errors:
        failure_count = len(errors.exceptions)

    # These lines run after the TaskGroup has awaited sibling cleanup.
    print("Started siblings:", sorted(started))
    print("Cleaned-up siblings:", sorted(cleaned_up))
    print("ValueError failures:", failure_count)
    print("Task scope exited")


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Started siblings: ['A', 'B']
Cleaned-up siblings: ['A', 'B']
ValueError failures: 1
Task scope exited
```

**Follow the key lines:**

1. `both_started` makes the failure wait until A and B have actually started. The demonstration does not guess their timing with a long sleep.
2. Each reader waits on an unset event as a stand-in for pending I/O. Its `finally` block records cleanup when cancellation arrives.
3. `group.create_task(...)` attaches each task to this `TaskGroup`. When `fail_read` raises, the group cancels the pending readers and awaits their cleanup.
4. `except* ValueError` handles the `ValueError` subgroup reported by the group. It is the grouped-exception syntax used with `TaskGroup` failures.
5. After the scope and handler finish, both names appear in `cleaned_up`. The names are sorted only for stable display; cleanup order is not the contract.


---

## Set 2 - Q03: Preserve cancellation after cleanup (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `03`.

A coroutine has been cancelled by its caller while it awaits an operation. Its `except asyncio.CancelledError` handler releases a resource, then returns a cached answer. The contract requires the caller to observe cancellation, not a successful fallback. What should the handler do after successful cleanup?

A. Keep returning the cached answer; catching `CancelledError` cannot suppress cancellation.

B. Raise `RuntimeError("cancelled")` instead of the cancellation exception.

C. Shield the inner operation and keep returning the cached answer.

D. Use a bare `raise` to re-raise the caught `CancelledError`.

**Answer: D.**

- D: A bare `raise` inside this handler preserves the caught cancellation signal after cleanup.
- A: Catching the exception and returning a value can turn the task into a normal successful result.
- B: `RuntimeError` signals an ordinary failure, changing the meaning the caller is required to observe.
- C: Shielding changes cancellation of inner work; it does not repair a handler that suppresses cancellation by returning.

**Standalone example — tested locally; no API key required.** The pending operation and resource are local simulations. Cancellation is requested explicitly rather than waiting for a real request deadline.

```python
import asyncio


async def main():
    started = asyncio.Event()
    cleanup = []

    async def slow_call():
        started.set()
        await asyncio.Event().wait()  # Simulated pending operation.

    async def release():
        cleanup.append("resource released")

    async def run():
        try:
            return await slow_call()
        except asyncio.CancelledError:
            await release()
            raise

    task = asyncio.create_task(run())
    await started.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Caller observed: CancelledError")
    print("Cleanup:", cleanup)
    print("Task cancelled:", task.cancelled())


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Caller observed: CancelledError
Cleanup: ['resource released']
Task cancelled: True
```

**Follow the key lines:**

1. `started` tells the caller that the task has reached the pending operation before it requests cancellation.
2. `task.cancel()` requests cancellation. The next cancellable wait raises `asyncio.CancelledError` inside `run`.
3. The handler awaits `release()` so this sample resource cleanup happens first.
4. Bare `raise` re-raises the caught cancellation. It does not create a replacement `RuntimeError` or return a cached result.
5. The caller catches `CancelledError`, and `task.cancelled()` is `True`. The cleanup list confirms that releasing the resource did not require suppressing cancellation.


---

## Set 2 - Q04: Use one timeout for the whole request (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `04`.

Retrieval and generation are consecutive, nonblocking, cancellation-cooperative coroutines. A request has one total two-second budget. Retrieval takes 1.4 seconds; generation would take another 1.2 seconds. Which design enforces the shared deadline, allowing normal scheduling and cleanup overhead?

A. Give each await its own fresh `asyncio.timeout(2)` scope.

B. Put both awaits inside one `asyncio.timeout(2)` scope and catch `TimeoutError` outside it.

C. Check elapsed time only after both stages have finished.

D. Allow retrieval two seconds, then give generation a fresh 1.2 seconds.

**Answer: B.**

- B: One timeout scope covers the combined work. Time consumed by retrieval reduces the time left for generation.
- A: Two fresh budgets can allow the stated 2.6-second combined operation to complete, exceeding the two-second total.
- C: Measuring afterward detects an overrun after the work has already completed; it does not enforce the deadline.
- D: A fresh generation allowance ignores the time already consumed by retrieval.

**Standalone example — tested locally; no API key required.** Evidence and generation are simulated. The timeout mechanism is real local asyncio behavior; real service latency and production deadlines were not tested.

```python
import asyncio


async def main():
    events = []

    async def retrieve():
        events.append("retrieval finished")
        return "Revenue grew 12%."

    async def generate(evidence):
        events.append("generation started: " + evidence)
        try:
            await asyncio.Event().wait()  # Simulated work awaiting cancellation.
        finally:
            events.append("generation cleaned up")

    # A short demonstration budget; this does not measure the 1.4s/1.2s scenario.
    try:
        async with asyncio.timeout(0.01):
            evidence = await retrieve()
            await generate(evidence)
    except TimeoutError:
        events.append("caller received TimeoutError")

    for event in events:
        print(event)


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
retrieval finished
generation started: Revenue grew 12%.
generation cleaned up
caller received TimeoutError
```

**Follow the key lines:**

1. The original numbers leave about `2.0 - 1.4 = 0.6` seconds for generation. The two stages share a budget rather than restarting it.
2. The runnable example uses a 0.01-second budget for a quick local demonstration. Retrieval returns a fixed sample immediately, and generation waits until cancelled; it does not reproduce or benchmark the original stage durations.
3. Both awaits are inside the same `asyncio.timeout(...)` block. When its deadline expires, the pending generation receives cancellation and runs its `finally` cleanup.
4. The timeout context converts its cancellation into `TimeoutError`, which is caught outside the context.
5. The output shows cleanup before the caller handles the timeout. A timeout is not a guarantee of exact wall-clock termination for arbitrary blocking code or cleanup.


---

## Set 2 - Q05: Make backpressure reach the producer (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `05`.

A source streams millions of fixed-size records faster than workers can process them. The pipeline must keep pending records bounded in memory without dropping records. The source itself can pause between records. Which arrangement meets that requirement?

A. Use a bounded queue, but create a new task for every `queue.put(record)` without awaiting each put.

B. Use a bounded `asyncio.Queue`, a fixed number of workers, and a producer that awaits each `queue.put(record)`.

C. Use an unbounded queue and a semaphore only around worker processing.

D. Create one task per record and put a semaphore inside each task.

**Answer: B.**

- B: A full bounded queue makes an awaited put wait, slowing the producer. A fixed worker count also bounds active processing.
- A: An unlimited number of pending put tasks can retain records outside the queue, defeating the memory bound.
- C: A semaphore limits active work but does not stop an unbounded queue from accumulating waiting records.
- D: Waiting tasks themselves can retain the records even before they obtain a semaphore permit.

**Standalone example — tested locally; no API key required.** Only three local records are used. Processing is simulated, and the example tests queue backpressure rather than a million-record throughput benchmark.

```python
import asyncio


async def main():
    queue = asyncio.Queue(maxsize=1)
    processed = []

    async def produce():
        for record in range(3):  # Small stand-in for a pausable streaming source.
            await queue.put(record)
        await queue.put(None)  # Sentinel tells the one worker to finish.

    async def work():
        while True:
            record = await queue.get()
            if record is None:
                return
            processed.append(record)
            await asyncio.sleep(0)  # Simulated nonblocking processing.

    producer = asyncio.create_task(produce())
    await asyncio.sleep(0)  # Let it fill the queue and wait on the next put.
    print("Queue size before worker:", queue.qsize())
    print("Producer already finished:", producer.done())

    # A fixed pool of one worker keeps this demonstration small.
    worker = asyncio.create_task(work())
    await producer
    await worker
    print("Processed:", processed)
    print("Queue size at end:", queue.qsize())


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Queue size before worker: 1
Producer already finished: False
Processed: [0, 1, 2]
Queue size at end: 0
```

**Follow the key lines:**

1. `maxsize=1` allows one waiting record inside the queue. The producer adds record zero, then waits when it tries to add the next record.
2. Before starting the worker, the queue size is one and `producer.done()` is `False`. Those intermediate values show backpressure reaching the producer.
3. The producer uses `await queue.put(record)` directly. It does not create an unlimited number of background put tasks.
4. The one worker removes and processes records in order. Removing a queued record allows the producer to add the next one.
5. `None` is a sentinel, a sample value meaning stop. The worker exits only after all three records, and the final list confirms none were dropped.
6. The queue bound applies to waiting queue entries; one worker and the producer can also hold a record. This is a small bounded pipeline demonstration, not a measurement of total production memory or external buffers.


---

## Set 2 - Q06: Distinguish cancelling a wait from stopping a thread (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `06`.

A synchronous SDK write has already started inside `asyncio.to_thread()`. The awaiting request task is then cancelled. The SDK has no cancellation or rollback API. Which conclusion is justified?

A. `to_thread` turns cancellation into a successful SDK return value.

B. Cancellation forcibly stops the thread, so the write cannot finish.

C. Cancelling the request automatically rolls back the remote write.

D. The thread may still finish the write; check or reconcile its outcome before assuming it failed.

**Answer: D.**

- D: Cancelling the awaiting task does not forcibly terminate a running Python thread. Work already in progress may still complete.
- A: The awaiting task receives cancellation; `to_thread` does not fabricate a successful business result.
- B: Cancellation of an await is not forced termination of the already-running thread.
- C: Local task cancellation is not a transaction rollback protocol for an external SDK or service.

**Standalone example — tested locally; no API key required.** The SDK and committed write are explicitly simulated with threading events and a local list. It tests an already-started thread, not cancellation of a job that has not begun.

```python
import asyncio
import threading


async def main():
    started = threading.Event()
    finish_write = threading.Event()
    finished = threading.Event()
    writes = []

    def sdk_write():
        # Simulated synchronous SDK; no external write is performed.
        started.set()
        finish_write.wait()
        writes.append("operation-7 committed")
        finished.set()
        return "ok"

    task = asyncio.create_task(asyncio.to_thread(sdk_write))
    await asyncio.to_thread(started.wait)
    print("SDK thread started:", started.is_set())
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Awaiting task: cancelled")
    print("Writes before release:", writes)

    finish_write.set()  # Let the already-running synchronous operation finish.
    await asyncio.to_thread(finished.wait)
    print("Writes after release:", writes)


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
SDK thread started: True
Awaiting task: cancelled
Writes before release: []
Writes after release: ['operation-7 committed']
```

**Follow the key lines:**

1. `started` confirms that the synchronous function is already running in a thread before the caller requests cancellation.
2. `finish_write.wait()` blocks that worker thread until the example explicitly releases it. It is a local stand-in for an SDK operation still in progress.
3. The caller cancels and awaits the asyncio task, receiving `CancelledError`. That stops this request from waiting for the SDK result.
4. The thread remains alive. After `finish_write.set()`, it appends a simulated committed write and signals `finished`.
5. The final list contains the write even though the awaiting task was cancelled. In a real integration, an operation ID and status lookup can help determine the eventual outcome. This example performs no remote write or rollback test.


---

## Set 2 - Q07: Understand the context copied into a child task (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `07`.

A `ContextVar` named `request_id` is set to `"A"`. The parent creates an asyncio task that will read it, then sets its own binding to `"B"` before awaiting the child. Use the default task factory and do not pass an explicit `context` argument. What does the child's one `get()` call return?

A. `"A"`, because task creation copies the current context.

B. `"B"`, because a child always reads the parent’s latest binding.

C. `None`, because child tasks never inherit context variables.

D. Both `"A"` and `"B"`, because one read returns the binding history.

**Answer: A.**

- A: `asyncio.create_task` copies the current context by default. The child receives the A binding at creation, even when it starts running after the parent sets B.
- B: Later changes to the parent’s binding do not change the child task’s copied context binding.
- C: The default task-creation behavior does copy context; a variable with no default would otherwise raise on an unset get, not automatically return None.
- D: `get()` returns one value for the current context, not a history of values.

**Standalone example — tested locally; no API key required.** This runs the actual local ContextVar and asyncio task APIs. It uses no web request or tracing system.

```python
import asyncio
from contextvars import ContextVar


request_id = ContextVar("request_id")


async def read_id():
    return request_id.get()


async def main():
    request_id.set("A")
    print("Parent at task creation:", request_id.get())
    child = asyncio.create_task(read_id())
    request_id.set("B")
    print("Parent before await:", request_id.get())
    print("Child value:", await child)
    print("Parent after await:", request_id.get())


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Parent at task creation: A
Parent before await: B
Child value: A
Parent after await: B
```

**Follow the key lines:**

1. The parent sets A before calling `create_task`. That is the binding copied into the child task’s context.
2. There is no await between creating the task and setting B. With the stated default task factory, the parent changes its own binding before the child runs.
3. The child later calls `request_id.get()` in its own task context and receives A.
4. The parent still sees B after awaiting the child. Context isolation applies to bindings; it does not promise a deep copy of mutable objects stored as values. This example uses immutable strings.


---

## Set 2 - Q08: Count the scope of a semaphore limit (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `08`.

Four independent worker processes each create their own `asyncio.Semaphore(8)`. Every outbound call holds one permit until completion. All four processes are busy, and there are no other limits. How many calls can be in flight, and how could a fleet-wide cap of eight be enforced?

A. At most four; each event loop can have only one outbound I/O operation in flight.

B. At most eight; asyncio semaphores share permits automatically across processes.

C. Up to 32; use coordinated admission control or per-process budgets whose sum is eight.

D. Up to 32; give all semaphore variables the same global name.

**Answer: C.**

- C: The four independent sets of eight permits total 32. A fleet cap requires shared coordination or a fixed allocation whose total is eight.
- A: An event loop can have many concurrent I/O operations waiting for completion.
- B: An `asyncio.Semaphore` is a local synchronization object, not an automatic cross-process permit service.
- D: Equal variable names in separate processes do not share their objects or permits.

**Standalone example — tested locally; no API key required.** This intentionally uses a simple capacity simulation. No fleet-wide limit, real process coordination, or outbound I/O was tested.

```python
# Capacity simulation only: no worker processes or network calls are launched.
workers = ["worker-1", "worker-2", "worker-3", "worker-4"]
independent_budgets = {name: 8 for name in workers}
fixed_fleet_budgets = {name: 2 for name in workers}

print("Independent per-process permits:", list(independent_budgets.values()))
print("Possible simultaneous calls:", sum(independent_budgets.values()))
print("Fixed per-process fleet allocation:", list(fixed_fleet_budgets.values()))
print("Combined fixed cap:", sum(fixed_fleet_budgets.values()))
```

**Expected output — captured from the local run:**

```text
Independent per-process permits: [8, 8, 8, 8]
Possible simultaneous calls: 32
Fixed per-process fleet allocation: [2, 2, 2, 2]
Combined fixed cap: 8
```

**Follow the key lines:**

1. Each process has its own eight-permit object. The first dictionary represents those four independent capacities.
2. Adding them gives `8 + 8 + 8 + 8 = 32` possible in-flight calls under the question’s assumptions.
3. The sample fixed allocation assigns two permits per process. Its sum is eight, so processes that respect those fixed allocations cannot jointly exceed eight.
4. This is arithmetic illustrating the scope of the limit, not a distributed semaphore implementation or a multiprocess load test. A fixed allocation must account for the actual worker count and can leave capacity unused when some workers are idle.


---

## Set 2 - Q09: Use processes for pure-Python CPU work (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `09`.

A profile of ordinary GIL-enabled CPython 3.12 shows four independent, long-running, pure-Python CPU transformations dominate latency. Inputs and results are picklable, enough CPU cores are available, and useful work outweighs process-transfer overhead. Which option most directly enables execution on multiple CPU cores?

A. Submit the transformations to a suitably sized `ProcessPoolExecutor`.

B. Put the transformations inside `async def` and use `asyncio.gather`.

C. Run `asyncio.to_thread` four times and assume four-core Python bytecode execution.

D. Insert `asyncio.sleep(0)` repeatedly inside each transformation.

**Answer: A.**

- A: Separate processes use separate interpreters, allowing independent Python bytecode work on multiple CPU cores under the stated assumptions.
- B: An async declaration does not make CPU work run in parallel or automatically move it off the event-loop thread.
- C: Under the question’s GIL-enabled, pure-Python assumption, threads do not generally provide parallel execution of that Python bytecode on four cores.
- D: Yielding lets other coroutines be scheduled; it does not create multicore CPU execution.

**Standalone example — tested locally; no API key required.** Actual local worker processes are used, with no service or API key. The workload is intentionally tiny; no CPU-scaling or performance claim is made.

```python
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context


def transform(limit):
    # Tiny pure-Python stand-in for a much larger independent transformation.
    return sum(number * number for number in range(limit))


def main():
    inputs = [3, 4, 5, 6]
    print("Inputs:", inputs)
    with ProcessPoolExecutor(
        max_workers=2, mp_context=get_context("spawn")
    ) as pool:
        results = list(pool.map(transform, inputs))
    print("Results:", results)
    print("First result calculation:", "0*0 + 1*1 + 2*2 =", results[0])


if __name__ == "__main__":
    main()
```

**Expected output — captured from the local run:**

```text
Inputs: [3, 4, 5, 6]
Results: [5, 14, 30, 55]
First result calculation: 0*0 + 1*1 + 2*2 = 5
```

**Follow the key lines:**

1. `transform` is a top-level function and its integer input is picklable, so a spawned worker can import and execute it.
2. `ProcessPoolExecutor(max_workers=2, ...)` creates a pool with up to two worker processes. The tiny sample uses two rather than claiming a four-core benchmark.
3. `pool.map` submits the independent inputs and returns results in input order. Completion order need not equal that display order.
4. For input three, `range(3)` is zero, one, two; the squared total is five. The other totals are fourteen, thirty, and fifty-five.
5. The `if __name__ == "__main__"` guard prevents spawned child processes from creating the pool again when they import the file.
6. Run this block as a saved `.py` file. It tests actual process-pool execution, but the tiny workload is not a speedup benchmark and may cost more to transfer than to compute.


---

## Set 2 - Q10: Close an async generator after an early break (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `10`.

`stream()` is an async generator whose `finally` block releases a connection. The caller stops after the first item. Cleanup must complete before the caller leaves the surrounding scope. Which pattern gives explicit, deterministic closure?

A. Call `rows.close()` synchronously after the loop.

B. Use an ordinary `async for` and assume `break` always immediately closes the generator.

C. Use `async with contextlib.aclosing(stream()) as rows`, with the `async for` inside that block.

D. Wait for garbage collection to run the generator cleanup eventually.

**Answer: C.**

- C: `aclosing` awaits the async generator’s `aclose()` when its context exits, including after an early break.
- A: An async generator exposes awaitable `aclose()`, not this synchronous `close()` call.
- B: Ending iteration early does not itself provide the requested immediate async-generator closure guarantee.
- D: Eventual garbage collection does not meet a requirement that cleanup finish before the scope exits.

**Standalone example — tested locally; no API key required.** The connection is simulated by a local event log. Async-generator closure and its awaited cleanup are actual local execution.

```python
import asyncio
from contextlib import aclosing


async def main():
    events = []

    async def stream():
        events.append("connection opened")
        try:
            yield "first evidence"
            yield "second evidence"
        finally:
            # Simulated asynchronous connection release.
            await asyncio.sleep(0)
            events.append("connection released")

    async with aclosing(stream()) as rows:
        async for item in rows:
            print("Consumed:", item)
            break
        print("Released before context exit:", "connection released" in events)
    print("Released after context exit:", "connection released" in events)
    print("Events:", events)


asyncio.run(main())
```

**Expected output — captured from the local run:**

```text
Consumed: first evidence
Released before context exit: False
Released after context exit: True
Events: ['connection opened', 'connection released']
```

**Follow the key lines:**

1. The first iteration enters `stream`, records the opening, and yields the first evidence item.
2. `break` stops the loop after one item. Inside the context but after the loop, cleanup has not yet run, so the first release check is False.
3. Leaving `async with aclosing(...)` awaits `rows.aclose()`. Closing the suspended generator runs its `finally` block.
4. The cleanup itself awaits once before recording release. `aclosing` waits for that asynchronous cleanup to finish.
5. After the context exits, release is True and the event log shows open followed by release. The second evidence item is never consumed.

---

## Set 2 - Q11: Select an event branch with a discriminator (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `11`.

An API accepts two event shapes. A success has `status: Literal["ok"]` and a required `value: float`. A failure has `status: Literal["error"]` and a required `message: str`. Both branch models use `extra="forbid"`.

The payload is `{"status": "ok", "message": "timeout"}`. It must be rejected as an inconsistent success, rather than silently relabeled as a failure. Which contract directly expresses these two valid event shapes?

A. Accept a `dict[str, Any]` and ask the producer to use consistent fields.

B. Use one model with `status: str` and independently optional `value` and `message` fields, without further validation.

C. Change `status` to `"error"` whenever a `message` field is present.

D. Use a discriminated union of the two branch models, with literal tags and `discriminator="status"`.

**Answer: D.**

**Why it works:** The discriminator reads `status` and selects the corresponding branch. `"ok"` selects the success model. That branch requires `value` and forbids `message`, so this contradictory payload fails instead of being treated as a failure event.

**Why the other choices fail:**

- **A:** A broad dictionary does not enforce the event fields or their relationship.
- **B:** Without an additional invariant, independently optional fields permit `status="ok"` together with `message` and no value.
- **C:** Rewriting the tag conceals the producer contradiction rather than rejecting the supplied event.

**Standalone Python example — tested locally; no API key required.**

```python
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Success(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]
    value: float


class Failure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["error"]
    message: str


Event = Annotated[Success | Failure, Field(discriminator="status")]


class Envelope(BaseModel):
    event: Event


good = Envelope.model_validate({"event": {"status": "ok", "value": 12.5}})
print("Selected branch:", type(good.event).__name__)
print("Valid event:", good.event.model_dump())

bad_event = {"status": "ok", "message": "timeout"}
print("Invalid event:", bad_event)
try:
    Envelope.model_validate({"event": bad_event})
except ValidationError as error:
    for item in error.errors():
        print("Error:", item["loc"], item["type"])
```

**Expected output — observed locally:**

```text
Selected branch: Success
Valid event: {'status': 'ok', 'value': 12.5}
Invalid event: {'status': 'ok', 'message': 'timeout'}
Error: ('event', 'ok', 'value') missing
Error: ('event', 'ok', 'message') extra_forbidden
```

**Follow the key lines:**

1. `Success` and `Failure` name the valid fields for each event. `Literal` restricts each status to its exact tag.
2. `Field(discriminator="status")` tells Pydantic to use the supplied tag to choose one model, rather than rewrite the payload.
3. The valid payload selects `Success` and stores `12.5` in its `value` field.
4. The invalid payload still selects `Success` because its status is `"ok"`. The error path contains `"ok"` to identify that selected branch.
5. The two reported problems are a missing `value` and a forbidden `message`. Pydantic does not reinterpret the event as `Failure`.


---

## Set 2 - Q12: Validate untrusted updates after merging plain data (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `12`.

A Pydantic model named `Config` declares `retries: int = Field(gt=0)`. `old = Config(retries=2)` is valid. The code then runs `new = old.model_copy(update={"retries": "bad"})` and prints `new.retries` followed by `type(new.retries).__name__`.

Under default Pydantic 2 behavior, what prints, and how should the application handle this untrusted patch?

A. A `ValidationError` is raised because `model_copy` always validates update values.

B. `bad str` prints; merge the existing dumped data with the patch, then call `Config.model_validate` on that plain data.

C. `0 int` prints because invalid integer updates are replaced with zero.

D. `bad str` prints; adding `deep=True` to `model_copy` makes the patch pass through validation.

**Answer: B.**

**Why it works:** `model_copy(update=...)` trusts the supplied update values. It does not parse the string or check the positive-integer constraint. To enforce the contract at an untrusted update boundary, validate a merged dictionary before using the updated configuration.

**Why the other choices fail:**

- **A:** `model_copy` explicitly does not validate its update data.
- **C:** No integer parser or fallback runs during this copy operation.
- **D:** `deep=True` changes copying of nested objects; it does not enable validation of the updates.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field, ValidationError


class Config(BaseModel):
    retries: int = Field(gt=0)


old = Config(retries=2)
patch = {"retries": "bad"}
new = old.model_copy(update=patch)
print("Copied value:", new.retries, type(new.retries).__name__)
print("Original value:", old.retries)

merged = {**old.model_dump(), **patch}
print("Merged untrusted data:", merged)
try:
    Config.model_validate(merged)
except ValidationError as error:
    item = error.errors()[0]
    print("Validation rejected:", item["loc"], item["type"])

valid_patch = {"retries": 3}
checked = Config.model_validate({**old.model_dump(), **valid_patch})
print("Validated update:", checked.retries, type(checked.retries).__name__)
```

**Expected output — observed locally:**

```text
Copied value: bad str
Original value: 2
Merged untrusted data: {'retries': 'bad'}
Validation rejected: ('retries',) int_parsing
Validated update: 3 int
```

**Follow the key lines:**

1. `old` begins with the validated integer `2`.
2. `model_copy(update=patch)` places the raw string `"bad"` in the copied object. The printed type is `str`; the original object still has `2`.
3. `{**old.model_dump(), **patch}` starts with existing values, then lets patch keys replace matching keys. It produces ordinary untrusted data, not a validated model.
4. `Config.model_validate(merged)` runs the integer parser and the field constraint. The bad string fails parsing with `int_parsing`.
5. The same merge-and-validate boundary accepts the integer `3`. Only use this newly validated result after validation succeeds.


---

## Set 2 - Q13: Distinguish strict Python input from strict JSON input (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `13`.

A model `D` has one field, `day: date`. Evaluate these two calls independently, both with `strict=True`: `D.model_validate({"day": "2026-01-01"}, strict=True)` and `D.model_validate_json('{"day":"2026-01-01"}', strict=True)`.

Which result is expected, and what does it mean for ingress tests?

A. The Python-dictionary call succeeds and the JSON call fails because JSON cannot carry date representations.

B. Both fail because strict mode rejects every string representation in every input mode.

C. Both succeed because every `YYYY-MM-DD` string is accepted for a strict Python date field.

D. The Python-dictionary call fails and the JSON call succeeds; tests should exercise the actual validation input mode.

**Answer: D.**

**Why it works:** Strict Python validation expects a `date` instance for this field. Strict JSON validation accepts a supported date string because JSON has no native date value. The same-looking text can therefore have different acceptance rules depending on the validation entry point.

**Why the other choices fail:**

- **A:** JSON can carry the supported date string, even though it has no dedicated date type.
- **B:** Strict JSON mode permits supported representations needed for values JSON cannot encode natively.
- **C:** A date-looking string is still a string in a Python dictionary; strict Python validation rejects that conversion.

**Standalone Python example — tested locally; no API key required.**

```python
from datetime import date
from pydantic import BaseModel, ValidationError


class D(BaseModel):
    day: date


python_input = {"day": "2026-01-01"}
print("Python input type:", type(python_input["day"]).__name__)
try:
    D.model_validate(python_input, strict=True)
except ValidationError as error:
    item = error.errors()[0]
    print("Strict Python error:", item["loc"], item["type"])

json_input = '{"day":"2026-01-01"}'
from_json = D.model_validate_json(json_input, strict=True)
print("Strict JSON result:", from_json.day, type(from_json.day).__name__)

from_python_date = D.model_validate({"day": date(2026, 1, 1)}, strict=True)
print("Strict Python date result:", from_python_date.day)
```

**Expected output — observed locally:**

```text
Python input type: str
Strict Python error: ('day',) date_type
Strict JSON result: 2026-01-01 date
Strict Python date result: 2026-01-01
```

**Follow the key lines:**

1. `python_input["day"]` is a Python `str`. `strict=True` prevents that input from being converted into a date through the Python validation path.
2. The error identifies `day` and uses `date_type` to explain the type mismatch.
3. `model_validate_json` receives the original JSON text. On this input path, the supported date representation is a JSON string.
4. Successful JSON validation stores a Python `date`, not the original string.
5. A genuine `date(2026, 1, 1)` also succeeds in strict Python mode. This shows that the rejection concerns the supplied representation, not the calendar value.


---

## Set 2 - Q14: Freeze the model and choose immutable contained values (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `14`.

A model `Snapshot` has `model_config = ConfigDict(frozen=True)` and `tags: list[str]`. After `s = Snapshot(tags=["reviewed"])`, code calls `s.tags.append("changed")`.

What happens, and which declaration better represents an immutable collection of string tags?

A. The append succeeds; use `tuple[str, ...]` for tags together with the frozen model.

B. The append raises `ValidationError` because frozen models recursively freeze every contained object.

C. The append succeeds; adding `extra="forbid"` makes the existing list immutable.

D. The append creates a new model, leaving the original list unchanged.

**Answer: A.**

**Why it works:** The frozen setting prevents ordinary reassignment of model attributes. It does not recursively freeze a list already stored in a field. A tuple of strings removes this list-mutation path while the frozen model prevents replacing the field normally.

**Why the other choices fail:**

- **B:** Nested list operations are not model attribute assignments; the frozen setting does not recursively intercept them.
- **C:** Extra-field policy controls unknown input keys, not mutation of an existing list.
- **D:** `list.append` mutates the same list; it does not construct a replacement model.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Snapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    tags: list[str]


s = Snapshot(tags=["reviewed"])
print("Before append:", s.tags)
s.tags.append("changed")
print("After append:", s.tags)


class ImmutableSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    tags: tuple[str, ...]


safe = ImmutableSnapshot(tags=("reviewed",))
print("Immutable tags:", safe.tags, type(safe.tags).__name__)
try:
    safe.tags = ("changed",)
except ValidationError as error:
    print("Attribute replacement error:", error.errors()[0]["type"])
print("Unchanged tags:", safe.tags)
```

**Expected output — observed locally:**

```text
Before append: ['reviewed']
After append: ['reviewed', 'changed']
Immutable tags: ('reviewed',) tuple
Attribute replacement error: frozen_instance
Unchanged tags: ('reviewed',)
```

**Follow the key lines:**

1. `s.tags` is a list. Calling its `append` method changes that list directly, so the output includes `"changed"`.
2. `frozen=True` applies to setting the model attribute, such as assigning a different object to `s.tags`. It does not turn list methods into forbidden operations.
3. `tuple[str, ...]` means a tuple containing zero or more strings. Tuples do not offer the list append operation.
4. The second model combines an immutable tuple of immutable strings with frozen field assignment. The attempted replacement raises `frozen_instance`.
5. The final print confirms that this simple snapshot still holds `("reviewed",)`. This example makes no claim that arbitrary nested objects would become immutable automatically.


---

## Set 2 - Q15: Revalidate an existing model instance when required (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `15`.

With default configuration, `Config` declares `retries: int`. Code constructs `cfg = Config(retries=2)`, then assigns `cfg.retries = "bad"`, then calls `Config.model_validate(cfg)`.

What happens, and which configuration option on `Config` specifically forces validation at the second boundary?

A. The second call always raises because `model_validate` always rechecks existing model instances.

B. The invalid instance is accepted; set `revalidate_instances="always"` to force revalidation at the second boundary.

C. The assignment itself always raises because assignment validation is enabled by default.

D. The invalid instance is accepted; set `extra="forbid"` to force validation of that existing value.

**Answer: B.**

**Why it works:** Default assignment behavior allows the field to be changed without parsing it again, and the default instance-revalidation policy trusts an existing instance of the model. `revalidate_instances="always"` changes that second behavior, making the later validation call check the mutated value.

**Why the other choices fail:**

- **A:** Existing model instances are not automatically revalidated under the default configuration.
- **C:** Assignment validation requires its own explicit setting; it is not enabled by default.
- **D:** Extra-field rejection concerns unknown input keys, not revalidation of values already stored in a model instance.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class DefaultConfig(BaseModel):
    retries: int


cfg = DefaultConfig(retries=2)
cfg.retries = "bad"
checked = DefaultConfig.model_validate(cfg)
print("Default boundary value:", checked.retries, type(checked.retries).__name__)
print("Same instance:", checked is cfg)


class RecheckedConfig(BaseModel):
    model_config = ConfigDict(revalidate_instances="always")
    retries: int


cfg2 = RecheckedConfig(retries=2)
cfg2.retries = "bad"
print("Before revalidation:", cfg2.retries, type(cfg2.retries).__name__)
try:
    RecheckedConfig.model_validate(cfg2)
except ValidationError as error:
    item = error.errors()[0]
    print("Revalidation rejected:", item["loc"], item["type"])
```

**Expected output — observed locally:**

```text
Default boundary value: bad str
Same instance: True
Before revalidation: bad str
Revalidation rejected: ('retries',) int_parsing
```

**Follow the key lines:**

1. The first model starts with integer `2`, but ordinary assignment later stores the string `"bad"`.
2. `DefaultConfig.model_validate(cfg)` trusts that existing instance. The printed identity check is `True`, and the bad string remains.
3. `revalidate_instances="always"` tells the second model to check existing instances when they pass through validation again.
4. That setting does not enable assignment validation. The direct assignment to `cfg2.retries` still happens; the later boundary catches it.
5. The second validation fails at `retries` with `int_parsing`. Catching this error does not repair the original mutated object.


---

## Set 2 - Q16: Serialize using the declared model type (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `16`.

`User` declares only `name: str`. `UserWithToken(User)` adds `token: str`. `Envelope` declares `user: User`, and receives `UserWithToken(name="Jay", token="demo-token")`.

With default Pydantic 2 serialization, no custom serializers, and no duck-typed serialization override, what does `Envelope(...).model_dump()` include? The token shown here is dummy sample text.

A. Neither field, because a subclass instance cannot be supplied for a base-model field.

B. Both `user.name` and `user.token`, because runtime subclasses always serialize every field.

C. Only `user.name`, because serialization follows the declared `User` field schema.

D. Both fields, with the plain string token automatically replaced by asterisks.

**Answer: C.**

**Why it works:** The field is declared as `User`, whose schema includes `name` but not `token`. Default serialization uses that declared model boundary. It accepts the compatible subclass object but omits fields declared only by that subclass from this envelope dump.

**Why the other choices fail:**

- **A:** A compatible subclass instance is accepted for the base-model field.
- **B:** Including all runtime-subclass fields requires serialization behavior different from the stated defaults.
- **D:** A plain string field named `token` has no automatic secret-masking policy.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str


class UserWithToken(User):
    token: str


class Envelope(BaseModel):
    user: User


# Dummy sample token, not a real credential.
user = UserWithToken(name="Jay", token="demo-token")
envelope = Envelope(user=user)
print("Stored runtime type:", type(envelope.user).__name__)
print("Subclass field still stored:", envelope.user.token == "demo-token")
print("Envelope dump:", envelope.model_dump())
print("Subclass's own dump keys:", sorted(user.model_dump()))
```

**Expected output — observed locally:**

```text
Stored runtime type: UserWithToken
Subclass field still stored: True
Envelope dump: {'user': {'name': 'Jay'}}
Subclass's own dump keys: ['name', 'token']
```

**Follow the key lines:**

1. `UserWithToken` inherits the `name` field and adds one extra field, `token`.
2. The `Envelope.user` annotation is `User`. Passing the subclass does not change that declaration.
3. The runtime object remains `UserWithToken`, and the comparison confirms that it still stores its dummy token. Serialization has not erased the data.
4. `envelope.model_dump()` serializes the nested value through the declared `User` schema, so only `name` appears.
5. Dumping `user` directly uses `UserWithToken` itself and includes both field names. Review the declared output type when deciding which fields a response should expose.


---

## Set 2 - Q17: Reuse a TypeAdapter for a JSON array of models (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `17`.

A service receives raw JSON text representing an array of records. `Record` is a Pydantic model with required fields `id: int` and `text: str`. The service needs runtime validation returning `list[Record]`, with no artificial enclosing model field.

Which design supplies that result and avoids rebuilding the same validator for each request?

A. Use a helper annotated as returning `list[Record]` that simply returns `json.loads(raw)`.

B. Call `typing.cast(list[Record], json.loads(raw))` for every request.

C. Create `TypeAdapter(list[Record])` once, then call `adapter.validate_json(raw)` for each request.

D. Create `TypeAdapter(list[dict[str, Any]])` once and assume the resulting dictionaries are `Record` instances.

**Answer: C.**

**Why it works:** `TypeAdapter` builds runtime validation for a type expression, including a list of models. Its JSON validation method parses the JSON and constructs validated `Record` objects. Keeping the adapter outside the request loop reuses that validation machinery.

**Why the other choices fail:**

- **A:** A return annotation does not change the dictionaries produced by `json.loads` or validate their fields.
- **B:** `cast` informs static type checking; it does not validate or construct model instances at runtime.
- **D:** The dictionary adapter validates a different, looser shape and returns dictionaries rather than `Record` instances.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, TypeAdapter, ValidationError


class Record(BaseModel):
    id: int
    text: str


# Build once; reuse this object for both sample requests.
adapter = TypeAdapter(list[Record])
requests = [
    '[{"id":"7","text":"Revenue"}]',
    '[{"id":8,"text":"Risk"},{"id":9,"text":"Outlook"}]',
]

for request_number, raw in enumerate(requests, start=1):
    records = adapter.validate_json(raw)
    print("Request", request_number, "types:", [type(item).__name__ for item in records])
    print("Validated values:", [item.model_dump() for item in records])

try:
    adapter.validate_json('[{"id":"bad","text":"Revenue"}]')
except ValidationError as error:
    item = error.errors()[0]
    print("Invalid record:", item["loc"], item["type"])
```

**Expected output — observed locally:**

```text
Request 1 types: ['Record']
Validated values: [{'id': 7, 'text': 'Revenue'}]
Request 2 types: ['Record', 'Record']
Validated values: [{'id': 8, 'text': 'Risk'}, {'id': 9, 'text': 'Outlook'}]
Invalid record: (0, 'id') int_parsing
```

**Follow the key lines:**

1. `TypeAdapter(list[Record])` describes the complete root shape: a list whose items must be `Record` models.
2. The adapter is created before the request loop. Both calls reuse that same object; the example does not make a timing or performance benchmark claim.
3. The first raw JSON contains string `"7"`. Default integer validation parses it to integer `7` inside a `Record` instance.
4. The second request produces two more `Record` objects. No extra wrapper key is added around the array.
5. The last input has an invalid ID. Its error path `(0, "id")` identifies the first array element and its `id` field.


---

## Set 2 - Q18: Pass request-specific validation context explicitly (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `18`.

An `Extraction` model has a string field `label`. Its field validator reads `info.context["labels"]` and rejects labels not in that request's allowed taxonomy. The allowed labels can differ between concurrent requests. The model uses default constructor behavior.

Which invocation supplies the taxonomy as validator context without changing process-global rules?

A. `Extraction(**payload, context={"labels": allowed_labels})`

B. `Extraction.model_validate(payload, context={"labels": allowed_labels})`

C. `Extraction.model_validate({**payload, "context": {"labels": allowed_labels}})`

D. Assign `Extraction.allowed_labels = allowed_labels` globally before validating each request.

**Answer: B.**

**Why it works:** `model_validate` accepts a separate `context` argument. Validators can read that specific call's context through `ValidationInfo`. Supplying context alone does not enforce membership: the validator must explicitly perform the check.

**Why the other choices fail:**

- **A:** With ordinary constructor behavior, that keyword is input data, not the separate validator context argument.
- **C:** Putting a `context` key inside the payload does not supply `info.context`.
- **D:** Changing one shared rule can make overlapping requests use each other's taxonomy.

**Standalone Python example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator


class Extraction(BaseModel):
    label: str

    @field_validator("label")
    @classmethod
    def allowed_label(cls, value: str, info: ValidationInfo) -> str:
        if info.context is None or "labels" not in info.context:
            raise ValueError("labels context is required")
        allowed = info.context["labels"]
        print("Validator sees:", value, "allowed:", allowed)
        if value not in allowed:
            raise ValueError("label is not allowed for this request")
        return value


payload = {"label": "finance"}
first = Extraction.model_validate(payload, context={"labels": ["finance", "risk"]})
print("First request result:", first.label)

try:
    Extraction.model_validate(payload, context={"labels": ["legal"]})
except ValidationError as error:
    item = error.errors()[0]
    print("Second request rejected:", item["loc"], item["type"])

try:
    Extraction.model_validate(payload)
except ValidationError as error:
    print("Missing context rejected:", error.errors()[0]["type"])
```

**Expected output — observed locally:**

```text
Validator sees: finance allowed: ['finance', 'risk']
First request result: finance
Validator sees: finance allowed: ['legal']
Second request rejected: ('label',) value_error
Missing context rejected: value_error
```

**Follow the key lines:**

1. The field validator receives the parsed string and `ValidationInfo`. Its `info.context` belongs to this validation call.
2. The first call passes `["finance", "risk"]`; the validator sees that list and accepts `"finance"`.
3. The second call uses the same payload with `["legal"]`. The validator sees the new request-specific list and rejects the same label.
4. `return value` keeps a valid label in the model. Raising `ValueError` becomes a structured Pydantic `ValidationError` at `label`.
5. The example also defines a missing-context policy: reject it. These calls run sequentially to show data flow; they do not test concurrent scheduling or use mutable global policy.


---

## Set 2 - Q19: Choose Decimal before binary-float arithmetic (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `19`.

A monetary calculation must preserve exact decimal input. Using the default Decimal context and exact equality, code calculates `a = Decimal(0.1 + 0.2)` and `b = Decimal("0.1") + Decimal("0.2")`, then prints `a == Decimal("0.3"), b == Decimal("0.3")`.

What prints, and which ingestion rule preserves the intended decimal values?

A. `True False`; arithmetic on decimal strings loses more precision than float conversion.

B. `True True`; converting any float to `Decimal` recovers its intended decimal value.

C. `False False`; `Decimal` cannot represent tenths exactly.

D. `False True`; retain decimal text and construct `Decimal` values before doing binary-float arithmetic.

**Answer: D.**

**Why it works:** The float expression is evaluated before `Decimal` receives it, so its binary approximation is already present. Decimal conversion preserves the supplied float value rather than guessing the intended decimal arithmetic. Constructing the two Decimal operands from text preserves these decimal fractions exactly.

**Why the other choices fail:**

- **A:** The string-based Decimal computation is the exact one for these values.
- **B:** Conversion cannot infer decimal intent from a float approximation.
- **C:** Finite tenths are exactly representable as Decimal values under the stated context.

**Standalone Python example — tested locally; no API key required.**

```python
from decimal import Decimal


float_sum = 0.1 + 0.2
a = Decimal(float_sum)
first_decimal = Decimal("0.1")
second_decimal = Decimal("0.2")
b = first_decimal + second_decimal
target = Decimal("0.3")

print("Float sum:", repr(float_sum))
print("Decimal made from that float:", a)
print("Decimal operands:", first_decimal, second_decimal)
print("Decimal sum:", b)
print("Exact equality:", a == target, b == target)
```

**Expected output — observed locally:**

```text
Float sum: 0.30000000000000004
Decimal made from that float: 0.3000000000000000444089209850062616169452667236328125
Decimal operands: 0.1 0.2
Decimal sum: 0.3
Exact equality: False True
```

**Follow the key lines:**

1. Python first evaluates `0.1 + 0.2` as float arithmetic. The intermediate print exposes `0.30000000000000004`.
2. `Decimal(float_sum)` converts that actual float value. The long decimal expansion shows the supplied binary approximation.
3. `Decimal("0.1")` and `Decimal("0.2")` read decimal text before arithmetic. Their sum is Decimal `0.3`.
4. The exact comparisons therefore produce `False True`. This example is about numeric representation; it does not define a rounding or currency policy.


---

## Set 2 - Q20: Upgrade compatible readers before enabling new writers (Medium)

**Original reference:** `Python-Pydantic-M-H-Set2`, question `20`.

V1 queue events carry `amount_cents: int`. V2 events carry `amount: Decimal` and `currency`. Old consumers reject V2. The queue cannot route messages according to consumer version, and consumers are upgraded gradually.

Which rollout avoids sending unsupported V2 events to old consumers?

A. Deploy consumers that validate both explicit versions and normalize them; confirm all readers are upgraded, then enable V2 producers.

B. Enable V2 producers first, then upgrade consumers after validation failures appear.

C. Rename `amount_cents` to `amount` in producers and rely on numeric coercion to interpret the changed meaning.

D. Set `extra="ignore"` on old consumers and assume they can interpret missing required fields and new units.

**Answer: A.**

**Why it works:** When any queue message can reach any consumer, every active reader must understand V2 before writers emit it. A compatible reader can accept both versions and convert them into one internal representation. Existing V1 events also still need their defined interpretation.

**Why the other choices fail:**

- **B:** A V2 message can reach an old consumer during the rollout and be rejected.
- **C:** Renaming a key or coercing a number does not define unit conversion or currency semantics.
- **D:** Ignoring unfamiliar keys neither supplies required old fields nor teaches the old consumer how to interpret the new format.

**Standalone Python example — tested locally; no API key required.** The example uses local sample messages and a simulated deployment inventory. The assumed legacy currency is USD, and legacy amounts are divided by 100 to convert cents into currency units. No queue or deployment API is contacted.

```python
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


class V1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    amount_cents: int


class V2(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[2]
    amount: Decimal
    currency: str


VersionedEvent = Annotated[V1 | V2, Field(discriminator="version")]
reader = TypeAdapter(VersionedEvent)


def normalize(payload):
    event = reader.validate_python(payload)
    if isinstance(event, V1):
        # Explicit demo contract: every legacy event is USD cents.
        return {"amount": Decimal(event.amount_cents) / Decimal("100"), "currency": "USD"}
    return {"amount": event.amount, "currency": event.currency}


legacy = {"version": 1, "amount_cents": 1250}
new = {"version": 2, "amount": "12.50", "currency": "USD"}
try:
    V1.model_validate(new)  # Simulates an old consumer receiving a V2 event.
except ValidationError:
    print("Old reader accepts V2:", False)

print("Compatible reader normalizes V1:", normalize(legacy))
print("Compatible reader normalizes V2:", normalize(new))

# Simulated deployment inventory; this does not inspect a real fleet.
for upgraded_readers, total_readers in [(1, 2), (2, 2)]:
    can_enable_v2 = upgraded_readers == total_readers
    print("Upgraded readers:", f"{upgraded_readers}/{total_readers}",
          "enable V2 producers:", can_enable_v2)
```

**Expected output — observed locally:**

```text
Old reader accepts V2: False
Compatible reader normalizes V1: {'amount': Decimal('12.5'), 'currency': 'USD'}
Compatible reader normalizes V2: {'amount': Decimal('12.50'), 'currency': 'USD'}
Upgraded readers: 1/2 enable V2 producers: False
Upgraded readers: 2/2 enable V2 producers: True
```

**Follow the key lines:**

1. `version` is an explicit literal tag. The adapter chooses V1 or V2 and validates that version's required fields.
2. The old-reader check validates V2 data against V1 only and rejects it. This locally demonstrates the incompatible message shape.
3. `normalize` makes one explicit assumption for the sample: every V1 amount is USD cents. `1250 / 100` becomes Decimal `12.5` USD. That rule is an application contract, not inferred by Pydantic.
4. V2 supplies decimal amount text and currency directly. Validation converts `"12.50"` to Decimal while keeping its stated currency.
5. The two printed deployment states are a simulation: one of two upgraded readers is insufficient; two of two permits enabling V2 producers under the question's assumptions.
6. This example tests local validation and normalization. It does not deploy consumers, inspect a shared queue, or prove a real rollout is complete. Keep V1 reader support while retained V1 events still require it.

---

## Set 3 - Q01: Validate a nested dictionary into a model (Easy)

**Original reference:** Pydantic-E-M-Set3, question 01.

An ingestion endpoint receives `{"owner": {"team": "search"}}`. `Owner` is a Pydantic model with the field `team: str`. `Job` is a Pydantic model with the field `owner: Owner`. After `job = Job.model_validate(payload)` succeeds, what is `job.owner`?

A. It remains a dictionary, so only `job.owner["team"]` works.

B. It is an `Owner` instance, and `job.owner.team` is `"search"`.

C. It is a JSON string containing the owner object.

D. Validation fails because nested dictionaries must be converted manually.

**Answer: B.**

**Why it works:** The `owner: Owner` annotation tells Pydantic to validate the nested dictionary using `Owner`. Successful validation stores an `Owner` instance, so attribute access works.

**Why the other choices fail:**

- **A:** The input starts as a dictionary, but validation constructs the nested model declared by the field.
- **C:** Validation builds Python objects here; it does not JSON-encode this field.
- **D:** Pydantic supports nested models directly, so this input needs no manual conversion.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel


class Owner(BaseModel):
    team: str


class Job(BaseModel):
    owner: Owner


payload = {"owner": {"team": "search"}}
print("input owner type:", type(payload["owner"]).__name__)
job = Job.model_validate(payload)
print("validated owner type:", type(job.owner).__name__)
print("team:", job.owner.team)
print("dump:", job.model_dump())
```

**Expected output — captured from the local run:**

```text
input owner type: dict
validated owner type: Owner
team: search
dump: {'owner': {'team': 'search'}}
```

**Follow the key lines:**

1. `payload["owner"]` is initially an ordinary dictionary. Its `team` value is the string `"search"`.
2. `Job.model_validate(payload)` reads the `owner` field and applies the `Owner` model to that nested value.
3. The resulting `job.owner` is an `Owner`. `job.owner.team` reads the validated team through an attribute.
4. `model_dump()` converts the model back to a dictionary representation, including a nested dictionary for the owner. That dump does not mean the stored `job.owner` was a dictionary.


---

## Set 3 - Q02: Read both numeric boundaries (Easy)

**Original reference:** Pydantic-E-M-Set3, question 02.

A Pydantic model declares `threshold: float = Field(gt=0, le=1)`, with no custom validators. The threshold must be strictly greater than zero and no greater than one. Which construction succeeds?

A. `Search(threshold=-0.1)`

B. `Search(threshold=0.0)`

C. `Search(threshold=1.0)`

D. `Search(threshold=1.01)`

**Answer: C.**

**Why it works:** `gt=0` excludes zero, while `le=1` includes one. The accepted interval is therefore greater than zero through one, including the upper endpoint.

**Why the other choices fail:**

- **A:** A negative value violates `gt=0`.
- **B:** Zero is excluded because `gt` means greater than, not greater than or equal to.
- **D:** A value above one violates `le=1`.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field, ValidationError


class Search(BaseModel):
    threshold: float = Field(gt=0, le=1)


for value in [-0.1, 0.0, 1.0, 1.01]:
    try:
        search = Search(threshold=value)
        print(value, "-> accepted:", search.threshold)
    except ValidationError as error:
        problem = error.errors()[0]
        print(value, "-> rejected:", problem["type"])
```

**Expected output — captured from the local run:**

```text
-0.1 -> rejected: greater_than
0.0 -> rejected: greater_than
1.0 -> accepted: 1.0
1.01 -> rejected: less_than_equal
```

**Follow the key lines:**

1. The list contains the four candidate inputs in choice order.
2. For each input, `Search(threshold=value)` applies both declared bounds. Passing one bound does not bypass the other.
3. Only `1.0` passes. Its value stays `1.0` on the validated model.
4. The `except` block catches the expected validation failures and prints their structured error types. The script continues so you can compare all four cases.


---

## Set 3 - Q03: Match an enum value exactly (Easy)

**Original reference:** Pydantic-E-M-Set3, question 03.

`Mode` is a `str, Enum` with members `QUICK = "quick"` and `FULL = "full"`. `Run` has the field `mode: Mode` and uses default Pydantic 2 configuration, without custom validators. Which statement is correct?

A. `Run(mode="quick").mode is Mode.QUICK`.

B. `Run(mode="QUICK").mode is Mode.QUICK`.

C. `Run(mode="Quick").mode is Mode.QUICK`.

D. `Run(mode="fast").mode is Mode.QUICK`.

**Answer: A.**

**Why it works:** The external value declared for `Mode.QUICK` is exactly `"quick"`. Pydantic accepts that value and stores the corresponding enum member under the stated default configuration.

**Why the other choices fail:**

- **B:** `QUICK` is the Python member name, not the declared external string value.
- **C:** Value matching does not automatically change capitalization.
- **D:** The enum does not define `"fast"` or infer it as a synonym.

**Standalone example — tested locally; no API key required.**

```python
from enum import Enum
from pydantic import BaseModel, ValidationError


class Mode(str, Enum):
    QUICK = "quick"
    FULL = "full"


class Run(BaseModel):
    mode: Mode


run = Run(mode="quick")
print("stored type:", type(run.mode).__name__)
print("member name:", run.mode.name)
print("member value:", run.mode.value)
print("is QUICK:", run.mode is Mode.QUICK)
for value in ["QUICK", "Quick", "fast"]:
    try:
        Run(mode=value)
    except ValidationError as error:
        print(repr(value), "->", error.errors()[0]["type"])
```

**Expected output — captured from the local run:**

```text
stored type: Mode
member name: QUICK
member value: quick
is QUICK: True
'QUICK' -> enum
'Quick' -> enum
'fast' -> enum
```

**Follow the key lines:**

1. `QUICK` is the member name used in Python; `"quick"` is its declared value. They are different strings.
2. `Run(mode="quick")` matches that value and stores `Mode.QUICK`, rather than storing an arbitrary unvalidated string.
3. The first four prints show the stored type, member name, value, and identity comparison separately.
4. The three alternative inputs do not match either declared enum value, so each produces an enum validation error.


---

## Set 3 - Q04: Separate a description from an enforced limit (Easy)

**Original reference:** Pydantic-E-M-Set3, question 04.

A model declares `limit: int = Field(description="Must be at most 100")`, with no other constraints or validators. What happens when `Request(limit=500)` is evaluated?

A. The model definition fails because descriptions cannot mention numeric rules.

B. It raises `ValidationError` because the description states an upper bound.

C. It succeeds after changing `limit` automatically to `100`.

D. It succeeds with `limit=500`; an actual constraint such as `le=100` is needed to enforce the bound.

**Answer: D.**

**Why it works:** A description is documentation metadata. Pydantic does not turn its English text into a validation rule. The field accepts `500` as an integer unless a real upper-bound constraint or validator is supplied.

**Why the other choices fail:**

- **A:** Descriptions can contain ordinary explanatory text, including a numeric rule.
- **B:** The description is not an executable upper-bound check.
- **C:** Nothing in this declaration clamps the value. Even `le=100` would reject `500`, rather than change it to `100`.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field, ValidationError


class Request(BaseModel):
    limit: int = Field(description="Must be at most 100")


class ConstrainedRequest(BaseModel):
    limit: int = Field(le=100, description="Must be at most 100")


request = Request(limit=500)
print("description-only value:", request.limit)
field_schema = Request.model_json_schema()["properties"]["limit"]
print("description:", field_schema["description"])
print("schema has maximum:", "maximum" in field_schema)
try:
    ConstrainedRequest(limit=500)
except ValidationError as error:
    print("with le=100:", error.errors()[0]["type"])
```

**Expected output — captured from the local run:**

```text
description-only value: 500
description: Must be at most 100
schema has maximum: False
with le=100: less_than_equal
```

**Follow the key lines:**

1. The first model has a description but no numeric bound. Its stored `limit` therefore remains `500`.
2. `model_json_schema()` shows where the description appears: it documents the field for schema consumers.
3. The description-only schema has no `maximum` rule, which the script checks explicitly.
4. The second model adds `le=100`, an actual validation constraint. Constructing it with `500` now raises the expected upper-bound error.


---

## Set 3 - Q05: Read fields from an object’s attributes (Easy)

**Original reference:** Pydantic-E-M-Set3, question 05.

A repository returns `record = SimpleNamespace(id=7)`, a Python object with an `id` attribute. `Item` is a Pydantic model declaring `id: int`. Which call reads that attribute and creates `Item` without manually building an input dictionary?

A. `Item.model_validate({"record": record})`

B. `Item.model_validate_json(record)`

C. `Item.model_validate(str(record))`

D. `Item.model_validate(record, from_attributes=True)`

**Answer: D.**

**Why it works:** `from_attributes=True` tells this validation call to read the declared field names from object attributes. It reads `record.id`, validates the integer, and stores it as `item.id`.

**Why the other choices fail:**

- **A:** The wrapper dictionary has a `record` key, but the model requires `id` at its input level.
- **B:** `model_validate_json` expects JSON text or supported bytes, not this object.
- **C:** The object’s display string is not a field mapping and does not request attribute-based validation.

**Standalone example — tested locally; no API key required.**

```python
from types import SimpleNamespace
from pydantic import BaseModel


class Item(BaseModel):
    id: int


record = SimpleNamespace(id=7)
print("input object type:", type(record).__name__)
print("input attribute:", record.id)
item = Item.model_validate(record, from_attributes=True)
print("validated type:", type(item).__name__)
print("validated id:", item.id)
print("dump:", item.model_dump())
```

**Expected output — captured from the local run:**

```text
input object type: SimpleNamespace
input attribute: 7
validated type: Item
validated id: 7
dump: {'id': 7}
```

**Follow the key lines:**

1. `SimpleNamespace(id=7)` creates a small local object with an `id` attribute. It is a stand-in for an object returned by a repository; no database is contacted.
2. `from_attributes=True` enables attribute lookup for this call to `model_validate`.
3. The model reads `record.id`, validates that value for its `id: int` field, and creates an `Item` instance.
4. The resulting `item.id` is `7`, and its dictionary dump contains the declared field `id`.


---

## Set 3 - Q06: Exclude a field from a dump without deleting it (Easy)

**Original reference:** Pydantic-E-M-Set3, question 06.

`Ticket` declares `title: str` and `internal_note: str = Field(exclude=True)`. After `t = Ticket(title="Index slow", internal_note="triage-42")`, which statement describes `t.model_dump()` and the stored instance?

A. Validation fails because an excluded field cannot receive input.

B. The dump contains both fields; `exclude=True` affects only the printed representation.

C. The dump contains only `title`, and `t.internal_note` remains accessible.

D. Validation accepts the note and then immediately discards it from the instance.

**Answer: C.**

**Why it works:** `Field(exclude=True)` excludes the field from serialization. It still accepts, validates, and stores the supplied value on the model.

**Why the other choices fail:**

- **A:** Serialization exclusion is not a rule that forbids input.
- **B:** This option directly affects dumps; it is not merely a representation setting.
- **D:** The note remains stored. Omitting it from a dump does not erase the Python attribute.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, Field


class Ticket(BaseModel):
    title: str
    internal_note: str = Field(exclude=True)


t = Ticket(title="Index slow", internal_note="triage-42")
print("stored title:", t.title)
print("stored note:", t.internal_note)
print("default dump:", t.model_dump())
print("note in dump:", "internal_note" in t.model_dump())
```

**Expected output — captured from the local run:**

```text
stored title: Index slow
stored note: triage-42
default dump: {'title': 'Index slow'}
note in dump: False
```

**Follow the key lines:**

1. Both supplied values are validated against their string fields during construction.
2. `t.internal_note` reads the stored note normally; serialization exclusion does not remove that attribute.
3. `model_dump()` includes `title` and omits `internal_note` because of the field’s exclusion setting.
4. The final membership check prints `False` for the output dictionary, while the earlier print confirms the note still exists on the instance.


---

## Set 3 - Q07: Know what HTTP URL validation proves (Easy)

**Original reference:** Pydantic-E-M-Set3, question 07.

A webhook model declares `endpoint: HttpUrl` with no custom validators. Its construction succeeds for `"https://example.invalid/hook"`. What does this successful validation establish?

A. Pydantic contacted the endpoint and received HTTP 200.

B. The value meets the HTTP URL type requirements; delivery requires a separate network operation.

C. Pydantic confirmed that the endpoint belongs to the submitting customer.

D. The same type accepts FTP URLs whenever they include a host and scheme.

**Answer: B.**

**Why it works:** `HttpUrl` validates the URL value and permits HTTP or HTTPS schemes. This is parsing and validation, not a webhook delivery attempt or ownership check.

**Why the other choices fail:**

- **A:** Constructing this model sends no HTTP request and obtains no response status.
- **C:** A syntactically acceptable URL does not demonstrate ownership.
- **D:** `HttpUrl` rejects the FTP scheme even if the URL contains a host.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, HttpUrl, ValidationError


class Webhook(BaseModel):
    endpoint: HttpUrl


# Local validation only. This example makes no network requests.
hook = Webhook(endpoint="https://example.invalid/hook")
print("stored URL:", str(hook.endpoint))
print("scheme:", hook.endpoint.scheme)
print("host:", hook.endpoint.host)
try:
    Webhook(endpoint="ftp://example.invalid/hook")
except ValidationError as error:
    print("FTP rejected:", error.errors()[0]["type"])
```

**Expected output — captured from the local run:**

```text
stored URL: https://example.invalid/hook
scheme: https
host: example.invalid
FTP rejected: url_scheme
```

**Follow the key lines:**

1. The HTTPS input is fixed sample data. No HTTP client or other delivery function is called.
2. `Webhook(...)` parses the value into a `HttpUrl` object. Its `scheme` and `host` attributes show the parsed parts.
3. The parsed HTTPS URL is accepted even though the script never checks whether a server exists there.
4. The FTP candidate produces a scheme validation error. Validation checks the allowed URL type, while delivery and ownership require separate work.


---

## Set 3 - Q08: Include a computed property in output (Easy)

**Original reference:** Pydantic-E-M-Set3, question 08.

`Usage` declares `tokens_in: int` and `tokens_out: int`. Its property `total` returns `self.tokens_in + self.tokens_out` and is decorated with `@computed_field` above `@property`. With default dumping options, what does `Usage(tokens_in=3, tokens_out=5).model_dump()` return?

A. `{"tokens_in": 3, "tokens_out": 5, "total": 8}`

B. `{"tokens_in": 3, "tokens_out": 5}`

C. `{"total": 8}`

D. It raises `ValidationError` because `total` was not supplied.

**Answer: A.**

**Why it works:** `computed_field` includes this property in serialization. The stored input fields remain in the dump, and the property derives `8` from their values.

**Why the other choices fail:**

- **B:** The decorator explicitly includes the computed property in the ordinary dump.
- **C:** Adding a computed field does not exclude the two declared input fields.
- **D:** The property computes its value; it is not a required input field.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, computed_field


class Usage(BaseModel):
    tokens_in: int
    tokens_out: int

    @computed_field
    @property
    def total(self) -> int:
        return self.tokens_in + self.tokens_out


usage = Usage(tokens_in=3, tokens_out=5)
print("stored inputs:", usage.tokens_in, usage.tokens_out)
print("computed total:", usage.total)
print("dump:", usage.model_dump())
```

**Expected output — captured from the local run:**

```text
stored inputs: 3 5
computed total: 8
dump: {'tokens_in': 3, 'tokens_out': 5, 'total': 8}
```

**Follow the key lines:**

1. Construction supplies only the two measurements, `3` and `5`.
2. Accessing `usage.total` evaluates the property using those values and returns `8`.
3. `@computed_field` tells Pydantic to include the property in serialization. `@property` provides ordinary property access in Python.
4. The dump contains the two stored inputs and their derived sum. No separate `total` argument is needed.


---

## Set 3 - Q09: Retrieve a SecretStr explicitly (Easy)

**Original reference:** Pydantic-E-M-Set3, question 09.

A model has a `token: SecretStr` field. A client library needs the original token string. Which operation retrieves it, and what does that imply about `SecretStr`?

A. Use `token.decrypt()`; `SecretStr` encrypts the string using an automatically managed key.

B. Use `str(token)`; it reveals the original string only to authenticated callers.

C. Use `token.get_secret_value()`; `SecretStr` masks common displays but is not encryption.

D. The original is unrecoverable because `SecretStr` stores only a one-way hash.

**Answer: C.**

**Why it works:** `get_secret_value()` returns the stored string. `SecretStr` masks its common string display and default JSON representation; it does not encrypt or hash away the original value.

**Why the other choices fail:**

- **A:** `SecretStr` does not provide this automatic encryption system or a `decrypt()` method.
- **B:** `str(token)` gives a masked display. It does not authenticate callers to decide what to show.
- **D:** The original string is recoverable through the explicit accessor, so it is not stored only as a one-way hash.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, SecretStr


class Credentials(BaseModel):
    token: SecretStr


# Invented sample token only; this is not a real credential.
credentials = Credentials(token="demo-token")
print("stored type:", type(credentials.token).__name__)
print("string display:", str(credentials.token))
print("JSON display:", credentials.model_dump_json())
raw_token = credentials.token.get_secret_value()
print("explicit sample value:", raw_token)
print("retrieved type:", type(raw_token).__name__)
```

**Expected output — captured from the local run:**

```text
stored type: SecretStr
string display: **********
JSON display: {"token":"**********"}
explicit sample value: demo-token
retrieved type: str
```

**Follow the key lines:**

1. The example deliberately uses an invented string, `"demo-token"`, so its unmasked value is safe to inspect here.
2. Pydantic stores a `SecretStr` object. Its ordinary string display is masked.
3. The default JSON dump also contains a masked token. That is output formatting, not evidence of encrypted storage.
4. `get_secret_value()` explicitly retrieves the original Python string. A real application should pass that raw value only where it is needed; do not copy this sample print for real credentials.


---

## Set 3 - Q10: Inspect all independent field errors (Easy)

**Original reference:** Pydantic-E-M-Set3, question 10.

`Batch` declares the independent fields `size: int` and `retries: int`, with no custom validators. The form supplies `size="many"` and `retries="several"`. What should the caller expect when constructing `Batch`?

A. One `ValidationError` containing two field errors, inspectable with `errors()` or `error_count()`.

B. Two separate exceptions raised simultaneously, one for each field.

C. One error for `size` only, because Pydantic never checks another field after a failure.

D. No error, because both nonnumeric strings become zero.

**Answer: A.**

**Why it works:** These two integer fields fail independently. Pydantic reports both problems inside one `ValidationError`, so the caller can inspect their count and locations together.

**Why the other choices fail:**

- **B:** One validation attempt raises one aggregate `ValidationError` object here, containing multiple error entries.
- **C:** The first failure does not prevent collection of the second independent field error in this model.
- **D:** Neither string can be parsed as an integer, and no fallback-to-zero rule is declared.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, ValidationError


class Batch(BaseModel):
    size: int
    retries: int


payload = {"size": "many", "retries": "several"}
print("input:", payload)
try:
    Batch.model_validate(payload)
except ValidationError as error:
    print("exception type:", type(error).__name__)
    print("error count:", error.error_count())
    for problem in error.errors():
        print("location:", problem["loc"], "type:", problem["type"])
```

**Expected output — captured from the local run:**

```text
input: {'size': 'many', 'retries': 'several'}
exception type: ValidationError
error count: 2
location: ('size',) type: int_parsing
location: ('retries',) type: int_parsing
```

**Follow the key lines:**

1. The dictionary contains two values that cannot be parsed as integers.
2. `model_validate(payload)` attempts validation of the declared fields and raises one `ValidationError` for this input.
3. `error_count()` returns `2`, the number of field failures contained in that exception.
4. `errors()` returns structured entries. The `loc` tuples identify `size` and `retries`, while `int_parsing` identifies the failed conversion for each.

---

## Set 3 - Q11: Generate a default only when the field is omitted (Medium)

**Original reference:** Pydantic-E-M-Set3, question 11.

A fresh `itertools.count(100)` counter supplies IDs. A model field is declared as `id: int = Field(default_factory=lambda: next(ids))`, where `ids` is that counter. In order, the code creates `a = Request()`, `b = Request(id=999)`, and `c = Request()`. There are no custom validators or other counter consumers. What are `a.id`, `b.id`, and `c.id`?

A. `100, 999, 102`

B. `100, 999, 101`

C. `100, 999, 100`

D. `101, 999, 102`

**Answer: B.**

**Why it works:** The factory runs only when this field needs its default. Creating `a` consumes `100`. Supplying `999` for `b` bypasses the factory. Creating `c` therefore consumes `101`.

**Why the other choices fail:**

- **A:** It incorrectly counts the explicit value for `b` as another factory call.
- **C:** The callable runs again for `c`; its first result is not reused as a constant.
- **D:** Defining the model stores the callable without advancing the counter. Its first generated value is `100`.

**Standalone example — tested locally; no API key required.**

```python
from itertools import count
from pydantic import BaseModel, Field

ids = count(100)
factory_calls = []

def generate_id():
    value = next(ids)
    factory_calls.append(value)
    print("factory generated:", value)
    return value

class Request(BaseModel):
    id: int = Field(default_factory=generate_id)

print("factory calls after class definition:", factory_calls)
a = Request()
b = Request(id=999)
c = Request()
print("IDs:", a.id, b.id, c.id)
print("factory calls:", factory_calls)
```

**Expected output — observed locally:**

```text
factory calls after class definition: []
factory generated: 100
factory generated: 101
IDs: 100 999 101
factory calls: [100, 101]
```

**Follow the key lines:**

1. `count(100)` produces `100`, then `101`, then `102` when asked. Creating the counter does not consume a value.
2. `default_factory=generate_id` passes a function, without calling it at class definition. This named function does the same work as the question's lambda and adds diagnostic prints.
3. `Request()` has no ID input, so the factory supplies one. `Request(id=999)` already has an ID and does not call the factory.
4. The recorded calls are `[100, 101]`, making the two default-generation events visible. The three model IDs are `100`, `999`, and `101`.


---

## Set 3 - Q12: Constrain the list and each item separately (Medium)

**Original reference:** Pydantic-E-M-Set3, question 12.

A request must contain **one to three tags**, and **each tag must have at most eight characters**. No defaults or custom validators are present. The item type is `Tag = Annotated[str, Field(max_length=8)]`. Which field declaration enforces both rules?

A. `tags: list[Tag] = Field(min_length=1, max_length=8)`

B. `tags: list[str] = Field(min_length=1, max_length=3)`

C. `tags: list[Tag] = Field(max_length=3)`

D. `tags: list[Tag] = Field(min_length=1, max_length=3)`

**Answer: D.**

**Why it works:** The annotation on `Tag` checks each string. The `Field` on `tags` counts list items. Combining them checks both levels of the input.

**Why the other choices fail:**

- **A:** It allows up to eight tags, exceeding the requested maximum of three.
- **B:** It counts the tags but does not limit the length of each string.
- **C:** It imposes the item and upper-count limits, but accepts an empty list.

**Standalone example — tested locally; no API key required.**

```python
from typing import Annotated
from pydantic import BaseModel, Field, ValidationError

Tag = Annotated[str, Field(max_length=8)]

class Request(BaseModel):
    tags: list[Tag] = Field(min_length=1, max_length=3)

samples = [
    ["alpha", "beta"],
    [],
    ["a", "b", "c", "d"],
    ["123456789"],
]
for tags in samples:
    print("input:", tags, "count:", len(tags))
    try:
        request = Request(tags=tags)
        print("accepted:", request.tags)
    except ValidationError as error:
        first = error.errors()[0]
        print("rejected:", first["loc"], first["type"])
```

**Expected output — observed locally:**

```text
input: ['alpha', 'beta'] count: 2
accepted: ['alpha', 'beta']
input: [] count: 0
rejected: ('tags',) too_short
input: ['a', 'b', 'c', 'd'] count: 4
rejected: ('tags',) too_long
input: ['123456789'] count: 1
rejected: ('tags', 0) string_too_long
```

**Follow the key lines:**

1. `Tag` is a string type with its own eight-character limit. It is the type used for each element of the list.
2. `min_length=1, max_length=3` on the list field counts elements, not characters.
3. The two-tag input passes both checks. The empty and four-tag inputs fail the list-size check, so their error location is just `('tags',)`.
4. The final input has an acceptable list count of one, but its first tag has nine characters. Its location `('tags', 0)` identifies that element using a zero-based index.


---

## Set 3 - Q13: Return the normalized value from a validator (Medium)

**Original reference:** Pydantic-E-M-Set3, question 13.

A `User` model has `name: str`. Its after field validator currently ends with `value.strip()` and has **no return statement**. The input is `"  Jay  "`, and the intended stored value is `"Jay"`. What is the direct correction to that final line?

A. Use `return value.strip()`.

B. Leave it unchanged because `str.strip()` mutates the original string.

C. Use `return True` to signal that validation succeeded.

D. Leave it unchanged and make the input field strict.

**Answer: A.**

**Why it works:** A field validator returns the value that should be stored. `strip()` creates the cleaned string, so that new string must be returned.

**Why the other choices fail:**

- **B:** Strings are immutable. Calling `strip()` without keeping its result does not normalize the input.
- **C:** The returned object becomes the field value; `True` is not a separate success flag.
- **D:** Strict input checking cannot supply a missing return statement.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, field_validator

class BrokenUser(BaseModel):
    name: str

    @field_validator("name", mode="after")
    @classmethod
    def normalize(cls, value: str):
        value.strip()  # Intentionally broken: the function returns None.

class User(BaseModel):
    name: str

    @field_validator("name", mode="after")
    @classmethod
    def normalize(cls, value: str) -> str:
        cleaned = value.strip()
        print("validator received:", repr(value))
        print("validator returns:", repr(cleaned))
        return cleaned

raw = "  Jay  "
print("broken stored value:", repr(BrokenUser(name=raw).name))
user = User(name=raw)
print("corrected stored value:", repr(user.name))
print("original string:", repr(raw))
```

**Expected output — observed locally:**

```text
broken stored value: None
validator received: '  Jay  '
validator returns: 'Jay'
corrected stored value: 'Jay'
original string: '  Jay  '
```

**Follow the key lines:**

1. The deliberately broken method reaches its end without a `return`, so ordinary Python returns `None`. The observed broken model therefore stores `None`; do not assume the after-validator result is automatically rechecked against `str`.
2. The corrected validator first receives a validated string. `value.strip()` produces a new string with its surrounding spaces removed.
3. `return cleaned` is equivalent to `return value.strip()`. It gives Pydantic the actual value to retain.
4. `repr(...)` displays quotation marks and spaces clearly. The model stores `'Jay'`, while the original immutable string remains `'  Jay  '`.


---

## Set 3 - Q14: Format output without changing the stored integer (Medium)

**Original reference:** Pydantic-E-M-Set3, question 14.

A model declares `count: int` and a field serializer for `count` that returns `f"{value:,}"`, annotated to return `str`. The serializer uses its default settings. After `v = Volume(count=1200)`, what are the value and type of `v.count` and `v.model_dump()["count"]`?

A. Model creation fails because the serializer returns a different type.

B. `v.count` is the string `"1,200"`; the dumped value is also that string.

C. `v.count` is the integer `1200`; the dumped value is also that integer.

D. `v.count` is the integer `1200`; the dumped value is the string `"1,200"`.

**Answer: D.**

**Why it works:** The serializer creates an output representation when the model is dumped. It does not assign the formatted representation back to the model attribute.

**Why the other choices fail:**

- **A:** A serializer can intentionally return a representation whose type differs from the internal field type.
- **B:** Serialization does not replace the stored integer with its formatted text.
- **C:** The custom serializer runs during this dump, so its string replaces the default integer output.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, field_serializer

class Volume(BaseModel):
    count: int

    @field_serializer("count")
    def display(self, value: int) -> str:
        return f"{value:,}"

v = Volume(count=1200)
print("stored before dump:", v.count, type(v.count).__name__)
dumped = v.model_dump()
print("dump:", dumped)
print("dumped field:", repr(dumped["count"]), type(dumped["count"]).__name__)
print("stored after dump:", v.count, type(v.count).__name__)
```

**Expected output — observed locally:**

```text
stored before dump: 1200 int
dump: {'count': '1,200'}
dumped field: '1,200' str
stored after dump: 1200 int
```

**Follow the key lines:**

1. `count: int` describes the internal field. The supplied integer `1200` is stored as an integer.
2. `@field_serializer("count")` attaches `display` to output serialization of that field. `f"{value:,}"` inserts a thousands separator and returns text.
3. `model_dump()` calls the serializer and puts its returned string under `count` in the new dictionary.
4. The before-and-after prints both show `1200 int`. Formatting the dump did not change the internal value.


---

## Set 3 - Q15: Keep internal instance data in a private attribute (Medium)

**Original reference:** Pydantic-E-M-Set3, question 15.

A `Query` model has a normal field `text: str` and `_memo: dict[str, int] = PrivateAttr(default_factory=dict)`. After `q = Query(text="latency")` and `q._memo["hits"] = 4`, which statement is correct under default Pydantic settings?

A. `q.model_dump()` includes `_memo` because its type annotation is explicit.

B. `q._memo` contains the memo, but the ordinary dump and model field schema omit `_memo`.

C. Assigning a string to `q._memo["hits"]` automatically raises `ValidationError`.

D. The memo is one class-level dictionary shared by every `Query` instance.

**Answer: B.**

**Why it works:** `PrivateAttr` stores internal instance data outside the normal model fields. It remains accessible in Python but is not included as a public model field in ordinary serialization or JSON Schema.

**Why the other choices fail:**

- **A:** A private-attribute annotation does not turn it into a normal serialized field.
- **C:** Private attributes do not automatically validate later dictionary mutations.
- **D:** The factory creates a new dictionary for each instance.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, PrivateAttr

class Query(BaseModel):
    text: str
    _memo: dict[str, int] = PrivateAttr(default_factory=dict)

q = Query(text="latency")
q._memo["hits"] = 4
other = Query(text="throughput")
print("first memo:", q._memo)
print("second memo:", other._memo)
print("same dictionary:", q._memo is other._memo)
print("dump:", q.model_dump())
print("schema fields:", list(Query.model_json_schema()["properties"]))
```

**Expected output — observed locally:**

```text
first memo: {'hits': 4}
second memo: {}
same dictionary: False
dump: {'text': 'latency'}
schema fields: ['text']
```

**Follow the key lines:**

1. `text` is an ordinary model field. `_memo` is explicitly declared as private instance data.
2. `default_factory=dict` calls `dict()` for each new instance. Updating `q._memo` therefore leaves `other._memo` empty.
3. `q.model_dump()` returns only the normal `text` field. The memo still exists on `q`; omission from a dump does not erase it.
4. `model_json_schema()["properties"]` lists normal public fields, so it lists `text` and omits `_memo`. The annotation on the private dictionary does not automatically enforce types when its contents change.


---

## Set 3 - Q16: Validate function arguments before running the body (Medium)

**Original reference:** Pydantic-E-M-Set3, question 16.

A fresh list `events = []` records side effects. A function decorated with `@validate_call` has parameter `count: int`; its body appends `count` to `events`. There are no custom validators or defaults. The caller invokes `record("many")` and catches its exception. What is in `events` immediately afterward?

A. `[None]`, because an invalid integer is replaced with `None`.

B. `["many"]`, because argument validation occurs after the body.

C. `[]`, because argument validation fails before the body runs.

D. `[0]`, because the decorator supplies zero for an invalid integer.

**Answer: C.**

**Why it works:** `validate_call` validates the arguments before entering the function body. The string `"many"` cannot be parsed as an integer, so a `ValidationError` is raised before any append occurs.

**Why the other choices fail:**

- **A:** Validation reports the invalid value instead of silently substituting `None`.
- **B:** The invalid argument is rejected before execution, not after the body runs.
- **D:** No numeric fallback has been declared, and the decorator does not invent one.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import ValidationError, validate_call

events = []

@validate_call
def record(count: int):
    print("body receives:", count, type(count).__name__)
    events.append(count)

try:
    record("many")
except ValidationError as error:
    first = error.errors()[0]
    print("rejected argument:", first["loc"], first["type"])
print("events after invalid call:", events)

record("3")
print("events after valid call:", events)
```

**Expected output — observed locally:**

```text
rejected argument: (0,) int_parsing
events after invalid call: []
body receives: 3 int
events after valid call: [3]
```

**Follow the key lines:**

1. The decorator wraps `record`. Calling the wrapped function first sends its annotated arguments through validation.
2. `record("many")` fails integer parsing. The location `(0,)` refers to the first positional argument, and no `body receives` line appears for that call.
3. The caller catches the validation error, then prints the still-empty `events` list.
4. The second call uses `"3"`, which can be parsed as an integer under the default settings. The body receives `3 int` and appends that integer. This second call is only a contrast with the rejected input.


---

## Set 3 - Q17: Serialize a root list as a top-level JSON array (Medium)

**Original reference:** Pydantic-E-M-Set3, question 17.

A model is defined as `class Names(RootModel[list[str]]): pass`. It validates `["alpha", "beta"]` as its root value. An integration needs JSON text whose top-level value is an array, without an enclosing object. What does `names.model_dump_json()` return? Each option describes the **returned JSON string's contents**, not a Python list object.

A. JSON text `'["alpha","beta"]'`.

B. JSON text `'{"root":["alpha","beta"]}'`.

C. JSON text `'{"Names":["alpha","beta"]}'`.

D. It raises an error because every Pydantic model must serialize as a JSON object.

**Answer: A.**

**Why it works:** `RootModel` serializes its root value directly. A list root becomes a top-level JSON array. The method returns a Python `str` containing that JSON text.

**Why the other choices fail:**

- **B:** The Python attribute is named `root`, but that name does not become a serialization wrapper.
- **C:** The Python class name does not become an enclosing JSON object key.
- **D:** Root models can represent and serialize supported top-level values such as lists.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import RootModel

class Names(RootModel[list[str]]):
    pass

names = Names.model_validate(["alpha", "beta"])
print("root value:", names.root)
print("Python dump:", names.model_dump())
json_text = names.model_dump_json()
print("JSON text:", json_text)
print("JSON return type:", type(json_text).__name__)
```

**Expected output — observed locally:**

```text
root value: ['alpha', 'beta']
Python dump: ['alpha', 'beta']
JSON text: ["alpha","beta"]
JSON return type: str
```

**Follow the key lines:**

1. `RootModel[list[str]]` says that the model represents one list value rather than a collection of named fields.
2. `names.root` gives Python code access to that list. `model_dump()` also returns the underlying list without a `root` wrapper.
3. `model_dump_json()` JSON-encodes the list, producing the text `["alpha","beta"]`.
4. The final `str` print separates the Python return type from the shape described by its contents: it is a string containing a JSON array.


---

## Set 3 - Q18: Preserve an exact string match in a smart union (Medium)

**Original reference:** Pydantic-E-M-Set3, question 18.

A model declares `key: int | str` and uses default Pydantic 2 union behavior, with no custom validators or union-mode changes. What are the value and Python type of `Ref(key="007").key`?

A. `"7"`, a `str`.

B. `7`, an `int`.

C. `"007"`, a `str`.

D. Validation fails because both union members can accept the input.

**Answer: C.**

**Why it works:** The input is already a string, so it exactly matches the string branch. That match takes priority over parsing it into an integer for this union. Its leading zeros remain intact.

**Why the other choices fail:**

- **A:** The exact string match does not first parse the value as an integer and remove its zeros.
- **B:** Putting `int` first does not force coercion when the string branch has an exact match.
- **D:** More than one potentially accepting branch does not itself make a union invalid; the union selects an appropriate match.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel

class Ref(BaseModel):
    key: int | str

for raw in ["007", 7]:
    ref = Ref(key=raw)
    print("input:", repr(raw), type(raw).__name__)
    print("stored:", repr(ref.key), type(ref.key).__name__)
```

**Expected output — observed locally:**

```text
input: '007' str
stored: '007' str
input: 7 int
stored: 7 int
```

**Follow the key lines:**

1. The two annotations describe the types that this field can store. Default smart-union matching considers the kind of match, not just the member order.
2. For the input `"007"`, the string branch accepts the value directly. The stored value remains `'007' str`.
3. For the integer input `7`, the integer branch is an exact match, so the stored value is `7 int`.
4. `repr(...)` makes a string's quotes visible, so a numeric-looking string is easy to distinguish from an integer.


---

## Set 3 - Q19: Decode JSON text inside one field, then validate its items (Medium)

**Original reference:** Pydantic-E-M-Set3, question 19.

A model declares `values: Json[list[int]]`. The surrounding input is already a Python object, but this particular field arrives as the JSON string `'[1, "2"]'`. Under default Pydantic 2 settings and no custom validators, what is stored in `Payload(values='[1, "2"]').values`?

A. Validation fails because `Json[list[int]]` requires an already-decoded Python list.

B. The original string `'[1, "2"]'`.

C. The Python list `[1, "2"]`.

D. The Python list `[1, 2]`.

**Answer: D.**

**Why it works:** `Json` first decodes the field's JSON text. The inner `list[int]` then validates the decoded list, parsing the numeric string `"2"` into integer `2`. The stored value is a Python list of integers.

**Why the other choices fail:**

- **A:** `Json[T]` is used for encoded JSON input; it decodes that input before validating it as `T`.
- **B:** Successful validation stores the decoded and validated result, not the encoded text.
- **C:** That is the intermediate decoded list; integer-item validation still converts its second element.

**Standalone example — tested locally; no API key required.**

```python
import json
from pydantic import BaseModel, Json

class Payload(BaseModel):
    values: Json[list[int]]

raw = '[1, "2"]'
print("field input:", repr(raw), type(raw).__name__)
print("JSON decoding alone:", json.loads(raw))
p = Payload(values=raw)
print("stored field:", p.values)
print("stored item types:", [type(item).__name__ for item in p.values])
```

**Expected output — observed locally:**

```text
field input: '[1, "2"]' str
JSON decoding alone: [1, '2']
stored field: [1, 2]
stored item types: ['int', 'int']
```

**Follow the key lines:**

1. `raw` is a Python string containing JSON text for one field. It is not an already-decoded list.
2. `json.loads(raw)` is printed only to show the decoding stage: `[1, '2']`. That operation alone leaves the second value as a string.
3. `Payload(values=raw)` gives the original text to `Json[list[int]]`. Pydantic decodes it and then validates every decoded element as an integer.
4. The stored result is `[1, 2]`, and both item types are `int`. No API call or external data source is involved.


---

## Set 3 - Q20: Reject non-finite floating-point values (Medium)

**Original reference:** Pydantic-E-M-Set3, question 20.

A metrics exporter must reject `float("nan")`, `float("inf")`, and `float("-inf")`, while accepting an ordinary finite float such as `1.25`. Use default Pydantic 2 configuration with no custom validators. Which declaration directly expresses this finite-value requirement?

A. `latency: float`

B. `latency: FiniteFloat`

C. `latency: StrictFloat`

D. `latency: float | None`

**Answer: B.**

**Why it works:** `FiniteFloat` excludes NaN and both infinities. Input strictness and finite magnitude are different requirements: a non-finite value can already be a genuine Python float.

**Why the other choices fail:**

- **A:** A plain float field accepts these non-finite Python floats by default.
- **C:** Strictness alone does not impose a finite-value constraint on an existing float.
- **D:** Allowing `None` adds a possible value; it does not exclude non-finite floats.

**Standalone example — tested locally; no API key required.**

```python
from pydantic import BaseModel, FiniteFloat, StrictFloat, ValidationError

class Measurement(BaseModel):
    latency: FiniteFloat

class StrictMeasurement(BaseModel):
    latency: StrictFloat

samples = [1.25, float("nan"), float("inf"), float("-inf")]
for value in samples:
    print("input:", value)
    try:
        print("FiniteFloat accepted:", Measurement(latency=value).latency)
    except ValidationError as error:
        first = error.errors()[0]
        print("FiniteFloat rejected:", first["loc"], first["type"])
    print("StrictFloat accepted:", StrictMeasurement(latency=value).latency)
```

**Expected output — observed locally:**

```text
input: 1.25
FiniteFloat accepted: 1.25
StrictFloat accepted: 1.25
input: nan
FiniteFloat rejected: ('latency',) finite_number
StrictFloat accepted: nan
input: inf
FiniteFloat rejected: ('latency',) finite_number
StrictFloat accepted: inf
input: -inf
FiniteFloat rejected: ('latency',) finite_number
StrictFloat accepted: -inf
```

**Follow the key lines:**

1. All four inputs are already Python floats. Only the first, `1.25`, is finite.
2. `Measurement` uses `FiniteFloat`, so `1.25` passes while the other three inputs produce the stable error type `finite_number`.
3. The caught errors let the loop continue through every test input. Their location `('latency',)` identifies the rejected field.
4. `StrictMeasurement` accepts all four float inputs in the tested version. That observed behavior shows why strict input typing alone cannot enforce this exporter's finite-number rule.

---

## Official API references

These references were checked alongside the locally executed examples. Outputs above were captured from the examples in this file. Documentation describes the contracts; the small simulations do not establish production performance or deployment behavior.

| Questions or behavior | Official reference |
| --- | --- |
| Set 1 Q01, Q05: defaults and callbacks | [Python control flow and default arguments](https://docs.python.org/3.12/tutorial/controlflow.html#default-argument-values) |
| Set 1 Q04, Q06: consuming iterators and strict zip | [Python built-in functions](https://docs.python.org/3.12/library/functions.html#zip) |
| Set 1 Q07; Set 2 Q17: annotations and runtime validation | [Python typing](https://docs.python.org/3.12/library/typing.html#typing.TypedDict) |
| Set 1 Q08–Q10: exception propagation and cleanup | [Python errors and exceptions](https://docs.python.org/3.12/tutorial/errors.html) |
| Set 2 Q01, Q08: local locks and semaphores | [Asyncio synchronization primitives](https://docs.python.org/3.12/library/asyncio-sync.html) |
| Set 2 Q02–Q04, Q06–Q07: task groups, cancellation, timeouts, threads, context | [Asyncio coroutines and tasks](https://docs.python.org/3.12/library/asyncio-task.html) |
| Set 2 Q05: producer backpressure | [Asyncio queues](https://docs.python.org/3.12/library/asyncio-queue.html) |
| Set 2 Q06, Q09: running threads and process pools | [Concurrent futures](https://docs.python.org/3.12/library/concurrent.futures.html) |
| Set 2 Q07: context-local bindings | [Context variables](https://docs.python.org/3.12/library/contextvars.html) |
| Set 2 Q10: async generator cleanup | [Contextlib and aclosing](https://docs.python.org/3.12/library/contextlib.html#contextlib.aclosing) |
| Set 2 Q19: decimal input and binary-float conversion | [Decimal arithmetic](https://docs.python.org/3.12/library/decimal.html) |
| Set 1 Q11, Q13; Set 3 Q02, Q04, Q08, Q11–Q12: fields and constraints | [Pydantic fields](https://docs.pydantic.dev/latest/concepts/fields/) |
| Set 1 Q12; Set 2 Q13: strict validation and input mode | [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) |
| Set 1 Q14; Set 2 Q14–Q15: extras, freezing, revalidation | [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/) |
| Set 1 Q15–Q16; Set 2 Q18; Set 3 Q13: validators and context | [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/) |
| Set 1 Q17–Q18; Set 2 Q16; Set 3 Q06, Q14: serialization | [Pydantic serialization](https://docs.pydantic.dev/latest/concepts/serialization/) |
| Set 1 Q19: separate input and output names | [Pydantic aliases](https://docs.pydantic.dev/latest/concepts/alias/) |
| Set 1 Q20; Set 3 Q10: structured validation errors | [Pydantic error handling](https://docs.pydantic.dev/latest/errors/errors/) |
| Set 2 Q11, Q20; Set 3 Q18: tagged and smart unions | [Pydantic unions](https://docs.pydantic.dev/latest/concepts/unions/) |
| Set 2 Q12: copying with unvalidated updates | [Pydantic BaseModel API](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_copy) |
| Set 2 Q17: validating a collection directly | [Pydantic TypeAdapter](https://docs.pydantic.dev/latest/concepts/type_adapter/) |
| Set 3 Q01, Q05, Q15, Q17: nested models, attributes, private state, root models | [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/) |
| Set 3 Q09, Q19–Q20: SecretStr, Json, finite numeric types | [Pydantic types](https://docs.pydantic.dev/latest/api/types/) |
| Set 3 Q16: validation before a function body runs | [Pydantic validation decorator](https://docs.pydantic.dev/latest/concepts/validation_decorator/) |
