# Usage Guide

Core validation features for everyday use.

## Basic Usage

Start by importing the needed decorators:

```python
from daffy import df_in, df_out
```

## Calling Styles

Both `@df_in` and `@df_out` accept columns as the first positional argument. These two forms are equivalent:

```python
# Shorthand — columns as first positional argument
@df_in(["Brand", "Price"])
@df_in({"Brand": "object", "Price": "int64"})

# Explicit keyword
@df_in(columns=["Brand", "Price"])
@df_in(columns={"Brand": "object", "Price": "int64"})
```

Use whichever style you prefer. The shorthand is more concise; the keyword form reads well when combined with other parameters:

```python
@df_in(columns=["Brand", "Price"], strict=True)
```

When validating a specific named parameter, pass `name` as a keyword:

```python
@df_in(name="car_df", columns=["Brand", "Price"])
```

## Input Validation

To check a DataFrame input to a function, annotate the function with `@df_in`. For example the following function expects to get a DataFrame with columns `Brand` and `Price`:

```python
@df_in(["Brand", "Price"])
def process_cars(car_df):
    # do stuff with cars
```

If your function takes multiple arguments, specify the field to be checked with its `name`:

```python
@df_in(name="car_df", columns=["Brand", "Price"])
def process_cars(year, style, car_df):
    # do stuff with cars
```

You can also check columns of multiple arguments if you specify the names:

```python
@df_in(name="car_df", columns=["Brand", "Price"])
@df_in(name="brand_df", columns=["Brand", "BrandName"])
def process_cars(car_df, brand_df):
    # do stuff with cars
```

## Output Validation

To check that a function returns a DataFrame with specific columns, use `@df_out` decorator:

```python
@df_out(["Brand", "Price"])
def get_all_cars():
    # get those cars
    return all_cars_df
```

In case one of the listed columns is missing from the DataFrame, a helpful assertion error is thrown:

```python
AssertionError("Missing columns: ['Price'] in function 'get_all_cars' return value. Got columns: ['Brand']")
```

The error message clearly indicates that this is a **return value** validation failure in the function `get_all_cars`.

## Combined Validation

To check both input and output, just use both annotations on the same function:

```python
@df_in(["Brand", "Price"])
@df_out(["Brand", "Price"])
def filter_cars(car_df):
    # filter some cars
    return filtered_cars_df
```

Note that error messages will clearly distinguish between input and output validation failures:

- Input validation: `"Missing columns: ['Price'] in function 'filter_cars' parameter 'car_df'. Got columns: ['Brand']"`
- Output validation: `"Missing columns: ['Price'] in function 'filter_cars' return value. Got columns: ['Brand']"`

## Data Type Validation

If you want to also check the data types of each column, you can replace the column array:

```python
columns=["Brand", "Price"]
```

with a dict:

```python
columns={"Brand": "object", "Price": "int64"}
```

This will not only check that the specified columns are found from the DataFrame but also that their `dtype` is the expected. In case of a wrong `dtype`, an error message similar to following will explain the mismatch:

```
AssertionError("Column Price in function 'process_cars' parameter 'car_df' has wrong dtype. Was int64, expected float64")
```

## Strict Mode

You can enable strict-mode for both `@df_in` and `@df_out`. This will raise an error if the DataFrame contains columns not defined in the annotation:

```python
@df_in(["Brand"], strict=True)
def process_cars(car_df):
    # do stuff with cars
```

will, when `car_df` contains columns `["Brand", "Price"]` raise an error:

```
AssertionError: DataFrame in function 'process_cars' parameter 'car_df' contained unexpected column(s): Price
```

You can set the default value for strict mode at the project level by adding a `[tool.daffy]` section to your `pyproject.toml` file:

```toml
[tool.daffy]
strict = true
```

When this configuration is present, all `@df_in` and `@df_out` decorators will use strict mode by default. You can still override this setting on individual decorators.

## Logging

To quickly check what the incoming and outgoing dataframes contain, you can add a `@df_log` annotation to the function. For example adding `@df_log` to the above `filter_cars` function will produce log lines:

```
Function filter_cars parameters contained a DataFrame: columns: ['Brand', 'Price']
Function filter_cars returned a DataFrame: columns: ['Brand', 'Price']
```

or with `@df_log(include_dtypes=True)` you get:

```
Function filter_cars parameters contained a DataFrame: columns: ['Brand', 'Price'] with dtypes ['object', 'int64']
Function filter_cars returned a DataFrame: columns: ['Brand', 'Price'] with dtypes ['object', 'int64']
```

## Next Steps

For more advanced validation features, see [Advanced Validation](advanced.md):

- Regex column pattern matching
- Nullable and uniqueness constraints
- Optional columns
- Value checks (ranges, sets, patterns)
- Row validation with Pydantic
