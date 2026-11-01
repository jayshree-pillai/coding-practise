# FastAPI + Requests Crash Course

Practical, coding-first preparation for FDE technical interviews. Each concept builds on the previous discussion. Python snippets are kept as discussed.

## 1. The HTTP request–response cycle

Start by creating an endpoint with FastAPI, then call it using Requests.

- **FastAPI:** build an API that receives requests and returns responses.
- **Requests:** call an API and read its response.
- **Endpoint:** an HTTP method plus a path, such as `GET /health`.

### Build the API: `main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

`app = FastAPI()` creates the application. The decorator registers `health()` as the handler for `GET /health`. When a request arrives, FastAPI calls the function and turns its returned dictionary into JSON. The default success status is `200`.

Install and run:

```bash
python -m pip install "fastapi[standard]" requests
fastapi dev main.py
```

The server runs at `http://127.0.0.1:8000`: your own computer, port `8000`. Keep that terminal running.

### Call the API: `client.py`

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/health",
    timeout=5,
)

response.raise_for_status()

data = response.json()

print(response.status_code)  # 200
print(data["status"])        # ok
```

Run in a second terminal:

```bash
python client.py
```

| Expression | Meaning |
| --- | --- |
| `requests.get(...)` | Send a GET request and return a `Response` object. |
| `timeout=5` | Set connection/read timeouts; this is not a total request deadline. |
| `response.raise_for_status()` | Raise an exception for HTTP `4xx` or `5xx`. |
| `response.json()` | Parse the response body as JSON. |

Requests has no timeout by default. Always set one.

Successfully parsing JSON does not prove the HTTP request succeeded: a `500` response can also contain valid JSON.

**Practice:** add `GET /version`, return `{"version": "1.0"}`, and call it using Requests to print `1.0`.

## 2. Path and query parameters

Accept inputs through the URL. For this request:

```text
GET /companies/42/reports?year=2024
```

`42` is a path parameter identifying the company. `year=2024` is a query parameter filtering the reports.

```python
@app.get("/companies/{company_id}/reports")
def get_reports(company_id: int, year: int = 2025):
    return {"company_id": company_id, "year": year}
```

`company_id` matches a placeholder in the path, so FastAPI treats it as a path parameter. `year` is a simple parameter outside the path, so it is a query parameter. Its default is `2025`.

The `int` annotations tell FastAPI to convert and validate the inputs.

### Call it

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/companies/42/reports",
    params={"year": 2024},
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

Output:

```python
{"company_id": 42, "year": 2024}
```

`params=` builds the URL query string for you.

| Request | Result |
| --- | --- |
| `/companies/42/reports?year=2024` | Company `42`, year `2024`. |
| `/companies/42/reports` | Company `42`, default year `2025`. |
| `/companies/42/reports?year=hello` | `422`: year is not a valid integer. |
| `/companies/abc/reports` | `422`: company ID is not a valid integer. |

Invalid inputs are rejected before the handler runs.

### Make the year mandatory: the path version we discussed

```python
@app.get("/companies/{company_id}/reports/{year}")
def get_reports(company_id: int, year: int):
    return {"company_id": company_id, "year": year}
```

Call it with:

```text
GET /companies/42/reports/2024
```

### The required-query alternative

Removing the default also makes a query parameter required:

```python
@app.get("/companies/{company_id}/reports")
def get_reports(company_id: int, year: int):
    return {"company_id": company_id, "year": year}
```

Call it with:

```text
GET /companies/42/reports?year=2024
```

Both versions make `year` mandatory. They put it in different parts of the URL.

### Whole code: required path parameters

`main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/companies/{company_id}/reports/{year}")
def get_reports(company_id: int, year: int):
    return {"company_id": company_id, "year": year}
```

`client.py`:

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/companies/42/reports/2024",
    timeout=5,
)

response.raise_for_status()

data = response.json()

print(response.status_code)
print(data)
print(data["company_id"])
print(data["year"])
```

