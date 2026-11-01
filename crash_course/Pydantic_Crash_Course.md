# Pydantic Crash Course

Pydantic v2 — the topics and code discussed, with brief notes.

## 1. BaseModel and input validation

`BaseModel` uses field annotations to validate incoming data at runtime. Ordinary Python type annotations do not enforce types at runtime.

```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    question: str
    top_k: int = 5
```

- `question` is required because it has no default.
- `top_k` expects an integer and defaults to `5` when omitted.

### Validate an incoming dictionary

```python
raw_input = {
    "question": "What were the main credit risks?",
    "top_k": "3",
}

request = SearchRequest.model_validate(raw_input)

print(request.question)     # What were the main credit risks?
print(request.top_k)        # 3
print(type(request.top_k))  # <class 'int'>
```

`model_validate()` returns a model instance. Access fields through attributes such as `request.question`. By default, Pydantic allows certain conversions: the string `"3"` becomes integer `3`.

### Handle invalid input

```python
from pydantic import ValidationError

try:
    request = SearchRequest.model_validate({
        "question": "What were the main credit risks?",
        "top_k": "three",
    })
except ValidationError as error:
    print(error)
```

`"three"` cannot be parsed as an integer. Omitting `question` also fails. At this stage, `top_k=-3` still passes because it is an integer; a range constraint is needed to reject it.

## 2. Field constraints

`Field` adds rules beyond the field's type.

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
```

| Setting | Meaning |
| --- | --- |
| `min_length=1` | String must contain at least one character |
| `default=5` | Use `5` when `top_k` is omitted |
| `ge=1` | Greater than or equal to `1` |
| `le=20` | Less than or equal to `20` |

`question` remains required: its `Field` supplies a constraint, not a default.

```python
request = SearchRequest.model_validate({
    "question": "What were the main credit risks?",
    "top_k": 3,
})

print(request.top_k)  # 3
```

Assuming a valid question:

| `top_k` input | Result |
| --- | --- |
| Omitted | Uses `5` |
| `1` or `20` | Accepted; boundaries are included |
| `0`, `-3`, or `21` | Raises `ValidationError` |
| `"3"` | Converted to integer `3` and accepted |

Range constraints do not disable type conversion. `min_length=1` rejects `""`, but accepts `"   "` because spaces count as characters.

## 3. Custom field validators

A field validator runs custom logic for a field. This example trims a question and rejects an empty result.

```python
from pydantic import BaseModel, field_validator

class SearchRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def clean_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be blank")

        return value
```

| Code | Meaning |
| --- | --- |
| `@field_validator("question")` | Registers the function for `question` |
| `@classmethod` | Receives the model class as `cls` |
| `value` | The field's current value |
| `value.strip()` | Removes leading and trailing whitespace |
| `raise ValueError(...)` | Rejects the value; Pydantic reports a `ValidationError` |
| `return value` | Supplies the value to store |

The default mode is `"after"`: Pydantic validates the field's type first, then runs this function. Pydantic calls the validator automatically.

```python
request = SearchRequest.model_validate({
    "question": "   What was revenue?   "
})

print(request.question)  # What was revenue?
```

| Input for `question` | Result |
| --- | --- |
| `"  Revenue?  "` | Stores `"Revenue?"` |
| `"   "` | Raises `ValidationError` |
| `""` | Raises `ValidationError` |
| `123` | Fails string validation before the custom validator runs |

Always return the value. Forgetting the return in an after validator can leave the field as `None`.

## 4. Required fields, defaults, and None

Whether a field can be omitted and whether it accepts `None` are separate questions.

```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    question: str
    top_k: int = 5
    company: str | None = None
```

| Field | Can be omitted? | Accepts `None`? |
| --- | --- | --- |
| `question` | No | No |
| `top_k` | Yes; defaults to `5` | No |
| `company` | Yes; defaults to `None` | Yes |

```python
request = SearchRequest.model_validate({
    "question": "What was revenue?"
})

