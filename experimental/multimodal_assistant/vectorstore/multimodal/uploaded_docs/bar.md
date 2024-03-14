---
hide:
  - navigation
---

# Bar charts

Bar charts can be handy when you need to compare data points
next to one another and look at a global change over time.

Taipy creates a bar chart when the [*type*](../chart.md#p-type) property for a trace
in the chart control is set to "bar".

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `bar`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*orientation*](../chart.md#p-orientation)  | `"v"` or `"h"`  | The orientation of the trace. |
| [*layout*](../chart.md#p-layout)  | dictionary  | `barmode` can be used to indicate how to show values at the same coordinates. |

## Examples

### Simple bar chart {data-source="gui:doc/examples/charts/bar-simple.py"}

Here is an example of how to use bar charts in an application.

You want to display the popular vote percentage for every presidential
election in the US since 1852 (source
[Wikipedia](https://en.wikipedia.org/wiki/List_of_United_States_presidential_elections_by_popular_vote_margin])).

The Python code will look like this:
```python
percentages=[(1852,50.83), (1856,45.29), ..., (2016,46.09), (2020,51.31)]
data = pandas.DataFrame(percentages, columns= ["Year", "%"])
```

A Pandas DataFrame is built from a list of tuples that hold the election year
and the percentage of votes the winner has received globally.

The definition of a bar chart that represents this data will look like this:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|x=Year|y=%|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" x="Year" y="%">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", x="Year", y="%")
        ```

All we did is set the [*type*](../chart.md#p-type) property to "bar", and the
following chart is displayed on the page (the blue color is not related to what
party the elected president belongs to - it is just the default color that Plotly
has picked up):
<figure>
    <img src="../bar-simple-d.png" class="visible-dark" />
    <img src="../bar-simple-l.png" class="visible-light"/>
    <figcaption>Simple bar chart</figcaption>
</figure>

### Multiple data sets {data-source="gui:doc/examples/charts/bar-multiple.py"}

Say you want to display the score of the winning side next to the
score of the losing side.

Starting with a smaller version of the data set used above, you can write:
```python
percentages=[(1852,50.83), (1856,45.29), ..., (1924,54.04), (1928,58.21)]
data = pandas.DataFrame(percentages, columns= ["Year", "Won"])
# Add the Lost column (100-Won)
data["Lost"] = [100-t[1] for t in percentages]
```

We add a new column to the DataFrame *data*, which is the complement to 100
of *percentages*.

To represent it, we will change the definition of the chart control, splitting
the two data sets to be represented in *y[1]* and *y[2]*.

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|x=Year|y[1]=Won|y[2]=Lost|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" x="Year" y[1]="Won" y[2]="Lost">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", x="Year", y[1]="Won", y[2]="Lost")
        ```

Here is how this new data set is represented:
<figure>
    <img src="../bar-multiple-d.png" class="visible-dark" />
    <img src="../bar-multiple-l.png" class="visible-light"/>
    <figcaption>Multiple data sets</figcaption>
</figure>

### Stacked bar chart {data-source="gui:doc/examples/charts/bar-stacked.py"}

When different data sets are available from the same set of *x* values, it
may be relevant to stack those values in the same bar.

We are reusing the same DataFrame as in the example above.

To indicate that we want a stacked representation, you must
create a *layout* dictionary:
```python
layout={ "barmode": "stack" }
```

And use this dictionary in the definition of the chart:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|x=Year|y[1]=Won|y[2]=Lost|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" x="Year" y[1]="Won" y[2]="Lost" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", x="Year", y[1]="Won", y[2]="Lost", layout="{layout}")
        ```

Here is the resulting image:
<figure>
    <img src="../bar-stacked-d.png" class="visible-dark" />
    <img src="../bar-stacked-l.png" class="visible-light"/>
    <figcaption>Stacked bar charts</figcaption>
</figure>

And each bar adds up to 100, as expected.

### Facing bar charts {data-source="gui:doc/examples/charts/bar-facing.py"}

It's sometimes helpful to display two bar charts facing each other 
so comparing data is more manageable.

This example creates a chart that shows the ratio of men and women
practicing certain activities as hobbies. We want a vertical scale
representing the different hobbies and the proportion of individuals
enjoying that activity on each side of a common vertical axis, represented
as two horizontal bars facing each other.

We have a DataFrame that holds the information we want to represent:
```python
data = pd.DataFrame({
    "Hobbies": [
        "Archery", "Tennis", "Football", "Basket", "Volley",
        "Golf", "Video-Games", "Reading", "Singing", "Music" ],
    "Female": [0.4, ..., 0.63],
    "Male":   [-0.39, ..., -0.6]
})
```
Note how we negated the values for the Male data so they are properly
located on the *x* axis.

The chart control definition for this example is slightly more complex than
in the previous examples. It is clearer to store the properties and their
value in a single dictionary, which we will later use as the value for the
[*properties*](../chart.md#p-properties) control property.

Here is our property dictionary:
```python
properties = {
    # Shared y values
    "y":              "Hobbies",
    # Bars for the female data set
    "x[1]":           "Female",
    "color[1]":       "#c26391",
    # Bars for the male data set
    "x[2]":           "Male",
    "color[2]":       "#5c91de",
    # Both data sets are represented with an horizontal orientation
    "orientation":    "h",
    # 
    "layout": {
        "barmode": "overlay",
        # Set a relevant title for the x axis
        "xaxis": { "title": "Gender" },
        # Hide the legend
        "showlegend": False
    }
}
```
Note how to define our two *x* sets of values (in *x[1]* and *x[2]*). The
*orientation[]* property is used to change the orientation of the bars in
our chart.

Also, note that the *layout* property is set as well: we indicate in its
*barmode* property that the two charts should share the same y coordinates,
and we hide the legend using the *showlegend* property.

Now let's use this dictionary in the definition of the chart:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", properties="{properties}")
        ```

Here is the result:
<figure>
    <img src="../bar-facing-d.png" class="visible-dark" />
    <img src="../bar-facing-l.png" class="visible-light"/>
    <figcaption>Facing bar charts</figcaption>
</figure>