Start the server:

```bash
python -m pip install "fastapi[standard]" requests
fastapi dev main.py
```

In a second terminal:

```bash
python client.py
```

Expected output:

```text
200
{'company_id': 42, 'year': 2024}
42
2024
```

## 3. POST requests with a JSON body

Use a JSON body to send structured input, such as a company ID and a question.

### `main.py`

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QuestionRequest(BaseModel):
    company_id: int
    question: str

@app.post("/questions")
def ask_question(payload: QuestionRequest):
    return {
        "company_id": payload.company_id,
        "question": payload.question,
    }
```

The important part is:

```python
def ask_question(payload: QuestionRequest):
```

The Pydantic model tells FastAPI to read the JSON body, validate it, construct a `QuestionRequest` instance, and pass it to the handler as `payload`.

Use attributes such as `payload.company_id` and `payload.question` to access the values.

### `client.py`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/questions",
    json={
        "company_id": 42,
        "question": "What was revenue in 2024?",
    },
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

`json=` serializes the dictionary and sets `Content-Type: application/json`.

Run `fastapi dev main.py`, then `python client.py` in a second terminal.

Output:

```python
{
    "company_id": 42,
    "question": "What was revenue in 2024?"
}
```

| Expression | Purpose |
| --- | --- |
| `params={...}` | Send URL query parameters. |
| `json={...}` | Send a JSON request body. |
| `response.json()` | Parse a JSON response body. |

Both model fields are required because neither has a default. A missing `question` or a `company_id` of `"abc"` produces `422` before the handler runs.

### Progress checkpoint after Concept 3

At this point, we estimated roughly **25% of the planned topic coverage**: GET endpoints, path/query parameters, and POST with JSON bodies.

The remaining topics discussed at that checkpoint were:

| Topic | What to learn |
| --- | --- |
| Error handling | Return meaningful HTTP errors. |
| Response models | Validate and shape outgoing data. |
| Input constraints | Validate ranges and lengths. |
| Dependencies | Reuse logic with `Depends`. |
| Headers and authentication | Pass and validate credentials. |
| Sync versus async | Choose the right execution model. |
| Reliable HTTP calls | Timeouts, connection errors, retries, and Sessions. |
| Lifespan | Manage shared clients and models. |
| Uploads and SSE | Receive files and stream responses. |
| Integration and organization | Connect an AI workflow and organize the application. |

This was the checkpoint after Concept 3, before the following lessons.

## 4. Error handling with `HTTPException`

An input can be valid in shape but refer to something that does not exist. An integer company ID passes validation; the application still needs to check whether the company exists.

### `main.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

companies = {42: "Acme"}

class QuestionRequest(BaseModel):
    company_id: int
    question: str

@app.post("/questions")
def ask_question(payload: QuestionRequest):
    if payload.company_id not in companies:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return {
        "company": companies[payload.company_id],
        "question": payload.question,
    }
```

`raise HTTPException(...)` stops the handler and sends the specified HTTP status. Here, the response is `404` with this JSON body:

```json
{"detail": "Company not found"}
```

### `client.py`

```python
import requests

try:
    response = requests.post(
        "http://127.0.0.1:8000/questions",
        json={
            "company_id": 999,
            "question": "What was revenue in 2024?",
        },
        timeout=5,
    )

    response.raise_for_status()
    print(response.json())

except requests.HTTPError as error:
    print(error.response.status_code)
    print(error.response.json())
```

Run the server with `fastapi dev main.py` and the client with `python client.py`.

Output:

```text
404
{'detail': 'Company not found'}
```

`requests.post()` receives the response. `raise_for_status()` raises `HTTPError`, and the `except` block accesses that response through `error.response`.

| Company ID | Result | Who handles it? |
| --- | --- | --- |
| `42` | `200`, company exists. | Your lookup succeeds. |
| `999` | `404`, company does not exist. | Your application logic. |
| `"abc"` | `422`, invalid integer. | FastAPI/Pydantic validation. |

**Common mistake:** simply returning `{"error": "Company not found"}` still produces the default `200`. The client's `raise_for_status()` will not treat it as an HTTP error.

## 5. Response models

A request model defines incoming data. A response model defines the outgoing data your API promises to return.

### `main.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