print(request.top_k)    # 5
print(request.company)  # None
```

This field is required, but its value may be `None`:

```python
company: str | None
```

This field can be omitted and defaults to `None`:

```python
company: str | None = None
```

In Pydantic v2, allowing `None` does not automatically make a field optional to provide. Defaults apply to missing fields; explicitly passing `None` does not trigger the default.

```python
SearchRequest.model_validate({
    "question": "What was revenue?",
    "top_k": None,
})
# ValidationError: top_k must be an integer
```

## 5. Nested models and lists

Use one model as a field type inside another. `list[Source]` means every item must validate against `Source`.

```python
from pydantic import BaseModel

class Source(BaseModel):
    filename: str
    page: int

class Answer(BaseModel):
    text: str
    sources: list[Source]
```

### Validate nested data

```python
data = {
    "text": "Revenue grew by 12%.",
    "sources": [
        {"filename": "annual_report.pdf", "page": "3"},
        {"filename": "earnings.pdf", "page": 7},
    ],
}

answer = Answer.model_validate(data)
```

Pydantic validates the outer model and each source dictionary, creates `Source` instances, and converts `"3"` into integer `3`.

```python
print(answer.text)                 # Revenue grew by 12%.
print(answer.sources[0].filename)  # annual_report.pdf
print(answer.sources[0].page)      # 3
```

`answer.sources` is a list of `Source` objects. An invalid nested field fails the entire validation call. If the first page were `"three"`, the error location would identify `sources.0.page`.

## 6. Serialization

Serialization converts a model into a dictionary or JSON string.

```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    question: str
    top_k: int = 5

request = SearchRequest.model_validate({
    "question": "What was revenue?"
})
```

### Convert to a Python dictionary

```python
data = request.model_dump()

print(data)
# {'question': 'What was revenue?', 'top_k': 5}

print(data["top_k"])  # 5
```

The result is a dictionary, so use key access such as `data["top_k"]`.

### Convert to a JSON string

```python
json_text = request.model_dump_json()

print(json_text)
# {"question":"What was revenue?","top_k":5}

print(type(json_text))  # <class 'str'>
```

Both methods serialize nested models automatically.

| Expression | Result |
| --- | --- |
| `request.model_dump()` | Python dictionary; may retain values such as `datetime` objects |
| `request.model_dump(mode="json")` | Dictionary containing JSON-compatible values |
| `request.model_dump_json()` | JSON string |

A `datetime` becomes a timestamp string in JSON mode. `model_dump(mode="json")` still returns a dictionary.

## 7. Strict validation

Strict validation controls type conversion. For a strict integer field, a numeric string is rejected instead of converted.

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20, strict=True)
```

| Setting | Rule |
| --- | --- |
| `strict=True` | Requires an integer input for this field |
| `ge=1, le=20` | Requires a value between 1 and 20 |
| `default=5` | Uses `5` when omitted |

### Valid input

```python
request = SearchRequest.model_validate({
    "question": "What was revenue?",
    "top_k": 3,
})

print(request.top_k)  # 3
```

### A numeric string fails

```python
SearchRequest.model_validate({
    "question": "What was revenue?",
    "top_k": "3",
})
# ValidationError: Input should be a valid integer
```

| `top_k` input | Result |
| --- | --- |
| `3` | Accepted |
| `"3"` | Rejected; string |
| `3.0` | Rejected; float |
| `21` | Rejected; outside the permitted range |
| Omitted | Uses `5` |

## 8. Extra fields

Extra fields are input keys the model does not define. By default, Pydantic silently ignores them. If the caller sends `topk` instead of `top_k`, the unknown key is discarded and the default for `top_k` is used.

### Reject unknown fields

```python
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    top_k: int = 5
```

`model_config` holds settings for the model. `extra="forbid"` rejects unexpected input keys.

