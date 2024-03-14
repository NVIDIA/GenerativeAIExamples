---
hide:
  - navigation
---

# Radar charts

A radar chart (sometimes called a Spider chart or a web chart) is a kind of
[polar chart](polar.md) that does not use explicit angular value to indicate the location
of data points.<br/>
Instead, radar charts use a categorical variable that is uniformly projected along the
angular axis. A data point is represented using its radial value (usually the quantity
or magnitude) and the angle associated with the category of the second variable.

Just like for [polar charts](polar.md), radar charts must have the
[*type*](../chart.md#p-type) property of the chart control set to "scatterpolar".<br/>
The [*r*](../chart.md#p-r) and [*theta*](../chart.md#p-theta) properties are still used
to indicate the data sets but here, *theta* is set to the value of a category. The
radar chart automatically arranges all categories along the angular axis.

## Key properties

| Name            | Value            | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)       | `scatterpolar`  |  |
| [*r*](../chart.md#p-r)             | radial values   |  |
| [*theta*](../chart.md#p-theta)     | angular values  | As categorical values.  |
| [*options*](../chart.md#p-options) | dictionary  | `fill` can be used to fill traces.  |

## Examples

### Simple radar chart {data-source="gui:doc/examples/charts/radar-simple.py"}

Here is an example that demonstrates the use of a radar chart to display
the relative usage of programming languages among developers:
```python
data = {
    # List of programming languages
    "Language": [
        "JavaScript", "HTML/CSS", "SQL", "Python",
        "Typescript", "Java", "Bash/Shell"
    ],
    # Percentage of usage, per language
    "%": [65.36, 55.08, 49.43, 48.07, 34.83, 33.27, 29.07]
}

# Close the shape for a nice-looking stroke
# If the first point is *not* appended to the end of the list,
# then the shape does not look as it is closed.
data["%"].append(data["%"][0])
data["Language"].append(data["Language"][0])

layout = {
    "polar": {
        "radialaxis": {
            # Force the radial range to 0-100
            "range": [0, 100],
        }
    },
    # Hide legend
    "showlegend": False
}

options = {
    # Fill the trace
    "fill": "toself"
}
```

Here is the chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|r=%|theta=Language|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" r="%" theta="Language" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", r="%", theta="Language", options="{options}", layout="{layout}")
        ```

Here is the resulting figure:
<figure>
    <img src="../radar-simple-d.png" class="visible-dark" />
    <img src="../radar-simple-l.png" class="visible-light" />
    <figcaption>Simple radar chart</figcaption>
</figure>

### Multiple data sets {data-source="gui:doc/examples/charts/radar-multiple.py"}

Radar charts are handy when used to compare two data sets: one can immediately spot
where a given data set performs better or worse than another for a given category.

This example shows how to use a radar chart that displays two distinct data sets using
the same categories:
```python
# Skill categories
skills=["HTML", "CSS", "Java", "Python", "PHP", "JavaScript", "Photoshop"]
data = [
    # Proportion of skills used for Backend development
    {
        "Backend": [10, 10, 80, 70, 90, 30, 0],
        "Skills": skills
    },
    # Proportion of skills used for Frontend development
    {
        "Frontend": [90, 90, 0, 10, 20, 80, 60],
        "Skills": skills
    }
]

# Append first elements to all arrays for a nice stroke
skills.append(skills[0])
data[0]["Backend"].append(data[0]["Backend"][0])
data[1]["Frontend"].append(data[1]["Frontend"][0])

layout = {
    # Force the radial axis displayed range
    "polar": { "radialaxis": { "range": [0, 100] } }
}

# Fill the trace
options = {"fill": "toself"}

# Reflected in the legend
names = ["Backend", "Frontend"]

# To shorten the chart control definition
r     = ["0/Backend", "1/Frontend"]
theta = ["0/Skills",  "1/Skills"]
```

The chart definition uses all those different objects:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|name={names}|r={r}|theta={theta}|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" name="{names}" r="{r}" theta="{theta}" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", name="{names}", r="{r}", theta="{theta}", options="{options}", layout="{layout}")
        ```

The chart created above looks like this:
<figure>
    <img src="../radar-multiple-d.png" class="visible-dark" />
    <img src="../radar-multiple-l.png" class="visible-light" />
    <figcaption>Backend vs. Frontend skills</figcaption>
</figure>