companies = {42: "Acme"}

class QuestionRequest(BaseModel):
    company_id: int
    question: str

class QuestionResponse(BaseModel):
    company: str
    question: str

@app.post("/questions", response_model=QuestionResponse)
def ask_question(payload: QuestionRequest):
    if payload.company_id not in companies:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return {
        "company": companies[payload.company_id],
        "question": payload.question,
        "internal_note": "Company lookup completed",
    }
```

The key addition is:

```python
@app.post("/questions", response_model=QuestionResponse)
```

FastAPI validates the returned data against `QuestionResponse` and filters the output to that model's fields. With this model, `internal_note` is not sent to the client.

### `client.py`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/questions",
    json={
        "company_id": 42,
        "question": "What was revenue in 2024?",
    },
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

Output:

```python
{
    "company": "Acme",
    "question": "What was revenue in 2024?"
}
```

| Model | Responsibility |
| --- | --- |
| `QuestionRequest` | Validate incoming data. |
| `QuestionResponse` | Validate and filter outgoing data. |

If your handler omits a required response field such as `company`, that is a server bug and results in `500`. Invalid incoming request data results in `422`.

## 6. Input constraints with `Path`, `Query`, and `Field`

Types validate the kind of value. Constraints validate its permitted range or length.

### `main.py`

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

@app.post("/companies/{company_id}/questions")
def ask_question(
    payload: QuestionRequest,
    company_id: int = Path(gt=0),
    top_k: int = Query(default=3, ge=1, le=10),
):
    return {
        "company_id": company_id,
        "question": payload.question,
        "top_k": top_k,
    }
```

`top_k` represents the requested number of retrieval results. This endpoint only echoes the inputs; it does not perform retrieval yet.

| Input | Source | Constraint |
| --- | --- | --- |
| `company_id` | Path | Required; greater than `0`. |
| `top_k` | Query | Between `1` and `10`; default `3`. |
| `question` | JSON body | Required; between `1` and `500` characters. |

`gt` means greater than, `ge` means greater than or equal to, and `le` means less than or equal to.

### `client.py`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/companies/42/questions",
    params={"top_k": 5},
    json={"question": "What was revenue in 2024?"},
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

Output:

```python
{
    "company_id": 42,
    "question": "What was revenue in 2024?",
    "top_k": 5
}
```

One request can combine path parameters, query parameters, and a JSON body.

A company ID of `0`, a `top_k` of `11`, or an empty question produces `422`. Omitting `top_k` uses `3`.

`min_length` counts whitespace. A value of `"   "` passes this length check; rejecting whitespace-only questions requires additional validation.

## 7. Dependencies with `Depends`

A dependency is a function FastAPI runs to produce a value needed by an endpoint. Use it to share logic such as looking up a company.

### `main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

companies = {42: "Acme"}

class QuestionRequest(BaseModel):
    question: str

def get_company(company_id: int):
    if company_id not in companies:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )
    return companies[company_id]

@app.get("/companies/{company_id}")
def read_company(company=Depends(get_company)):
    return {"company": company}

@app.post("/companies/{company_id}/questions")
def ask_question(
    payload: QuestionRequest,
    company=Depends(get_company),
):
    return {"company": company, "question": payload.question}