```python
SearchRequest.model_validate({
    "question": "What was revenue?",
    "topk": 10,
})
# ValidationError:
# topk
#   Extra inputs are not permitted
```

Correcting the key works:

```python
request = SearchRequest.model_validate({
    "question": "What was revenue?",
    "top_k": 10,
})

print(request.top_k)  # 10
```

| Setting | What happens to unknown fields? |
| --- | --- |
| `extra="ignore"` | Discarded silently; the default |
| `extra="forbid"` | Cause a `ValidationError` |
| `extra="allow"` | Retained and included in `model_dump()` |

`strict=True` controls type conversion; `extra="forbid"` controls unexpected field names.

## 9. Model validators

Model validators check rules involving multiple fields. Both years can be valid integers while their combination is invalid.

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

| Code | Meaning |
| --- | --- |
| `@model_validator` | Registers validation for the whole model |
| `mode="after"` | Runs after the fields validate successfully |
| `self` | The model instance, with access to both fields |
| `return self` | Returns the validated model |

An after model validator uses `self`; it does not use `@classmethod`.

### Valid input

```python
request = ReportRequest.model_validate({
    "start_year": 2023,
    "end_year": 2025,
})

print(request.model_dump())
# {'start_year': 2023, 'end_year': 2025}
```

### Invalid combination

```python
ReportRequest.model_validate({
    "start_year": 2025,
    "end_year": 2023,
})
# ValidationError: end_year must be >= start_year
```

Pydantic invokes the validator automatically. Raising `ValueError` inside it causes the validation call to raise `ValidationError`.

| Validator | Typical use |
| --- | --- |
| `field_validator` | Clean or validate one field, such as trimming a question |
| `model_validator` | Check related fields, such as a year range or matching passwords |

## 10. Validation order: before versus after

For a field validator:

| Mode | When it runs | What it receives |
| --- | --- | --- |
| `before` | Before Pydantic's type and constraint checks | Raw input |
| `after` | After those checks succeed | The parsed field value |

`after` is the default for `field_validator`. Use `before` when cleaning must happen before constraints are checked.

### Trim before checking the minimum length

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

A before validator receives raw input, which might not be a string. The `isinstance` check lets other values pass through to Pydantic's normal type validation.

### Valid input

```python
request = SearchRequest.model_validate({
    "question": "   What was revenue?   "
})

print(request.question)  # What was revenue?
```

### Whitespace-only input

```python
SearchRequest.model_validate({"question": "   "})
# ValidationError: String should have at least 1 character
```

For `"   "`, the order is:

1. The before validator strips it to `""`.
2. Pydantic checks the string type.
3. `min_length=1` rejects the empty string.

If the same trimming function used `mode="after"`, the spaces would pass the length check first. Trimming would then produce an empty string, and the earlier length check would not automatically run again.

## 11. Aliases

An alias lets a field use one name in incoming JSON and another in Python code. For example, an external API sends `"topK"`, while Python code uses `top_k`.

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    question: str
    top_k: int = Field(alias="topK")

request = SearchRequest.model_validate({
    "question": "What was revenue?",
    "topK": 3
})

print(request.top_k)  # 3
```

`alias="topK"` tells Pydantic which incoming key maps to `top_k`. Access the value using `request.top_k`.

### Choose field names when serializing

```python
print(request.model_dump())
# {'question': 'What was revenue?', 'top_k': 3}

print(request.model_dump(by_alias=True))
# {'question': 'What was revenue?', 'topK': 3}
```

By default, `model_dump()` uses Python field names. Pass `by_alias=True` to use aliases. This also works with `model_dump_json()`.

Defining an alias does not automatically make both input spellings valid. With the model above, sending `"top_k"` instead of `"topK"` produces a missing-field error.

### Accept both input spellings

In Pydantic v2.11+, use this configuration:

```python
from pydantic import BaseModel, ConfigDict, Field

