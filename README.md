# Daffy — Validate pandas & Polars DataFrames with Python Decorators

[![PyPI](https://img.shields.io/pypi/v/daffy)](https://pypi.org/project/daffy/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/daffy.svg)](https://anaconda.org/conda-forge/daffy)
[![Python](https://img.shields.io/pypi/pyversions/daffy)](https://pypi.org/project/daffy/)
[![Docs](https://readthedocs.org/projects/daffy/badge/?version=latest)](https://daffy.readthedocs.io)
[![CI](https://github.com/vertti/daffy/actions/workflows/main.yml/badge.svg)](https://github.com/vertti/daffy/actions)
[![codecov](https://codecov.io/gh/vertti/daffy/graph/badge.svg?token=CISZTQ2XMS)](https://codecov.io/gh/vertti/daffy)

**Validate your pandas and Polars DataFrames at runtime with simple Python decorators.** Daffy catches missing columns, wrong data types, and invalid values before they cause downstream errors in your data pipeline.

Also supports Modin and PyArrow DataFrames.

- ✅ **Column & dtype validation** — lightweight, minimal overhead
- ✅ **Value constraints** — nullability, uniqueness, range checks
- ✅ **Row validation with Pydantic** — when you need deeper checks
- ✅ **Works with pandas, Polars, Modin, PyArrow** — no lock-in

---

## Installation

```bash
pip install daffy
```

or with conda:

```bash
conda install -c conda-forge daffy
```

Works with whatever DataFrame library you already have installed. Python 3.10–3.14.

---

## Quickstart

```python
from daffy import df_in, df_out

@df_in(columns=["price", "bedrooms", "location"])
@df_out(columns=["price_per_room", "price_category"])
def analyze_housing(houses_df):
    # Transform raw housing data into price analysis
    return analyzed_df
```

If a column is missing, has wrong dtype, or violates a constraint — **Daffy fails fast** with a clear error message at the function boundary.

---

## Why Daffy?

Most DataFrame validation tools are schema-first (define schemas separately) or pipeline-wide (run suites over datasets). **Daffy is decorator-first:** validate inputs and outputs where transformations happen.

|                          |                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Non-intrusive**        | Just add decorators — no refactoring, no custom DataFrame types, no schema files |
| **Easy to adopt**        | Add in 30 seconds, remove just as fast if needed                                 |
| **In-process**           | No external stores, orchestrators, or infrastructure                             |
| **Pay for what you use** | Column validation is essentially free; opt into row validation when needed       |

---

## Examples

### Column validation

```python
from daffy import df_in, df_out

@df_in(columns=["Brand", "Price"])
@df_out(columns=["Brand", "Price", "Discount"])
def apply_discount(df):
    df = df.copy()
    df["Discount"] = df["Price"] * 0.1
    return df
```

### Regex column matching

Match dynamic column names with regex patterns:

```python
@df_in(columns=["id", "r/feature_\\d+/"])
def process_features(df):
    return df
```

### Value constraints

Vectorized checks with zero row iteration overhead:

```python
@df_in(columns={
    "price": {"checks": {"gt": 0, "lt": 10000}},
    "status": {"checks": {"isin": ["active", "pending", "closed"]}},
    "email": {"checks": {"str_regex": r"^[^@]+@[^@]+\.[^@]+$"}},
})
def process_orders(df):
    return df
```

Available checks: `gt`, `ge`, `lt`, `le`, `between`, `eq`, `ne`, `isin`, `notnull`, `str_regex`

### Nullability and uniqueness

```python
@df_in(
    columns=["user_id", "email", "age"],
    nullable={"email": False},  # email cannot be null
    unique=["user_id"],         # user_id must be unique
)
def clean_users(df):
    return df
```

### Row validation with Pydantic

For complex, cross-field validation (requires `pydantic>=2.4.0`):

```python
from pydantic import BaseModel, Field
from daffy import df_in

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)

@df_in(row_validator=Product)
def process_inventory(df):
    return df
```

---

## Daffy vs Alternatives

| Use Case                     |        Daffy        |      Pandera       | Great Expectations  |
| ---------------------------- | :-----------------: | :----------------: | :-----------------: |
| Function boundary guardrails |  ✅ Primary focus   |     ⚠️ Possible     | ❌ Not designed for |
| Quick column/type checks     |   ✅ Lightweight    | ⚠️ Requires schemas |  ⚠️ Requires setup   |
| Complex statistical checks   |      ⚠️ Limited      |    ✅ Extensive    |    ✅ Extensive     |
| Pipeline/warehouse QA        | ❌ Not designed for |   ⚠️ Some support   |  ✅ Primary focus   |
| Multi-backend support        |         ✅          |      ⚠️ Varies      |         ✅          |

---

## Configuration

Configure Daffy project-wide via `pyproject.toml`:

```toml
[tool.daffy]
strict = true
```

---

## Documentation

Full documentation available at **[daffy.readthedocs.io](https://daffy.readthedocs.io)**

- [Getting Started](https://daffy.readthedocs.io/getting-started/) — quick introduction
- [Usage Guide](https://daffy.readthedocs.io/usage/) — comprehensive reference
- [API Reference](https://daffy.readthedocs.io/api/) — decorator signatures
- [Changelog](https://github.com/vertti/daffy/blob/master/CHANGELOG.md) — version history

---

## Contributing

Issues and pull requests welcome on [GitHub](https://github.com/vertti/daffy).

## License

MIT
