# Advanced Validation

Advanced validation features for complex data quality requirements.

## Column Pattern Matching with Regex

You can use regex patterns to match column names that follow a specific pattern. This is useful when working with dynamic column names or when dealing with many similar columns.

Define a regex pattern by using the format `"r/pattern/"`:

```python
@df_in(["Brand", "r/Price_\d+/"])
def process_data(df):
    # This will accept DataFrames with columns like "Brand", "Price_1", "Price_2", etc.
    ...
```

In this example:

- The DataFrame must have a column named exactly "Brand"
- The DataFrame must have at least one column matching the pattern "Price_\d+" (e.g., "Price_1", "Price_2", etc.)

If no columns match a regex pattern, an error is raised:

```
AssertionError: Missing columns: ['r/Price_\d+/'] in function 'process_data' parameter 'df'. Got columns: ['Brand', 'Model']
```

Regex patterns are also considered in strict mode. Any column matching a regex pattern is considered valid.

### Combining Regex Patterns with Data Type Validation

You can use regex patterns in dictionaries that specify data types as well:

```python
@df_in({"Brand": "object", "r/Price_\d+/": "int64"})
def process_data(df):
    # This will check that all columns matching "Price_\d+" have int64 dtype
    ...
```

In this example:

- The DataFrame must have a column named exactly "Brand" with dtype "object"
- Any columns matching the pattern "Price_\d+" (e.g., "Price_1", "Price_2") must have dtype "int64"

If a column matches the regex pattern but has the wrong dtype, an error is raised:

```
AssertionError: Column Price_2 in function 'process_data' parameter 'df' has wrong dtype. Was float64, expected int64
```

## Nullable Validation

You can validate that columns contain no null values using the rich column spec format:

```python
@df_in({"price": {"nullable": False}})
def process_prices(df):
    # price column must not contain any null/NaN values
    ...
```

### Combining with Data Type Validation

Nullable validation can be combined with dtype validation:

```python
@df_in({"price": {"dtype": "float64", "nullable": False}})
def process_prices(df):
    # price must be float64 AND contain no nulls
    ...
```

### With Regex Patterns

Nullable validation works with regex patterns, applying to all matched columns:

```python
@df_in({"r/Price_\\d+/": {"nullable": False}})
def process_data(df):
    # All columns matching Price_1, Price_2, etc. must not contain nulls
    ...
```

### Default Behavior

By default, `nullable=True`, meaning null values are allowed. This preserves backwards compatibility - existing code continues to work unchanged.

If a column contains null values when `nullable=False`, an error is raised:

```
AssertionError: Column 'price' in function 'process_prices' parameter 'df' contains 3 null values but nullable=False
```

## Uniqueness Validation

You can validate that columns contain only unique values using the rich column spec format:

```python
@df_in({"user_id": {"unique": True}})
def process_users(df):
    # user_id column must not contain any duplicate values
    ...
```

### Combining with Other Validations

Uniqueness validation can be combined with dtype and nullable validation:

```python
@df_in({"user_id": {"dtype": "int64", "unique": True, "nullable": False}})
def process_users(df):
    # user_id must be int64, contain no nulls, AND have no duplicates
    ...
```

### With Regex Patterns

Uniqueness validation works with regex patterns, applying to all matched columns:

```python
@df_in({"r/ID_\\d+/": {"unique": True}})
def process_data(df):
    # All columns matching ID_1, ID_2, etc. must have unique values
    ...
```

### Default Behavior

By default, `unique=False`, meaning duplicate values are allowed. This preserves backwards compatibility - existing code continues to work unchanged.

If a column contains duplicate values when `unique=True`, an error is raised:

```
AssertionError: Column 'user_id' in function 'process_users' parameter 'df' contains 5 duplicate values but unique=True
```

## Composite Uniqueness

For validating that combinations of columns are unique (like a composite primary key), use `composite_unique`:

```python
@df_in(composite_unique=[["first_name", "last_name"]])
def process_users(df):
    # The combination of first_name + last_name must be unique
    ...
```

### Multiple Constraints

You can specify multiple composite uniqueness constraints:

```python
@df_in(
    columns={"email": {"unique": True}},  # Single column unique
    composite_unique=[
        ["first_name", "last_name"],      # Name combo must be unique
        ["department", "employee_id"],     # Dept + ID must be unique
    ]
)
def process_data(df):
    ...
```

### Error Messages

When composite uniqueness fails, you get an error like:

```
AssertionError: Columns 'first_name' + 'last_name' in function 'process_users' parameter 'df' contain 5 duplicate combinations but composite_unique is set
```

## Shape Validation

Enforce row count constraints on your DataFrames.

### Minimum Rows

Require a minimum number of rows:

```python
@df_in(min_rows=1)  # Reject empty DataFrames
def process_data(df):
    ...

@df_out(min_rows=10)  # Ensure at least 10 rows are returned
def get_results():
    ...
```

### Maximum Rows

Limit the maximum number of rows:

```python
@df_in(max_rows=1000)  # Reject DataFrames with more than 1000 rows
def process_batch(df):
    ...
```

### Exact Row Count

Require an exact number of rows:

```python
@df_in(exact_rows=5)  # Require exactly 5 rows
def process_lookup_table(df):
    ...
```

### Combining Constraints

```python
@df_out(min_rows=10, max_rows=100)  # Between 10 and 100 rows
def transform_data(df):
    ...
```

### Error Messages

```
# min_rows violation
AssertionError: DataFrame in function 'process_data' parameter 'df' has 0 rows but min_rows=1

# max_rows violation
AssertionError: DataFrame in function 'process_data' return value has 150 rows but max_rows=100

# exact_rows violation
AssertionError: DataFrame in function 'process_data' parameter 'df' has 8 rows but exact_rows=5
```

## Optional Columns

By default, all specified columns are required. You can mark columns as optional using `required=False`:

```python
@df_in({
    "user_id": {"dtype": "int64"},
    "nickname": {"dtype": "object", "required": False}
})
def process_users(df):
    # user_id is required, nickname is optional
    ...
```

### Behavior

- If an optional column is missing, no error is raised
- If an optional column is present, all other validations (dtype, nullable, unique) still apply

```python
@df_in({
    "discount": {"dtype": "float64", "nullable": False, "required": False}
})
def process_orders(df):
    # discount is optional, but if present it must be float64 with no nulls
    ...
```

### With Regex Patterns

Optional columns work with regex patterns:

```python
@df_in({
    "id": {"dtype": "int64"},
    "r/extra_\\d+/": {"dtype": "object", "required": False}
})
def process_data(df):
    # Must have 'id', may optionally have extra_1, extra_2, etc.
    ...
```

### Default Behavior

By default, `required=True`, meaning all columns must exist. This preserves backwards compatibility - existing code continues to work unchanged.

## Value Checks

You can validate column values using vectorized checks. This is faster than row-by-row validation because it uses vectorized DataFrame operations:

```python
@df_in({
    "price": {"checks": {"gt": 0}},
    "score": {"checks": {"between": (0, 100)}},
    "status": {"checks": {"isin": ["active", "pending", "closed"]}},
})
def process_data(df):
    ...
```

### Available Checks

| Check            | Argument   | Description                | Example                      |
| ---------------- | ---------- | -------------------------- | ---------------------------- |
| `gt`             | number     | Greater than               | `{"gt": 0}`                  |
| `ge`             | number     | Greater than or equal      | `{"ge": 0}`                  |
| `lt`             | number     | Less than                  | `{"lt": 100}`                |
| `le`             | number     | Less than or equal         | `{"le": 100}`                |
| `eq`             | value      | Equal to                   | `{"eq": "active"}`           |
| `ne`             | value      | Not equal to               | `{"ne": "deleted"}`          |
| `between`        | (lo, hi)   | Value in range (inclusive) | `{"between": (0, 100)}`      |
| `isin`           | list       | Value in set               | `{"isin": ["a", "b", "c"]}`  |
| `notin`          | list       | Value not in set           | `{"notin": ["x", "y"]}`      |
| `notnull`        | True       | No null values             | `{"notnull": True}`          |
| `str_regex`      | pattern    | String matches regex       | `{"str_regex": r"^\d+$"}`    |
| `str_startswith` | string     | String starts with prefix  | `{"str_startswith": "pre_"}` |
| `str_endswith`   | string     | String ends with suffix    | `{"str_endswith": ".csv"}`   |
| `str_contains`   | string     | String contains substring  | `{"str_contains": "@"}`      |
| `str_length`     | (min, max) | String length in range     | `{"str_length": (1, 100)}`   |

### Multiple Checks

You can combine multiple checks on a single column:

```python
@df_in({
    "price": {"checks": {"gt": 0, "lt": 10000}},
    "age": {"checks": {"ge": 0, "le": 120}},
})
def process_data(df):
    ...
```

### Combining with Other Validations

Checks work alongside other column validations:

```python
@df_in({
    "price": {
        "dtype": "float64",
        "nullable": False,
        "checks": {"gt": 0}
    }
})
def process_data(df):
    ...
```

### With Regex Column Patterns

Checks apply to all columns matching a regex pattern:

```python
@df_in({
    "r/score_\\d+/": {"checks": {"between": (0, 100)}}
})
def process_data(df):
    # All columns like score_1, score_2, etc. must be in range 0-100
    ...
```

### With Optional Columns

If a column is optional and missing, checks are skipped:

```python
@df_in({
    "discount": {"required": False, "checks": {"ge": 0, "le": 1}}
})
def process_data(df):
    # If discount column exists, it must be between 0 and 1
    ...
```

### Custom Check Functions