class SearchRequest(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True
    )

    question: str
    top_k: int = Field(alias="topK")

a = SearchRequest(question="Revenue?", topK=3)
b = SearchRequest(question="Revenue?", top_k=3)

print(a.top_k, b.top_k)  # 3 3
```

Both inputs work; Python attribute access remains `top_k`.

## 12. Default factories

Default factories create a default value by calling a function when the field is omitted.

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    question: str
    sources: list[str] = Field(default_factory=list)

a = SearchRequest(question="What was revenue?")
b = SearchRequest(question="What were the risks?")

a.sources.append("annual_report.pdf")

print(a.sources)  # ['annual_report.pdf']
print(b.sources)  # []
```

Three lines to understand:

- `default_factory=list` tells Pydantic to call `list()` to create an empty list.
- Each request that omits `sources` gets a fresh list.
- If the caller supplies `sources`, Pydantic validates that input instead of calling the factory.

```python
request = SearchRequest(
    question="What was revenue?",
    sources=["earnings.pdf"]
)

print(request.sources)  # ['earnings.pdf']
```

Pass the function itself: write `default_factory=list`, without parentheses. Pydantic calls it when needed.

| Declaration | Meaning |
| --- | --- |
| `Field(default=5)` | Use the fixed value `5` when omitted. |
| `Field(default_factory=list)` | Call `list()` when omitted. |

Pydantic also gives separate lists when writing `sources: list[str] = []`, because it copies mutable defaults. `default_factory` makes creation explicit and also supports generating values such as timestamps or request IDs.

## 13. Unions and discriminators

Unions and discriminators let a field accept different model shapes. A search request can use either a file source or a web source.

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
    question: str
    source: FileSource | WebSource = Field(discriminator="kind")

request = SearchRequest.model_validate({
    "question": "What was revenue?",
    "source": {
        "kind": "file",
        "filename": "annual_report.pdf"
    }
})

print(type(request.source).__name__)  # FileSource
print(request.source.filename)       # annual_report.pdf
```

Three lines to understand:

- `FileSource | WebSource` means the field accepts either model.
- `Literal["file"]` means that model's `kind` must equal `"file"`.
- `Field(discriminator="kind")` tells Pydantic to read `kind` inside `source` and select the corresponding model.

A web source looks like:

```python
request = SearchRequest.model_validate({
    "question": "What was revenue?",
    "source": {
        "kind": "web",
        "url": "https://example.com/report"
    }
})

print(request.source.url)  # https://example.com/report
```

| Input inside `source` | Result |
| --- | --- |
| `"kind": "file"` without `filename` | Required-field error |
| `"kind": "web"` without `url` | Required-field error |
| `"kind": "database"` | Unknown discriminator value |
| No `kind` | Missing discriminator |

The discriminator chooses the model; Pydantic then validates that model's fields.

## 14. Structured validation errors

Use `e.errors()` to get a list of error dictionaries and identify exactly what failed.

```python
from pydantic import BaseModel, Field, ValidationError

class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(ge=1, le=20)

try:
    request = SearchRequest.model_validate({
        "question": "",
        "top_k": 0
    })
except ValidationError as e:
    for error in e.errors():
        print(error["loc"], error["type"], error["msg"])

    print("Total errors:", e.error_count())
```

Output:

```text
('question',) string_too_short String should have at least 1 character
('top_k',) greater_than_equal Input should be greater than or equal to 1
Total errors: 2
```

Three fields to understand:

| Field | Meaning |
| --- | --- |
| `loc` | Where validation failed, represented as a tuple. |
| `type` | An error code your program can check. |
| `msg` | A readable explanation for a person. |

For a nested model, a location such as:

```python
("sources", 0, "page")
```

means the `page` field in the first item of `sources`.

Use `type` when writing logic that handles particular failures; use `msg` when displaying the explanation. One `ValidationError` can contain several failures, as the example shows.
