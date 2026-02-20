# Recipes & Patterns

Practical examples showing Daffy in common scenarios. Examples use Pandas, but Polars, Modin, and PyArrow work identically.

## ETL Pipeline Validation

Validate DataFrames at each step of an ETL pipeline to catch issues early.

```python
import pandas as pd
from daffy import df_in, df_out


@df_out({"product_id": "int64", "name": "object", "price": "float64", "category": "object"})
def load_products(filepath: str) -> pd.DataFrame:
    """Load product data from CSV."""
    return pd.read_csv(filepath)


@df_in(["product_id", "name", "price", "category"])
@df_out(["product_id", "name", "price", "category", "price_tier"])
def add_price_tier(df: pd.DataFrame) -> pd.DataFrame:
    """Add price tier classification."""
    df = df.copy()
    df["price_tier"] = pd.cut(
        df["price"],
        bins=[0, 25, 100, float("inf")],
        labels=["budget", "mid", "premium"]
    )
    return df


@df_in(["product_id", "name", "price", "category", "price_tier"])
@df_out(["category", "avg_price", "product_count"])
def summarize_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate products by category."""
    return df.groupby("category").agg(
        avg_price=("price", "mean"),
        product_count=("product_id", "count")
    ).reset_index()


def run_pipeline(input_path: str, output_path: str):
    """Run the full ETL pipeline."""
    products = load_products(input_path)
    products_with_tier = add_price_tier(products)
    summary = summarize_by_category(products_with_tier)
    summary.to_csv(output_path, index=False)
```

If the CSV is missing a column or has wrong types, you'll get an error at the first step rather than a confusing failure downstream.

## FastAPI Endpoint with DataFrame Validation

Validate DataFrames before converting to JSON responses.

```python
import pandas as pd
from fastapi import FastAPI, HTTPException
from daffy import df_out

app = FastAPI()

# Simulated database
PRODUCTS_DB = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Widget", "Gadget", "Gizmo"],
    "price": [19.99, 49.99, 29.99],
    "in_stock": [True, False, True]
})


@df_out({"id": "int64", "name": "object", "price": "float64", "in_stock": "bool"})
def get_products_df(in_stock_only: bool = False) -> pd.DataFrame:
    """Fetch products, optionally filtering to in-stock items."""
    df = PRODUCTS_DB.copy()
    if in_stock_only:
        df = df[df["in_stock"]]
    return df


@app.get("/products")
def list_products(in_stock_only: bool = False):
    """API endpoint returning product list."""
    try:
        df = get_products_df(in_stock_only)
        return df.to_dict(orient="records")
    except AssertionError as e:
        # Daffy validation failed - data integrity issue
        raise HTTPException(status_code=500, detail="Data validation error")
```

The `@df_out` decorator ensures the DataFrame has the expected structure before it's serialized. If someone accidentally modifies `get_products_df` to return different columns, the validation catches it immediately.

## FastAPI POST with Input Validation

Validate incoming data before processing:

```python
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from daffy import df_in, df_out

app = FastAPI()


class DataPayload(BaseModel):
    data: list[dict]


@df_in({"value": {"dtype": "float64", "checks": {"gt": 0}}})
@df_out(["value", "result"])
def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform values - validates input and output."""
    df = df.copy()
    df["result"] = df["value"] * 2
    return df


@app.post("/process")
def process_data(payload: DataPayload):
    """Accept JSON data, validate, transform, and return."""
    df = pd.DataFrame(payload.data)
    try:
        result = transform(df)
        return {"data": result.to_dict(orient="records")}
    except AssertionError as e:
        # Daffy validation failed - return 422 with details
        raise HTTPException(status_code=422, detail=str(e))
```

When validation fails, the API returns a 422 with the exact error:

```json
{
  "detail": "Column 'value' failed check gt: 2 values. Examples: [-5, 0]"
}
```