```

The important expression is:

```python
company=Depends(get_company)
```

For company `42`, FastAPI reads the path parameter, calls `get_company(42)`, receives `"Acme"`, and passes it to the endpoint as `company`. The POST endpoint also receives its validated body as `payload`.

### `client.py`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/companies/42/questions",
    json={"question": "What was revenue in 2024?"},
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

Output:

```python
{
    "company": "Acme",
    "question": "What was revenue in 2024?"
}
```

For company `999`, the dependency raises `404`; the endpoint does not run.

Use `Depends(get_company)`, passing the function itself. Writing `get_company()` would call it immediately when defining the endpoint instead of letting FastAPI call it for the request.

## 8. Headers and bearer-token authentication

Send a bearer token in the request header:

```text
Authorization: Bearer demo-token
```

This example uses a fixed token for local learning.

### `main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

app = FastAPI()
bearer = HTTPBearer(auto_error=False)

class QuestionRequest(BaseModel):
    question: str

def get_current_user(auth=Depends(bearer)):
    if auth is None or auth.credentials != "demo-token":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "demo-user"

@app.post("/questions")
def ask_question(
    payload: QuestionRequest,
    user=Depends(get_current_user),
):
    return {"user": user, "question": payload.question}
```

`HTTPBearer` extracts the bearer credentials. `get_current_user()` checks `auth.credentials`, returns `"demo-user"`, and FastAPI injects that value into `user`.

With `auto_error=False`, missing bearer credentials produce `None`, allowing our dependency to return its own `401` response.

### `client.py`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/questions",
    headers={"Authorization": "Bearer demo-token"},
    json={"question": "What was revenue in 2024?"},
    timeout=5,
)

response.raise_for_status()
print(response.json())
```

Output:

```python
{
    "user": "demo-user",
    "question": "What was revenue in 2024?"
}
```

Removing the header or sending the wrong token produces `401`; the handler does not run.

`HTTPBearer` extracts credentials; it does not validate the token's identity for you. This fixed-string example does not verify JWT signatures or expiry.

## 9. `def` versus `async def`

Choose based on the libraries and operations your endpoint uses.

### `main.py`

```python
import time
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/sync")
def sync_example():
    time.sleep(2)
    return {"message": "Done"}

@app.get("/async")
async def async_example():
    await asyncio.sleep(2)
    return {"message": "Done"}
```

Both simulate two seconds of waiting.

| Endpoint | Where it runs | What happens while waiting? |
| --- | --- | --- |
| Regular `def` | FastAPI's thread pool. | `time.sleep(2)` occupies a worker thread. |
| `async def` | The event loop. | `await asyncio.sleep(2)` suspends this request and lets the loop handle other work. |

Both can support concurrent requests. The async version does not occupy a worker thread while waiting on this async operation.

`await` pauses the current function until the operation finishes. Code after that `await` still waits for the result.

### `client.py`

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/async",
    timeout=5,
)
response.raise_for_status()
print(response.json())
```

### Calling another API from async code

Install HTTPX:

```bash
python -m pip install httpx
```

```python
import httpx

async def fetch_company(url):
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

`await client.get(url)` waits for the network operation without blocking the event loop. `async with` manages the client's lifecycle. `response.json()` does not need `await` because the response body has already been loaded.

Do not call blocking `requests.get()` directly inside an `async def` endpoint: it blocks that worker's event loop.

Use regular `def` for blocking libraries and `async def` with awaitable libraries. FastAPI automatically handles its regular endpoint and dependency functions in a thread pool; an ordinary helper you call yourself is not automatically moved there.

## 10. Timeouts and HTTP-client errors

Keep the earlier `/async` endpoint running. Separate network failures, unsuccessful HTTP responses, and invalid response bodies.

### `client.py`

```python
import requests
from requests.exceptions import (
    Timeout,
    ConnectionError,
    HTTPError,
    JSONDecodeError,
)

try:
    response = requests.get(
        "http://127.0.0.1:8000/async",
        timeout=(2, 3),
    )

    response.raise_for_status()
    data = response.json()
    print(data)

except Timeout:
    print("The API call timed out.")

except ConnectionError:
    print("The connection failed.")

except HTTPError as error:
    print("HTTP error:", error.response.status_code)

except JSONDecodeError:
    print("The response body was not valid JSON.")
```

