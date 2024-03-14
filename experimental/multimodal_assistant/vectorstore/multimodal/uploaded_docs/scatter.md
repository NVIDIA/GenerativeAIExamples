---
hide:
  - navigation
---

# Scatter charts

Scatter charts represent data points as dots or other symbols.
They are useful to see relationships between groups of data points.

In order to create scatter charts with Taipy, you need to set the
[*mode[]*](../chart.md#p-mode) property for your trace to "markers".

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `scatter`          | Default value  |
| [*mode*](../chart.md#p-mode)      | `markers`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*marker*](../chart.md#p-marker)  | dictionary  | `size` can be set to an integer value.<br/>`color` can be set to a color name or value.<br/>`symbol` can be set to a predefined symbol name (see [Symbol names](https://plotly.com/javascript/reference/scatter/#scatter-marker-symbol) for details).<br/>`opacity` can be set to an opacity value (between 0 and 1).  |
| [*layout*](../chart.md#p-layout) | dictionary | Global layout settings.  |

## Examples

### Classification {data-source="gui:doc/examples/charts/scatter-classification.py"}

Using a scatter chart to represent the result of the classification of
samples is really relevant: you can use different colors to represent
different classes that data points belong to.

Here is an example where we have two series of samples, based on the same
*x* axis: samples are stored in one series or the other depending on
a classification algorithm. The result is three numerical arrays:

- The values on the *x* axis.
- The *y* values for the samples that belong to the class 'A'. The value
  is set to Nan if it does not belong to class 'A'.
- The *y* values for the samples that belong to the class 'B'. The value
  is set to Nan if it does not belong to class 'B'.

```python
x_range = [ 0.64,  1.05, ...1000 values..., -0.7, -1.2]
a_values = [ nan, nan, 1.04, -1.01, ...1000 values..., 1.6, 1.45, nan ]
b_values = [ -2.1, -0.99, nan, nan, ...1000 values..., nan, nan, 2.12]
data = pd.DataFrame({
  "x" : x_range,
  "Class A" : a_values,
  "Class B" : b_values
})
```

The chart definition looks like this:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|x=x|y[1]=Class A|y[2]=Class B|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" x="x" y[1]="Class A" y[2]="Class B">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", x="x", y[1]="Class A", y[2]="Class B")
        ```

Note how the [*mode*](../chart.md#p-mode) property is set to "markers".

The resulting chart is:
<figure>
    <img src="../scatter-classification-d.png" class="visible-dark" />
    <img src="../scatter-classification-l.png" class="visible-light"/>
    <figcaption>Classification</figcaption>
</figure>

### Customizing a scatter chart {data-source="gui:doc/examples/charts/scatter-styling.py"}

A common problem with scatter charts is that individual markers can be displayed
on top of each other. This may result in markers being hidden by others, and
the display may not reflect the density of markers. This is why it
is usually not a good idea to use scatter charts where markers are completely
opaque.

It is easy to customize the markers representation using the
[*marker*](../chart.md#p-marker) indexed property. This property expects
a dictionary that indicates how markers should be represented. The structure
of this dictionary and available values are listed in the
[Plotly scatter](https://plotly.com/python/reference/scatter/#scatter-marker)
documentation page.

Here is how we can change the size and shape of the markers that are used in
our previous example (with fewer data points). We need to create two
dictionaries that hold the values we want to impact:
```python
marker_A = {
    "symbol": "circle-open",
    "size": 16
}
marker_B = {
  "symbol": "triangle-up-dot",
  "size": 20,
  "opacity": 0.7
}
```
We are requesting that the markers have different shape to represent different data sets,
and the markers for the B data set are slightly bigger.

To have Taipy use those styles, we must modify the chart definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|x=x|y[1]=Class A|marker[1]={marker_A}|y[2]=Class B|marker[2]={marker_B}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" x="x" y[1]="Class A" marker[1]="{marker_A}" y[2]="Class B" marker[2]="{marker_B}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", x="x", y[1]="Class A", marker[1]="{marker_A}", y[2]="Class B", marker[2]="{marker_B}")
        ```

That generates the following chart:
<figure>
    <img src="../scatter-styling-d.png" class="visible-dark" />
    <img src="../scatter-styling-l.png" class="visible-light"/>
    <figcaption>Styling markers</figcaption>
</figure>

### Customizing individual data points {data-source="gui:doc/examples/charts/scatter-more-styling.py"}

Changing the style of markers can also be set for each individual data point.

Consider the following array of three data sets:
```python
data = [
    { "x": [1, 2, 3, 4], "y": [10, 11, 12, 13] },
    { "x": [1, 2, 3, 4], "y": [11, 12, 13, 14] },
    { "x": [1, 2, 3, 4], "y": [12, 13, 14, 15] }
]
```

We can create an array of *marker* dictionaries, on for every trace, where
we indicate how data points will be represented:
```python
markers = [
    # First data set is represented by increasingly large
    # disks, getting more and more opaque
    {
        "color": "red",
        "size": [12, 22, 32, 42],
        "opacity": [0.2, 0.5, 0.7, 1]
    },
    # Second data set is represented with a different symbol
    # for each data point
    {
        "color": "blue",
        "size": 18,
        "symbol": ["circle", "square", "diamond", "cross"]
    },
    # Third data set is represented with green disks surrounded
    # by a red circle that becomes thicker and thicker
    {
        "color": "green",
        "size": 20,
        "line": {
            "color": "red",
            "width": [2, 4, 6, 8]
        }
    }
]
```

We can further customize the whole chart be creating a *layout* dictionary and
use it in our chart:
```python
layout = {
    # Hide the chart legend
    "showlegend": False,
    # Remove all ticks from the x axis
    "xaxis": {
        "showticklabels": False
    },
    # Remove all ticks from the y axis
    "yaxis": {
        "showticklabels": False
    }
}
```

The chart definition can now use this array as the value for the indexed property
[*marker*](../chart.md#p-marker): each item applies to consecutive traces.<br/>
We also set the [*layout*](../chart.md#p-layout) property to apply the global
layout settings:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|marker={markers}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" marker="{markers}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", marker="{markers}", layout="{layout}")
        ```

The resulting chart displays as:
<figure>
    <img src="../scatter-more-styling-d.png" class="visible-dark" />
    <img src="../scatter-more-styling-l.png" class="visible-light"/>
    <figcaption>Styling data points</figcaption>
</figure>

### Regression {data-source="gui:doc/examples/charts/scatter-regression.py"}

Regression is an excellent use case for using scatter charts: on top of samples data
points, you can trace the plot of a function that best fits the data points.

Here is an example of linear regression, where we can use a line plot on top of
markers. The chart will represent an array of two Data Frames: one for the
original data points and one for the computed regression line.

Here is the code that defines the source data for the chart:
```python
data = [
  {
    "x": [ 0.13, -0.49, ..., 1.89, -0.97 ],
    "y": [ 22.23, -51.77, ..., 135.76, -77.33 ]
  },
  {
    "x": [ -3.53,  2.95 ],
    "Regression": [ -237.48, 200 ]
  }
  ]
```

The values *x* and *Regression* could be computed, for example, using the
[LinearRegression class](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
from the [`scikit-learn` package](https://scikit-learn.org/stable/).

The chart definition uses the two data sets and their columns:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode[1]=markers|x[1]=0/x|y[1]=0/y|mode[2]=line|x[2]=1/x|y[2]=1/Regression|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode[1]="markers" x[1]="0/x" y[1]="0/y" mode[2]="line" x[2]="1/x" y[2]="1/Regression">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode[1]="markers", x[1]="0/x", y[1]="0/y", mode[2]="line", x[2]="1/x", y[2]="1/Regression")
        ```

See how, using the *mode[]*, *x[]*, and *y[]* properties, the two plots are defined.<br/>
Also note how the data sets are referenced: `x[1]` being set to `0/x` indicates that the
x values for the first trace should be retrieved from the column called *x* in the first
element of the data array (0 indicating the first array element).

The chart representing the linear regression result is the following:
<figure>
    <img src="../scatter-regression-d.png" class="visible-dark" />
    <img src="../scatter-regression-l.png" class="visible-light"/>
    <figcaption>Linear regression</figcaption>
</figure>