For validation logic not covered by built-in checks, you can use custom functions. The function receives a [Narwhals Series](https://narwhals-dev.github.io/narwhals/) and should return a boolean Series where `True` means valid:

```python
@df_in({
    "price": {"checks": {
        "gt": 0,  # built-in check
        "no_outliers": lambda s: s < s.mean() * 10  # custom check
    }}
})
def process_data(df):
    ...
```

The dictionary key becomes the check name in error messages:

```
AssertionError: Column 'price' failed check 'no_outliers': 3 values failed. Examples: [50000, 99999]
```

Custom checks can use any Narwhals Series operations:

```python
@df_in({
    "email": {"checks": {
        "has_at": lambda s: s.str.contains("@"),
        "reasonable_length": lambda s: (s.str.len_chars() >= 5) & (s.str.len_chars() <= 254)
    }},
    "score": {"checks": {
        "within_3_std": lambda s: (s - s.mean()).abs() <= s.std() * 3
    }}
})
def process_data(df):
    ...
```

### Error Messages

When checks fail, you get informative error messages:

```
AssertionError: Column 'price' in function 'process_data' parameter 'df' failed check gt: 3 values failed. Examples: [-5, 0, -1]
```

For multiple failures:

```
AssertionError: Check violations in function 'process_data' parameter 'df':
  Column 'price' failed gt: 3 values. Examples: [-5, 0, -1]
  Column 'status' failed isin: 2 values. Examples: ['deleted', 'unknown']
```

## Row Validation

In addition to column validation, Daffy supports row-level validation using Pydantic models. This allows you to validate actual data values, not just column structure.

**Performance consideration:** Column validation is lightweight with minimal overhead. Row validation validates data values and will impact performance, especially on large DataFrames. Use row validation when data quality is critical.

### Basic Row Validation

First, install Pydantic if you haven't already:

```bash
pip install 'daffy[pydantic]'
```

Define a Pydantic model describing your expected row structure:

```python
from pydantic import BaseModel, Field
from daffy import df_in

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Price must be positive
    stock: int = Field(ge=0)    # Stock cannot be negative

@df_in(row_validator=Product)
def process_inventory(df):
    return df
```

If any rows fail validation, you'll get a detailed error message:

```python
AssertionError: Row validation failed for 2 out of 100 rows:

  Row 5:
    - price: Input should be greater than 0

  Row 12:
    - stock: Input should be greater than or equal to 0

 in function 'process_inventory' parameter 'df'
```

### Combined Column and Row Validation

You can validate both columns and row data:

```python
@df_in(["name", "price", "stock"], row_validator=Product)
def process_inventory(df):
    return df
```

Column validation runs first (fast check), then row validation runs if columns are valid.

### Validating Return Values

Use `row_validator` with `@df_out` to validate returned DataFrames:

```python
@df_out(row_validator=Product)
def load_products():
    return products_df
```

### Performance Optimization

Row validation includes an early termination optimization. When validation errors are found, scanning stops after collecting `max_errors` failures instead of processing the entire DataFrame.

**Performance impact:**

- **DataFrames with errors:** 71-124x faster (stops early)
- **DataFrames without errors:** No overhead (must scan all rows)

For example, validating 100k rows with early errors takes ~1.2ms instead of ~140ms.

This optimization is enabled by default. Error messages will show "X out of Y+ rows" when early termination occurs, indicating there may be additional errors beyond those displayed.

### Advanced Features

Pydantic's validation features work seamlessly:

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator

class Employee(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    email: str
    age: int = Field(ge=18, le=120)
    salary: float = Field(gt=0)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('must contain @')
        return v

@df_in(row_validator=Employee)
def process_employees(df):
    return df
```

## Lazy Validation

By default, validation stops at the first error type. With `lazy=True`, all errors are collected and reported together:

```python
@df_in({
    "price": {"dtype": "float64", "nullable": False},
    "quantity": {"dtype": "int64", "checks": {"gt": 0}},
    "category": "object"
}, lazy=True)
def process_order(df):
    ...
```

When multiple validations fail, the error message includes all issues:

```
Missing columns: ['category'] in function 'process_order' parameter 'df'. Got columns: ['price', 'quantity']

Column 'price' contains 2 null values but nullable=False

Column 'quantity' failed check gt: 1 values failed. Examples: [-5]
```

This is useful for debugging when a DataFrame has multiple issues.

## Configuration

All configuration options can be set in `pyproject.toml`:

```toml
[tool.daffy]
strict = true                    # Enable strict mode by default
lazy = true                      # Collect all errors before raising (default: false)
allow_empty = false              # Reject empty DataFrames by default (default: true)
row_validation_max_errors = 5    # Max failed rows to show (default: 5)
checks_max_samples = 5           # Max sample values in check errors (default: 5)
```

### allow_empty

When set to `false`, all DataFrames will be rejected if they have 0 rows:

```python
# With allow_empty=false in config, this will raise:
@df_in()
def process(df):  # Raises if df is empty
    ...

# Override for specific decorators:
@df_in(allow_empty=True)  # Allow empty even if config says false
def optional_process(df):
    ...
```
