# Getting Started

This guide covers the essentials to get you validating DataFrames in minutes.

## Installation

```bash
pip install daffy
```

Daffy works with pandas, Polars, Modin, or PyArrow — whatever you already have installed.

For row validation with Pydantic:

```bash
pip install 'daffy[pydantic]'
```

## Your First Decorator

Import the decorators and add them to your functions:

```python
from daffy import df_in, df_out

@df_in(columns=["name", "price", "quantity"])
def process_orders(orders_df):
    # If orders_df is missing any of these columns,
    # Daffy raises an AssertionError immediately
    return orders_df
```

That's it! When `process_orders` is called, Daffy checks that the DataFrame has all required columns.

## Input and Output Validation

Validate both what goes in and what comes out:

```python
@df_in(columns=["name", "price"])
@df_out(columns=["name", "price", "total"])
def calculate_totals(df):
    df = df.copy()
    df["total"] = df["price"] * 1.1  # Add 10% tax
    return df
```

If the returned DataFrame doesn't have the expected columns, you'll know immediately.

## Type Checking

Check data types alongside column names:

```python
@df_in(columns={
    "name": "object",
    "price": "float64",
    "quantity": "int64"
})
def process_orders(df):
    return df
```

If `price` is accidentally an `int64` instead of `float64`, Daffy catches it.

## Value Constraints

Validate column values without row iteration:

```python
@df_in(columns={
    "price": {"dtype": "float64", "checks": {"gt": 0}},
    "quantity": {"dtype": "int64", "checks": {"ge": 0}},
    "status": {"checks": {"isin": ["pending", "shipped", "delivered"]}}
})
def process_orders(df):
    return df
```

## Error Messages

Daffy provides clear, actionable error messages:

```
AssertionError: Missing columns: ['quantity'] in function 'process_orders'
parameter 'df'. Got columns: ['name', 'price']
```

```
AssertionError: Column 'price' in function 'process_orders' parameter 'df'
has wrong dtype. Was int64, expected float64
```

```
AssertionError: Column 'price' in function 'process_orders' parameter 'df'
failed check gt: 3 values failed. Examples: [-5, 0, -1]
```

## Next Steps

- **[Usage Guide](usage.md)** — Complete reference for all validation options
- **[Recipes & Patterns](recipes.md)** — Real-world examples
- **[API Reference](api.md)** — Decorator signatures and parameters
