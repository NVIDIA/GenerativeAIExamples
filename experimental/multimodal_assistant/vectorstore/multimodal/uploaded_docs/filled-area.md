---
hide:
  - navigation
---

# Filled areas

An area chart displays a solid-colored area between the traces.

To get a filled area chart, we must set the *fill* property of the dictionary
used as the chart's [*options*](../chart.md#p-options) property to a value
that indicates how you want to perform the fill.<br/>
This value can be one of "none", "tozeroy", "tozerox" , "tonexty", "tonextx", "toself",
or "tonext", as indicated in the
[Scatter fill](https://plotly.com/javascript/reference/scatter/#scatter-fill) section
of the Plotly documentation

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `scatter`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*options*](../chart.md#p-options)  | dictionary  | `fill` indicates how to perform the fill.<br/>`stackgroup` indicates the name of the stack group to associate the trace with. |

## Examples

### Simple filled area chart {data-source="gui:doc/examples/charts/filled-area-simple.py"}

Here is how we can create a filled area chart to represent the number of items sold every
weekday:
```python
data = {
    "Day":   ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    "Items": [32, 25, 86, 60, 70],
}

options = {
    # Fill to x axis
    "fill": "tozeroy"
}
```

The chart control definition is straightforward:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=Day|y=Items|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="Day" y="Items" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="Day", y="Items", options="{options}")
        ```

Note that we have not set the [*type*](../chart.md#p-type) property, which defaults to
"scatter". This is what we want for our filled area chart.

The resulting chart is displayed as follows:
<figure>
    <img src="../filled-area-simple-d.png" class="visible-dark" />
    <img src="../filled-area-simple-l.png" class="visible-light" />
    <figcaption>Filled area chart</figcaption>
</figure>

### Overlayed filled areas {data-source="gui:doc/examples/charts/filled-area-overlay.py"}

Suppose we want also to visualize the price of the items.<br/>
One way of doing this could be to overlay the two traces on top of each other.

Here is an example that does just that:
```python
data = {
    "Day":   [ "Mon", "Tue", "Wed", "Thu", "Fri" ],
    "Items": [ 32, 25, 86, 60, 70],
    "Price": [ 80, 50, 140, 10, 70],
}

options = [
    # For items
    {"fill": "tozeroy"},
    # For price
    # Using "tonexty" not to cover the first trace
    {"fill": "tonexty"}
]
```

We now have two data sets (Items and Price) that we want to display in the same
chart, using overlay.

The *options* dictionary holds the *fill* setting for both traces.

Let's use that in our chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=none|x=Day|y[1]=Items|y[2]=Price|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="none" x="Day" y[1]="Items" y[2]="Price" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="none", x="Day", y[1]="Items", y[2]="Price", options="{options}")
        ```

Note that we set *mode* to "none" in order to remove the dots that would otherwise be
displayed at each data point.

Here is what the result looks like:
<figure>
    <img src="../filled-area-overlay-d.png" class="visible-dark" />
    <img src="../filled-area-overlay-l.png" class="visible-light" />
    <figcaption>Overlay of Area Charts</figcaption>
</figure>

### Stacked Area Chart {data-source="gui:doc/examples/charts/filled-area-stacked.py"}

Multiple traces in a filled area chart can also be displayed as a stack of traces.

To do this, you need to set the *stackgroup* of the dictionary set to
the [*options*](../chart.md#p-options) property of the chart control to a group name.

Here is some code that demonstrates this:
```python
data = {
    "Month":  [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ],
    "Milk":   [ 80, 85, 95, 120, 140, 130, 145, 150, 120, 100, 90, 110 ],
    "Bread":  [ 100, 90, 85, 90, 100, 110, 105, 95, 100, 110, 120, 125 ],
    "Apples": [ 50, 65, 70, 65, 70, 75, 85, 70, 60, 65, 70, 80 ]
}

# Name of the three sets to trace
items = ["Milk", "Bread", "Apples"]

options = {
    # Group all traces in the same stack group
    "stackgroup": "first_group"
}
```

The chart control definition will use that dictionary:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=none|x=Month|y={items}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="none" x="Month" y="{items}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="none", x="Month", y="{items}", options="{options}")
        ```

Here is the resulting display:
<figure>
    <img src="../filled-area-stacked-d.png" class="visible-dark" />
    <img src="../filled-area-stacked-l.png" class="visible-light" />
    <figcaption>Stacking areas</figcaption>
</figure>

### Normalized Stacked Area Chart {data-source="gui:doc/examples/charts/filled-area-normalized.py"}

Normalizing a stacked area chart makes it easy to visualize relative quantities
among different data. All values for a given 'x' value are displayed as a
percentage of the overall total.

Suppose we want to show the ratio of cosmetic products sales across different regions in
a hypothetic company:
```python
data = {
    "Products": [
        "Nail polish", "Eyebrow pencil", "Rouge", "Lipstick",
        "Eyeshadows", "Eyeliner", "Foundation", "Lip gloss", "Mascara"
    ],
    "USA": [ 12814, 13012, 11624, 8814, 12998, 12321, 10342, 22998, 11261 ],
    "China": [ 3054, 5067, 7004, 9054, 12043, 15067, 10119, 12043, 10419 ],
    "EU": [ 4376, 3987, 3574, 4376, 4572, 3417, 5231, 4572, 6134 ],
    "Africa": [ 4229, 3932, 5221, 9256, 3308, 5432, 13701, 4008, 18712 ]
}

# Order the different traces
ys = [ "USA", "China", "EU", "Africa" ]

options = [
    # For the USA
    { "stackgroup": "one", "groupnorm": "percent" },
    # For China
    { "stackgroup": "one" },
    # For the EU
    { "stackgroup": "one" },
    # For Africa
    { "stackgroup": "one" }
]

layout = {
    # Show all values when hovering on a data point
    "hovermode": "x unified"
}
```

Note how the first trace's options have the *groupnorm* property set to "percent".

Here is how we would define our chart control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=none|x=Products|y={ys}|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="none" x="Products" y="{ys}" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="none", x="Products", y="{ys}", options="{options}", layout="{layout}")
        ```

The chart looks like this:
<figure>
    <img src="../filled-area-normalized-d.png" class="visible-dark" />
    <img src="../filled-area-normalized-l.png" class="visible-light" />
    <figcaption>Normalized Stacked Area Chart</figcaption>
</figure>
