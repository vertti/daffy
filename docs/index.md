# Daffy

**Validate pandas and Polars DataFrames with Python decorators.**

Daffy catches missing columns, wrong data types, and invalid values at runtime — before they cause errors downstream in your data pipeline. Just add decorators to your functions.

Also supports Modin and PyArrow DataFrames.

<div class="grid" markdown>

:material-lightning-bolt: **Lightweight**<br>
Column & dtype validation with minimal overhead
{ .card }

:material-check-all: **Value Constraints**<br>
Nullability, uniqueness, range checks
{ .card }

:material-shield-check: **Row Validation**<br>
Deep validation with Pydantic models
{ .card }

:material-swap-horizontal: **Multi-Backend**<br>
Works with pandas, Polars, Modin, PyArrow
{ .card }

</div>

## Quick Example

```python
from daffy import df_in, df_out

@df_in(columns=["price", "bedrooms", "location"])
@df_out(columns=["price_per_room", "price_category"])
def analyze_housing(houses_df):
    # Transform raw housing data into price analysis
    return analyzed_df
```

If a column is missing, has wrong dtype, or violates a constraint — **Daffy fails fast** with a clear error message at the function boundary.

## Installation

=== "pip"

    ```bash
    pip install daffy
    ```

=== "conda"

    ```bash
    conda install -c conda-forge daffy
    ```

Works with whatever DataFrame library you already have installed. Python 3.11–3.14.

## Why Daffy?

Most DataFrame validation tools are schema-first (define schemas separately) or pipeline-wide (run suites over datasets). **Daffy is decorator-first:** validate inputs and outputs where transformations happen.

<table>
<tr>
<td>✓</td>
<td><strong>Non-intrusive</strong> — Just add decorators — no refactoring, no custom DataFrame types, no schema files</td>
</tr>
<tr>
<td>✓</td>
<td><strong>Easy to adopt</strong> — Add in 30 seconds, remove just as fast if needed</td>
</tr>
<tr>
<td>✓</td>
<td><strong>In-process</strong> — No external stores, orchestrators, or infrastructure</td>
</tr>
<tr>
<td>✓</td>
<td><strong>Pay for what you use</strong> — Column validation is essentially free; opt into row validation when needed</td>
</tr>
</table>

## Next Steps

<div class="grid" markdown>

:material-rocket-launch: **[Getting Started](getting-started.md)**<br>
Quick introduction to Daffy's core features
{ .card }

:material-book-open-variant: **[Usage Guide](usage.md)**<br>
Core validation features for everyday use
{ .card }

:material-chef-hat: **[Recipes & Patterns](recipes.md)**<br>
Real-world examples and best practices
{ .card }

:material-api: **[API Reference](api.md)**<br>
Decorator signatures and parameters
{ .card }

</div>
