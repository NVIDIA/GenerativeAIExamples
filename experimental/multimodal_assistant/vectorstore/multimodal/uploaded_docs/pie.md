---
hide:
  - navigation
---

# Pie charts

A pie chart is a circular graphic divided into slices representing a numerical quantity.
The arc length of each slice is proportional to the quantity it represents.

You must set the [*type*](../chart.md#p-type) property of the chart control
to "pie" to create a pie chart.

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `pie`     |  |
| [*labels*](../chart.md#p-labels)            | Slice labels |  |
| [*values*](../chart.md#p-values)            | Slice values  |  |
| [*marker*](../chart.md#p-marker)    | dictionary  | `colors` can be defined as an array of color names or values. |
| [*options*](../chart.md#p-options)  | dictionary  | `textinfo` can be set to customize how texts are displayed (see [*textinfo* reference](https://plotly.com/javascript/reference/#pie-textinfo) for details).  |
| [*layout*](../chart.md#p-layout)  | dictionary  | `showlegend` can be set to False to hide the legend.<br/>`annotations` can hold text annotations that are displayed in the chart control.  |

## Examples

### Simple pie chart {data-source="gui:doc/examples/charts/pie-simple.py"}

In this example, we want to represent the area covered by forests around the world. Only the
first few countries are represented since too many would make the chart unreadable.

Our data set indicates, for every listed country, how much land is covered by
forests in thousands of hectares. This data was copied from the [FAO](https://www.fao.org)
site for 2020.<br/>
Here is how the data set is defined in our code:
```python
data = {
  "Country": ["Rest of the world","Russian Federation",...,"Peru"],
  "Area": [1445674.66,815312,...,72330.4]
}
```

We can indicate the color of each individual slice using the *layout* property of the chart:

And the chart definition is the following:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=pie|values=Area|labels=Country|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="pie" values="Area" labels="Country">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="pie", values="Area", labels="Country")
        ```

Here is the resulting chart:
<figure>
    <img src="../pie-simple-d.png" class="visible-dark" />
    <img src="../pie-simple-l.png" class="visible-light"/>
    <figcaption>Simple pie chart</figcaption>
</figure>

### Styling {data-source="gui:doc/examples/charts/pie-styling.py"}

You can specify what the color of each slice should be.

Here is a sample that creates a pie chart showing all the colors of the
rainbow:
```python
n_slices = 20
# List: [1..n_slices]
# Slices are bigger and bigger
values = list(range(1, n_slices+1))

marker = {
    # Colors move around the Hue color disk
    "colors": [f"hsl({360*(i-1)/(n_slices-1)},90%,60%)" for i in values]
}

options = {
    # Hide the texts
    "textinfo": "none"
}

layout = {
    # Hide the legend
    "showlegend": False
}
```

The data set is the simple array *values*.

The dictionary *marker* is where you can define an array of color names or
values in the *colors* property.

*options* is used to hide the texts of the pie chart, and the setting of
*layout["showlegend"]* removes the legend.

The chart definition uses all these variables:
!!! example "Definition"

    === "Markdown"

        ```
        <|{values}|chart|type=pie|marker={marker}|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="pie" marker="{marker}" options="{options}" layout="{layout}">{values}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{values}", type="pie", marker="{marker}", options="{options}", layout="{layout}")
        ```

The colored pie chart renders as follows:
<figure>
    <img src="../pie-styling-d.png" class="visible-dark" />
    <img src="../pie-styling-l.png" class="visible-light"/>
    <figcaption>Styling</figcaption>
</figure>

### Multiple charts {data-source="gui:doc/examples/charts/pie-multiple.py"}

You can create a chart control that holds several pie charts and display
them together.

Here is an example that creates two pie charts sitting side by side
in the same chart control:
```python
# List of countries, used as labels in the pie charts
countries = [
        "US", "China", "European Union", "Russian Federation",
        "Brazil", "India", "Rest of World"
]

data = [
    {
        # Values for GHG Emissions
        "values": [16, 15, 12, 6, 5, 4, 42],
        "labels": countries
    },
    {
        # Values for CO2 Emissions
        "values": [27, 11, 25, 8, 1, 3, 25],
        "labels": countries
    }
]

options = [
    # First pie chart
    {
        # Show label value on hover
        "hoverinfo": "label",
        # Leave a hole in the middle of the chart
        "hole": 0.4,
        # Place the trace on the left side
        "domain": {"column": 0}
    },
    # Second pie chart
    {
        # Show label value on hover
        "hoverinfo": "label",
        # Leave a hole in the middle of the chart
        "hole": 0.4,
        # Place the trace on the right side
        "domain": {"column": 1}
    }
]

layout = {
    # Chart title
    "title": "Global Emissions 1990-2011",
    # Show traces in a 1x2 grid
    "grid": {
        "rows": 1,
        "columns": 2
    },
    "annotations": [
        # Annotation for the first trace
        {
            "text": "GHG",
            "font": {
                "size": 20
            },
            # Hide annotation arrow
            "showarrow": False,
            # Move to the center of the trace
            "x": 0.18,
            "y": 0.5
        },
        # Annotation for the second trace
        {
            "text": "CO2",
            "font": {
                "size": 20
            },
            "showarrow": False,
            # Move to the center of the trace
            "x": 0.81,
            "y": 0.5
        }
    ],
    "showlegend": False
}
```

The *options* dictionary configures three aspects of the resulting chart:

- *hoverinfo* indicates that the hover text will be the slice's label;
- *hole* creates a hole in the middle of the pie chart;
- *domain* locates the trace in the first column of the two declared in the *layout*
  object.

The *layout* dictionary has the *grid* that indicates the global layout of the traces
within this chart control.<br/>
The property *annotation* is also specified to add the text at the center of the traces.

Here is the chart definition that uses all those settings:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=pie|x[1]=0/values|x[2]=1/values|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="pie" x[1]="0/values" x[2]="1/values" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="pie", x[1]="0/values", x[2]="1/values", options="{options}", layout="{layout}")
        ```

Here is the resulting display:
<figure>
    <img src="../pie-multiple-d.png" class="visible-dark" />
    <img src="../pie-multiple-l.png" class="visible-light"/>
    <figcaption>Multiple pie charts</figcaption>
</figure>
