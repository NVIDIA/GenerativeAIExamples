---
hide:
  - navigation
---

# Heatmaps

A heatmap depicts values for a main variable of interest across two axes as a grid of colored
rectangles. The axes are divided into ranges like a bar chart or histogram, and each cell’s
color hints at the value of the main variable at the corresponding cell range's location.

Typical usages of heatmaps:

- Display the magnitude of a data set over two dimensions;
- In retail matrix, manufacturing diagram, and population maps;
- For marketing goals and analytics, reflecting on user behavior on specific web pages;
- ...

To create a heatmap in Taipy, you must set the property [*type*](../chart.md#p-type)
of the chart control to "heatmap".

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `heatmap`              |  |
| [*x*](../chart.md#p-x)            | x values               |  |
| [*y*](../chart.md#p-y)            | y values               |  |
| [*z*](../chart.md#p-z)            | Main variable values.  |  |
| [*options*](../chart.md#p-options)  | dictionary  | `colorscale` can be used to set a color scale.<br/>`showscale` can be set to False to hide the color scale.  |
| [*layout*](../chart.md#p-layout)    | dictionary  | `annotations` can be used to add specific text information to a cell.  |

## Examples

### Simple Heatmap {data-source="gui:doc/examples/charts/heatmap-simple.py"}

This example displays a heatmap representing the temperatures, in °C, in some cities during
a given season (of the northern hemisphere).

We define the dataset to be displayed as a simple dictionary:
```python
data = {
    "Temperatures": [[17.2, 27.4, 28.6, 21.5],
                     [5.6, 15.1, 20.2, 8.1],
                     [26.6, 22.8, 21.8, 24.0],
                     [22.3, 15.5, 13.4, 19.6]],
    "Cities": ["Hanoi", "Paris", "Rio", "Sydney"],
    "Seasons": ["Winter", "Spring", "Summer", "Autumn"]
}
```

Taipy converts the *data* dictionary into a Pandas DataFrame, where all entries
must be lists of the same size.

Here is how you would define the chart control to represent this data:

- The main variable is referenced by the [*z*](../chart.md#p-z) property.
- The two axes are referenced by the [*x*](../chart.md#p-x) and [*y*](../chart.md#p-y)
  properties.

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=heatmap|z=Temperatures|x=Seasons|y=Cities|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="heatmap" z="Temperatures" x="Seasons" y="Cities">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="heatmap", z="Temperatures", x="Seasons", y="Cities")
        ```

And here is how the resulting chart will look like on the page:
<figure>
    <img src="../heatmap-simple-d.png" class="visible-dark" />
    <img src="../heatmap-simple-l.png" class="visible-light" />
    <figcaption>Temperatures</figcaption>
</figure>

### Unbalanced Heatmap {data-source="gui:doc/examples/charts/heatmap-unbalanced.py"}

The example above was an example where the size of the datasets for the *x* and *y*
axes was the same.

If you needed to add another city to be represented on the *y* axis, you would need
to change the definition of the source dataset:
```python
data = [
    {
        "Temperatures": [[17.2, 27.4, 28.6, 21.5],
                         [5.6, 15.1, 20.2, 8.1],
                         [26.6, 22.8, 21.8, 24.0],
                         [22.3, 15.5, 13.4, 19.6],
                         [3.9, 18.9, 25.7, 9.8]],
        "Cities": ["Hanoi", "Paris", "Rio", "Sydney", "Washington"]
    },
    {
        "Seasons": ["Winter", "Spring", "Summer", "Autumn"]
    }
]
```

*data* is now an array of two dictionaries, where the first element's values
all have a length of 5 and the second element's value has a length
of 4.

To reference which value array to use on which axes, the declaration
of the control must change slightly:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=heatmap|z=0/Temperatures|x=1/Seasons|y=0/Cities|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="heatmap" z="0/Temperatures" x="1/Seasons" y="0/Cities">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="heatmap", z="0/Temperatures", x="1/Seasons", y="0/Cities")
        ```

Here is how the data is referenced from the chart control:

- *z* is set to "0/Temperatures", indicating the column "Temperatures" of the first element
  of *data*
- *x* is set to "1/Seasons", indicating the column "Seasons" of the second element
  of *data*
- *y* is set to "0/Cities", indicating the column "Cities" of the first element
  of *data*

And the chart displays as expected:
<figure>
    <img src="../heatmap-unbalanced-d.png" class="visible-dark" />
    <img src="../heatmap-unbalanced-l.png" class="visible-light" />
    <figcaption>Temperatures</figcaption>
</figure>

### Setting the color scale {data-source="gui:doc/examples/charts/heatmap-colorscale.py"}

If you want to change the color scale used in the heatmap cells, you must set the *colorscale*
property of the property [*options*](../chart.md#p-options) of the chart control.<br/>
You can create an entirely custom color scale or use one of the predefined values listed
in the [Colorscales](https://plotly.com/javascript/colorscales/) page of the
[Plotly.js](https://plotly.com/javascript/) documentation.

We are reusing the code of the first example, where we add a new variable to hold the
options for our chart control:
```python
options = { "colorscale": "Portland" }
```

And reference that dictionary in the [*options*](../chart.md#p-options) property of the
control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=heatmap|z=Temperatures|x=Seasons|y=Cities|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="heatmap" z="Temperatures" x="Seasons" y="Cities" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="heatmap", z="Temperatures", x="Seasons", y="Cities", options="{options}")
        ```

Here is how the page looks like:
<figure>
    <img src="../heatmap-colorscale-d.png" class="visible-dark" />
    <img src="../heatmap-colorscale-l.png" class="visible-light" />
    <figcaption>Specific Color Scale</figcaption>
</figure>

### Annotated Heatmap {data-source="gui:doc/examples/charts/heatmap-annotated.py"}

You may need to display some information in the cells of a heatmap.

This example demonstrates how to display the temperature for a given city
in a given season in the appropriate heatmap cell, leveraging the previous
example.

Here is the code that is needed (we use the same definition for *data* as in the previous
example):
```python
layout = {
    # This array contains the information we want to display in the cells
    # These are filled later
    "annotations": [],
    # No ticks on the x axis, show labels on top the of the chart
    "xaxis": {
        "ticks": "",
        "side": "top"
    },
    # No ticks on the y axis
    # Add a space character for a small margin with the text
    "yaxis": {
        "ticks": "",
        "ticksuffix": " "
    }
}

seasons = data["Seasons"]
cities = data["Cities"]
# Iterate over all cities
for city in range(len(cities)):
    # Iterate over all seasons
    for season in range(len(seasons)):
        temperature = data["Temperatures"][city][season]
        # Create the annotation
        annotation = {
            # The name of the season
            "x": seasons[season],
            # The name of the city
            "y": cities[city],
            # The temperature, as a formatted string
            "text": f"{temperature}\N{DEGREE SIGN}C",
            # Change the text color depending on the temperature
            # so it results in a better contrast
            "font": {
                "color": "white" if temperature < 14 else "black"
            },
            # Remove the annotation arrow
            "showarrow": False
        }
        # Add the annotation to the layout's annotations array
        layout["annotations"].append(annotation)
```

We create the *layout* dictionary that will be set to the [*layout*](../chart.md#p-layout)
property of the chart, then fill its *annotations* property for every city and every
season, storing a formatted string representing the temperature.

The chart definition will appear as follows:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=heatmap|z=Temperatures|x=Seasons|y=Cities|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="heatmap" z="Temperatures" x="Seasons" y="Cities" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="heatmap", z="Temperatures", x="Seasons", y="Cities", layout="{layout}")
        ```

And the result looks like this:
<figure>
    <img src="../heatmap-annotated-d.png" class="visible-dark" />
    <img src="../heatmap-annotated-l.png" class="visible-light" />
    <figcaption>Annotated Heatmap</figcaption>
</figure>

### Unequal Cell Sizes {data-source="gui:doc/examples/charts/heatmap-unequal-cell-sizes.py"}

You may need to specify the size of each heatmap cell, both in the horizontal and the vertical
dimensions.

Let's consider the following code:
```python
grid_size = 10
data = [
    {
        # z is set to:
        # - 0 if row+col is a multiple of 4
        # - 1 if row+col is a multiple of 2
        # - 0.5 otherwise
        "z": [[0. if (row+col) % 4 == 0 else 1 if (row+col) % 2 == 0 else 0.5 for col in range(grid_size)] for row in range(grid_size)]
    },
    {
        # A series of coordinates, growing exponentially
        "x": [0] + list(accumulate(np.logspace(0, 1, grid_size))),
        # A series of coordinates, shrinking exponentially
        "y": [0] + list(accumulate(np.logspace(1, 0, grid_size)))
    }
]

# Axis template used in the layout object
axis_template = {
    # Don't show any line or tick or label
    "showgrid": False,
    "zeroline": False,
    "ticks": "",
    "showticklabels": False,
    "visible": False
}

layout = {
    "xaxis": axis_template,
    "yaxis": axis_template
}

options = {
    # Remove the color scale display
    "showscale": False
}
```

Note how *data[1]* holds the two properties *x* and *y* that provide the size
of each cell on the relevant axis.

Here is how you would create the control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=heatmap|z=0/z|x=1/x|y=1/y|layout={layout}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="heatmap" z="0/z" x="1/x" y="1/y" layout="{layout}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="heatmap", z="0/z", x="1/x", y="1/y", layout="{layout}", options="{options}")
        ```

Note how the [*x*](../chart.md#p-x) and [*y*](../chart.md#p-y) properties are set to the
coordinate array we computed (in *data[1]*).

Here is resulting chart:
<figure>
    <img src="../heatmap-unequal-cell-sizes-d.png" class="visible-dark" />
    <img src="../heatmap-unequal-cell-sizes-l.png" class="visible-light" />
    <figcaption>Unequal cell sizes</figcaption>
</figure>

### Drawing on top of a heatmap {data-source="gui:doc/examples/charts/heatmap-drawing-on-top.py"}

You can even add another trace on top of a heatmap.

Here is an example of displaying a [Golden spiral](https://en.wikipedia.org/wiki/Golden_spiral)
on top of a heatmap representing a Fibonacci sequence. This example was more or less
translated to Python from the
[Plotly.js documentation](https://plotly.com/javascript/heatmaps/).

```python
# Return the x and y coordinates of the spiral for the given angle
def spiral(th):
    a = 1.120529
    b = 0.306349
    r = a * numpy.exp(-b * th)
    return (r * numpy.cos(th), r * numpy.sin(th))


# Prepare Golden spiral data as a parametric curve
(x, y) = spiral(numpy.linspace(-numpy.pi / 13, 4 * numpy.pi, 1000))

# Prepare the heatmap x and y cell sizes along the axes
golden_ratio = (1 + numpy.sqrt(5)) / 2.  # Golden ratio
grid_x = [0, 1, 1 + (1 / (golden_ratio**4)), 1 + (1 / (golden_ratio**3)), golden_ratio]
grid_y = [0, 1 / (golden_ratio**3), 1 / golden_ratio**3 + 1 / golden_ratio**4, 1 / (golden_ratio**2), 1]

# Main value is based on the Fibonacci sequence
z = [
        [13, 3, 3, 5],
        [13, 2, 1, 5],
        [13, 10, 11, 12],
        [13, 8, 8, 8]
]

# Group all data sets in a single array
data = [
    {
        "z": z,
    },
    {
        "x": numpy.sort(grid_x),
        "y": numpy.sort(grid_y)
    },
    {
        "xSpiral": -x + x[0],
        "ySpiral": y - y[0],
    }
]

# Axis template: hide all ticks, lines and labels
axis = {
    "range": [0, 2.0],
    "showgrid": False,
    "zeroline": False,
    "showticklabels": False,
    "ticks": "",
    "title": ""
}

layout = {
    # Use the axis template for both x and y axes
    "xaxis": axis,
    "yaxis": axis
}

options = {
    # Hide the color scale of the heatmap
    "showscale": False
}

# Chart holds two traces, with different types
types = [ "heatmap", "scatter" ]
# x and y values for both traces
xs = ["1/x", "2/xSpiral"]
ys = ["1/y", "2/ySpiral"]
```

Here is how the chart is declared:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type={types}|z[1]=0/z|x={xs}|y={ys}|layout={layout}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="{types}" z[1]="0/z" x="{xs}" y="{ys}" layout="{layout}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="{types}", z[1]="0/z", x="{xs}", y="{ys}", layout="{layout}", options="{options}")
        ```

Note that we need to create two separate traces, with two different types ("heatmap" and "scatter") listed in *types*.<br/>
The data that defines those two traces are retrieved from *data* using their corresponding
index and column names.

The image that you get looks like the following:
<figure>
    <img src="../heatmap-drawing-on-top-d.png" class="visible-dark" />
    <img src="../heatmap-drawing-on-top-l.png" class="visible-light" />
    <figcaption>The Golden spiral</figcaption>
</figure>