`timeout=(2, 3)` means a two-second connection timeout per connection attempt and a three-second read timeout between received bytes. It does not mean a five-second total deadline.

| Change | Expected outcome |
| --- | --- |
| Use `timeout=(2, 1)` with the two-second `/async` endpoint. | `Timeout`. |
| Stop the server. | `ConnectionError`. |
| Request `/missing`. | `404`; `raise_for_status()` raises `HTTPError`. |
| Request `/docs`, which returns HTML. | `JSONDecodeError` when parsing the body as JSON. |

Remember the three separate operations:

```python
response = requests.get(...)  # Perform the network call.
response.raise_for_status()   # Check for HTTP 4xx/5xx.
data = response.json()        # Parse the response body.
```

A `200` response can contain invalid JSON. An error response can contain valid JSON.

## 11. Reuse connections with `requests.Session`

When you repeatedly call the same API, a `Session` can reuse network connections and preserve shared settings such as headers and cookies. This reduces connection setup overhead.

Keep the earlier `/async` endpoint running. Use this as `client.py`:

```python
import requests

with requests.Session() as session:
    session.headers.update({"Accept": "application/json"})

    for _ in range(3):
        response = session.get(
            "http://127.0.0.1:8000/async",
            timeout=(2, 3),
        )

        response.raise_for_status()
        print(response.json())
```

Expected output:

```text
{'message': 'Done'}
{'message': 'Done'}
{'message': 'Done'}
```

| Expression | Meaning |
| --- | --- |
| `requests.Session()` | Create a reusable HTTP client with connection pooling. |
| `session.headers.update(...)` | Set default headers for requests made through this Session. |
| `session.get(...)` | Make a request using the Session. |
| `with ...` | Close the Session when leaving the block, including after an exception. |

Create the Session outside the loop so it can be reused.

Each iteration still makes a fresh request, and each call to this endpoint still takes about two seconds. Reusing connections does not cache responses.

The calls remain synchronous: the next iteration starts after the current one finishes. A Session does not make Requests asynchronous.

## 12. Bounded retries

A temporary failure may succeed on another attempt. A bounded retry policy limits how many times you try and adds a delay between attempts.

Build on the Session example. Keep `/async` running and use this as `client.py`:

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

    response = session.get(
        "http://127.0.0.1:8000/async",
        timeout=(2, 3),
    )
    response.raise_for_status()
    print(response.json())
```

`Retry` defines the policy. `HTTPAdapter` connects that policy to Requests. The two `mount()` calls apply it to HTTP and HTTPS URLs.

| Setting | Meaning |
| --- | --- |
| `total=2` | At most two retries after the original attempt: up to three attempts for eligible failures. |
| `status_forcelist` | Retry these temporary HTTP failures: rate limiting (`429`) and selected gateway/service failures (`502`, `503`, `504`). |
| `allowed_methods={"GET"}` | Limit status/read retries to GET. |
| `backoff_factor=0.5` | Normally no delay before the first retry, then one second before the second. A server's `Retry-After` header can change the wait. |
| `raise_on_status=False` | Return the final HTTP response after status retries are exhausted; `raise_for_status()` then raises `HTTPError` if needed. |

A successful `/async` request makes one attempt. A `404` is not in this retry list. Network failures can still raise connection exceptions before a response exists, and JSON parsing errors are not retried by this adapter.

The timeout applies to individual connection/read waits, not the complete operation including retries and delays. The retry count is bounded; this is not a total time budget.

**Interview point:** a timed-out POST may already have been processed. Before retrying a write, determine whether replaying it can create duplicate effects; use an API's supported idempotency mechanism where appropriate. `allowed_methods` does not restrict connection-error retries, which concern failures before the request is sent.

References: [urllib3 Retry](https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html) and [Requests: automatic retries](https://requests.readthedocs.io/en/latest/user/advanced/#example-automatic-retries).
