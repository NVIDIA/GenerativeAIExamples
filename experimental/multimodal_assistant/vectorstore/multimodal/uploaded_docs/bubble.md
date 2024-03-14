---
hide:
  - navigation
---

# Bubble charts

Bubble charts are a type of [scatter chart](scatter.md) where marker sizes and colors are depending
on the data: columns in the data set are used to retrieve the values for the color and size of each
data point representation, using the [*marker*](../chart.md#p-marker) property of the chart control.

The [*mode*](../chart.md#p-mode) property needs to be set to "markers" so that only
the data points get rendered.

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `scatter`          | Default value  |
| [*mode*](../chart.md#p-mode)      | `markers`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*marker*](../chart.md#p-marker)  | dictionary  | `size` can be set to a column name in *data*.<br/>`color` can be set to a column name in *data* that holds color names or values.<br/>`symbol` can be set to a column name in *data* that holds symbol names (see [Symbol names](https://plotly.com/javascript/reference/scatter/#scatter-marker-symbol) for details).<br/>`opacity` can be set to a column name in *data* that holds an opacity value between 0 and 1.  |

## Examples

### Simple bubble chart {data-source="gui:doc/examples/charts/bubble-simple.py"}

A simple use case for bubble charts is a data set where data points have a related color,
size, and opacity to be applied for their representation.

Here is a small example of this:
```python
data = {
    "x": [1, 2, 3],
    "y": [1, 2, 3],
    "Colors": ["blue", "green", "red"],
    "Sizes": [20, 40, 30],
    "Opacities": [1, .4, 1]
}

marker = {
    "color": "Colors",
    "size": "Sizes",
    "opacity": "Opacities"
}
```

The dictionary *marker* indicates the name of the columns from the data set that
are used to set the color, size, and opacity of each data point representation.

The chart definition looks like this:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|x=x|y=y|marker={marker}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" x="x" y="y" marker="{marker}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", x="x", y="y", marker="{marker}")
        ```

The result looks like this:
<figure>
    <img src="../bubble-simple-d.png" class="visible-dark" />
    <img src="../bubble-simple-l.png" class="visible-light"/>
    <figcaption>Simple bubble chart</figcaption>
</figure>

### Setting data point symbols {data-source="gui:doc/examples/charts/bubble-symbols.py"}

Setting the symbol that is used for every data point is a matter of setting
the *symbol* property of the dictionary used in the chart control's
[*marker*](../chart.md#p-marker) property.

Here is an example that demonstrates this:
```python
data = {
    "x": [1, 2, 3, 4, 5],
    "y": [10, 7, 4, 1, 5],
    "Sizes": [20, 30, 40, 50, 30],
    "Symbols": [
        "circle-open", "triangle-up", "hexagram",
        "star-diamond", "circle-cross"
    ]
}

marker = {
    "color": "#77A",
    "size": "Sizes",
    "symbol": "Symbols",
}
```

The chart definition remains exactly the same as in the example above:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|x=x|y=y|marker={marker}|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" x="x" y="y" marker="{marker}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", x="x", y="y", marker="{marker}")
        ```

And the resulting chart looks like this:
<figure>
    <img src="../bubble-symbols-d.png" class="visible-dark" />
    <img src="../bubble-symbols-l.png" class="visible-light"/>
    <figcaption>Bubble chart symbols</figcaption>
</figure>

### Hover text {data-source="gui:doc/examples/charts/bubble-hover.py"}

You can customize the text that would appear should the user move the pointing
device on top of a data point symbol.<br/>
This is known as the *hover text*, and a series of text values can be set
to the [*text*](../chart.md#p-text) property of the chart control to indicate
what this text should be, for every data point.

Here is some code that defines hover texts for a bubble chart:
```python
data = {
    "x": [1, 2, 3],
    "y": [1, 2, 3],
    "Texts": [
        "Blue<br>Small",
        "Green<br>Medium",
        "Red<br>Large"],
    "Sizes":  [60, 80, 100],
    "Colors": [
        "rgb(93, 164, 214)",
        "rgb(44, 160, 101)",
        "rgb(255, 65, 54)",
    ]
}

marker = {
    "size": "Sizes",
    "color": "Colors"
}
```

The chart definition needs to set the [*text*](../chart.md#p-text) property to the
proper column name:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|mode=markers|x=x|y=y|marker={marker}|text=Texts|>
        ```

    === "HTML"

        ```html
        <taipy:chart mode="markers" x="x" y="y" marker="{marker}" text="Texts">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", mode="markers", x="x", y="y", marker="{marker}", text="Texts")
        ```

Here is the result:
<figure>
    <img src="../bubble-hover-d.png" class="visible-dark" />
    <img src="../bubble-hover-l.png" class="visible-light"/>
    <figcaption>Hover texts</figcaption>
</figure>
