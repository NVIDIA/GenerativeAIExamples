---
hide:
  - navigation
---

# Continuous error bands

Continuous error bands represent the error or the measurement imprecision as
a filled area around a reference trace.<br/>
They are used similarly to [error bars](error-bars.md) except they appear
as a continuous shape surrounding the main trace.

A continuous error band is not a new type of chart: it is an additional trace
usually displayed under the reference trace, created as a
[filled area chart](filled-area.md).

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `scatter`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*options*](../chart.md#p-options)  | dictionary  | `fill` should be set to "toself" to create the error band shape. |

## Examples

### Simple continuous error band {data-source="gui:doc/examples/charts/continuous-error-simple.py"}

Here is a complete example that demonstrates how to create a continuous
error band.

We create the shape of the error band from the input data that is applied
a random error displacement, positively and negatively:
```python
# Common axis for all data: [1..10]
x = list(range(1, 11))
# Sample data
samples = [5, 7, 8, 4, 5, 9, 8, 8, 6, 5]

# Generate error data
# Error that adds to the input data
error_plus  = [3*random.random()+.5 for _ in x]
# Error substracted from to the input data
error_minus = [3*random.random()+.5 for _ in x]

# Upper bound (y + error_plus)
error_upper = [y+e for (y, e) in zip(samples, error_plus)]
# Lower bound (y - error_minus)
error_lower = [y-e for (y, e) in zip(samples, error_minus)]

data = [
    # Trace for samples
    {
        "x": x,
        "y": samples
    },
    # Trace for error range
    {
        # Roundtrip around the error bounds: onward then return
        "x": x + list(reversed(x)),
        # The two error bounds, with lower bound reversed
        "y": error_upper + list(reversed(error_lower))
    }
]

properties = {
    # Error data
    "x[1]": "1/x",
    "y[1]": "1/y",
    "options[1]": {
        # Shows as filled area
        "fill": "toself",
        "fillcolor": "rgba(70,70,240,0.6)",
        "showlegend": False
    },
    # Don't show surrounding stroke
    "color[1]": "transparent",

    # Raw data (displayed on top of the error band)
    "x[2]": "0/x",
    "y[2]": "0/y",
    "color[2]": "rgb(140,50,50)",
    # Shown in the legend
    "name[2]": "Input"
}
```

The reference data is stored in the *samples* array.<br/>
We generate a random error margin (additive in *error_plus* and subtractive
in *error_minus*) that we use to compute the band's shape, applying the error
for each data point.

The shape of the error band is the concatenation of two arrays: the upper and the lower bounds (respectively in *error_upper* and *error_lower*).

Note that because there are many properties to configure the chart
control, we use the dictionary *properties* that holds them all.

That dictionary is then used in the chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", properties="{properties}")
        ```

Here is the result:
<figure>
    <img src="../continuous-error-simple-d.png" class="visible-dark" />
    <img src="../continuous-error-simple-l.png" class="visible-light"/>
    <figcaption>Continuous Error</figcaption>
</figure>

### Multiple bands {data-source="gui:doc/examples/charts/continuous-error-multiple.py"}

Of course, you may need to display several traces with their related
continuous error bands.<br/>
In that situation, you only need is to create an individual trace for the
reference data and another for its band representation.

This example uses three sets of data with their own associated
bands. In this case, we're not talking about errors but rather: range.<br/>
Throughout  the year, we watch the price of three items at the closest store
every month, and we make a note of the cheapest and most expensive alternatives
we could have gotten our groceries from. This defines our ranges, for every type
of item.

Here is the code that does that:
```python
# Data is collected from January 1st, 2010, every month
start_date = datetime.datetime(year=2010, month=1, day=1)
period = dateutil.relativedelta.relativedelta(months=1)

# Data
# All arrays have the same size (the number of months to track)
prices = {
    # Data for apples
    "apples": [2.48, 2.47, 2.5, 2.47, 2.46, 2.38, 2.31, 2.25, 2.39, 2.41, 2.59, 2.61],
    "apples_low": [1.58, 1.58, 1.59, 1.64, 1.79, 1.54, 1.53, 1.61, 1.65, 2.02, 1.92, 1.54],
    "apples_high": [3.38, 3.32, 2.63, 2.82, 2.58, 2.53, 3.27, 3.15, 3.44, 3.42, 3.08, 2.86],
    "bananas": [2.94, 2.50, 2.39, 2.77, 2.43, 2.32, 2.37, 1.90, 2.31, 2.71, 3.38, 1.92],
    "bananas_low": [2.12, 1.90, 1.69, 2.44, 1.58, 1.81, 1.44, 1.00, 1.59, 1.74, 2.78, 0.96],
    "bananas_high": [3.32, 2.70, 3.12, 3.25, 3.00, 2.63, 2.54, 2.37, 2.97, 3.69, 4.36, 2.95],
    "cherries": [6.18, None, None, None, 3.69, 2.46, 2.31, 2.57, None, None, 6.50, 4.38],
    "cherries_high": [7.00, None, None, None, 8.50, 6.27, 5.61, 4.36, None, None, 8.00, 7.23],
    "cherries_low": [3.55, None, None, None, 1.20, 0.87, 1.08, 1.50, None, None, 5.00, 4.20]
}

# Create monthly time series
months = [start_date+n*period for n in range(0, len(prices["apples"]))]

data = [
    # Raw data
    {
        "Months":  months,
        "apples": prices["apples"],
        "bananas": prices["bananas"],
        "cherries": prices["cherries"]
    },
    # Range data (twice as many values)
    {
        "Months2":  months + list(reversed(months)),
        "apples": prices["apples_high"] + list(reversed(prices["apples_low"])),
        "bananas": prices["bananas_high"] + list(reversed(prices["bananas_low"])),
        "cherries": prices["cherries_high"] + list(reversed(prices["cherries_low"]))
    }
]

properties = {
    # First trace: reference for Apples
    "x[1]": "0/Months",
    "y[1]": "0/apples",
    "color[1]": "rgb(0,200,80)",
    #     Hide line
    "mode[1]": "markers",
    #     Show in the legend
    "name[1]": "Apples",
    # Second trace: reference for Bananas
    "x[2]": "0/Months",
    "y[2]": "0/bananas",
    "color[2]": "rgb(0,100,240)",
    #     Hide line
    "mode[2]": "markers",
    #     Show in the legend
    "name[2]": "Bananas",
    # Third trace: reference for Cherries
    "x[3]": "0/Months",
    "y[3]": "0/cherries",
    "color[3]": "rgb(240,60,60)",
    #     Hide line
    "mode[3]": "markers",
    #     Show in the legend
    "name[3]": "Cherries",
    # Fourth trace: range for Apples
    "x[4]": "1/Months2",
    "y[4]": "1/apples",
    "options[4]": {
        "fill": "tozerox",
        "showlegend": False,
        "fillcolor": "rgba(0,100,80,0.4)",
    },
    #      No surrounding stroke
    "color[4]": "transparent",
    # Fifth trace: range for Bananas
    "x[5]": "1/Months2",
    "y[5]": "1/bananas",
    "options[5]": {
        "fill": "tozerox",
        "showlegend": False,
        "fillcolor": "rgba(0,180,250,0.4)"
    },
    #      No surrounding stroke
    "color[5]": "transparent",
    # Sixth trace: range for Cherries
    "x[6]": "1/Months2",
    "y[6]": "1/cherries",
    "options[6]": {
        "fill": "tozerox",
        "showlegend": False,
        "fillcolor": "rgba(230,100,120,0.4)",
    },
    #      No surrounding stroke
    "color[6]": "transparent"
}
```

Because we now have to handle six different traces, it is not surprising to
see the dictionary *properties* to be quite populated.

The chart definition has not changed:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", properties="{properties}")
        ```

And the chart looks like this:
<figure>
    <img src="../continuous-error-multiple-d.png" class="visible-dark" />
    <img src="../continuous-error-multiple-l.png" class="visible-light"/>
    <figcaption>Multiple bands</figcaption>
</figure>

This chart clearly shows how the price for cherries varies significantly more
over the year than for apples or bananas.
