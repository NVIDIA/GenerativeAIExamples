---
hide:
  - navigation
---

# Basic concepts

This section explains how the chart control can used be used to represent data
in different situations. It also shows basic customization hints.

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `bar`          |  |
| [*data*](../chart.md#p-data)      | Array, dictionary or Pandas DataFrame.         |  |
| [*x*](../chart.md#p-x), [*y*](../chart.md#p-y), [*z*](../chart.md#p-z), [*theta*](../chart.md#p-theta), [*r*](../chart.md#p-r), [*lat*](../chart.md#p-lat), [*lon*](../chart.md#p-lon), [*high*](../chart.md#p-high), [*low*](../chart.md#p-low), [*close*](../chart.md#p-close), [*open*](../chart.md#p-open)       | Array or column name.  | Property name depends on the base chart coordinate system.  |
| [*option*](../chart.md#p-option)  | dictionary  | Options that are specific to a trace.  |
| [*layout*](../chart.md#p-layout)  | dictionary  | Layout settings applied globally to the chart control.  |

## Examples

### Plotting a series of values {data-source="gui:doc/examples/charts/basics-simple.py"}

Say you want to create a line chart connecting a series of values.<br/>
The *x* values will be the index of each plotted value.

Our example would plot the function *y = x * x* on a small range of *x* values.
We can do that using inline Python code in the page definition text:
!!! example "Definition"

    === "Markdown"

        ```
        <|{[x*x for x in range(0, 11)]}|chart|>
        ```

    === "HTML"

        ```html
        <taipy:chart>{[x*x for x in range(0, 11)]}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{[x*x for x in range(0, 11)]}")
        ```

Here is how this chart is displayed:
<figure>
    <img src="../basics-simple-d.png" class="visible-dark" />
    <img src="../basics-simple-l.png" class="visible-light"/>
    <figcaption>Plotting a series</figcaption>
</figure>

### Defining the range for *x* {data-source="gui:doc/examples/charts/basics-xrange.py"}

The example above does not explicitly define an *x* axis: we use the index of the
*y* value in the input array.<br/>
The values for *x* can be defined as well. To do this, we must create a data set
that holds the value arrays for both *x* and *y*.

Let us create a dictionary that holds data for our two series: the
*x* and the *y* values:
```python
# x values are [-10..10]
x_range = range(-10, 11)

# The data set that holds both the x and the y values
data = {
    "X": x_range,
    "Y": [x*x for x in x_range]
}
```

The only constraint you have at this point is that all the value arrays assigned
to the dictionary's properties must be the same size.

Here is how to define the chart control that uses these two series:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=X|y=Y|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="X" y="Y">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="X", y="Y")
        ```

Taipy internally transforms the dictionary *data* to a Pandas DataFrame.

The [*x*](../chart.md#p-x) property of the chart control is set to the name of the
DataFrame column ("X") that holds the values for the *x* axis. Similarly, the
property [*y*](../chart.md#p-y) of the chart control is set to "Y", which is the
name of the column in the DataFrame where the values for *y* are stored.

The resulting image is the following:
<figure>
    <img src="../basics-xrange-d.png" class="visible-dark" />
    <img src="../basics-xrange-l.png" class="visible-light"/>
    <figcaption>Defining the plot range</figcaption>
</figure>

Note that the axes now have relevant names: because the series are named in
the source data, both the *x* and *y* axes are labeled accordingly.

### Decorating a chart {data-source="gui:doc/examples/charts/basics-title.py"}

In the first example, you may have noticed the '0' sitting under
the *x* axis. This is the 'name' of the axis. Because we were not using
any DataFrame from which column names could be used, Taipy used the index
of the data series, which is 0, since we only have one dimension in
our data.<br/>
The second example fixed that by naming the series.

However, you can provide any name of your choosing to axes.<br/>
This involves using the [*layout*](../chart.md#p-layout) layout property of
the chart control. This property must be set to a dictionary (see the
[Plotly Reference](https://plotly.com/javascript/reference/layout/) for
all the details) defined as follows:
```python
layout = {
  "xaxis": {
    # Force the title of the x axis
    "title": "Values for x"
  }
}
```

In the chart control definition, we reuse the inline data and add
a setting to use the dictionary *layout*:
!!! example "Definition"

    === "Markdown"

        ```
        <|{[x*x for x in range(0, 11)]}|chart|title=Plotting x squared|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart title="Plotting x squared" layout="{layout}">{[x*x for x in range(0, 11)]}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{[x*x for x in range(0, 11)]}", title="Plotting x squared", layout="{layout}")
        ```

As you can see, we also added a title to the chart.

The result is the following:
<figure>
    <img src="../basics-title-d.png" class="visible-dark" />
    <img src="../basics-title-l.png" class="visible-light"/>
    <figcaption>Title and x axis label</figcaption>
</figure>

### Adding a trace {data-source="gui:doc/examples/charts/basics-multiple.py"}

You will often want to display several traces in the same chart control.

For each data series, we can add a column to the DataFrame and indicate
which series to display:
```python
# x values are [-10..10]
x_range = range(-10, 11)

# The data set holds the _x_ series and two distinct series for _y_
data = {
    "x": x_range,
    # y1 = x*x
    "y1": [x*x for x in x_range],
    # y2 = 100-x*x
    "y2": [100-x*x for x in x_range]
}
```

To indicate that both *y1* and *y2* should be plotted, you must set the indexed
property [*y*](../chart.md#p-y) to each of them: *y[1]* and *y[2]* must be set
to the name of the first and the second series (i.e., "y1" and "y2") that we want
to trace.

Here is what the chart definition looks like:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=x|y[1]=y1|y[2]=y2|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="x" y[1]="y1" y[2]="y2">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="x", y[1]="y1", y[2]="y2")
        ```

Note that, looking at the HTML definition, 'y[1]' or 'y[2]' are not valid HTML attribute names.
Taipy allows this syntax, nevertheless.

And now our chart displays the two traces, one for each *y* series:
<figure>
    <img src="../basics-multiple-d.png" class="visible-dark" />
    <img src="../basics-multiple-l.png" class="visible-light"/>
    <figcaption>Two traces</figcaption>
</figure>

Note that a legend is automatically added to the chart to indicate which trace
represents which series.

If you want to change the color of a trace, you can use the
[*color*](../chart.md#p-color) property: setting *color[2]* to "red" will impact the
color of the second trace, so it is displayed in red.

### Adding a *y* axis {data-source="gui:doc/examples/charts/basics-two-y-axis.py"}

Let us look at a situation where the two *y* series use ranges that are very
different:
```python
# x values are [-10..10]
x_range = range(-10, 11)

# The data set holds the _x_ series and two distinct series for _y_
data = {
    "x": x_range,
    # y1 = x*x
    "y1": [x*x for x in x_range],
    # y2 = 2-x*x/50
    "y2": [(100-x*x)/50 for x in x_range]
}
```

The chart control definition has not changed:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=x|y[1]=y1|y[2]=y2|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="x" y[1]="y1" y[2]="y2">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="x", y[1]="y1", y[2]="y2")
        ```

Compared to the previous example, we have divided all the values of the second
*y* series by 50, resulting in a plot that is hardly readable, as you can see in
the result:
<figure>
    <img src="../basics-two-y-axis-1-d.png" class="visible-dark" />
    <img src="../basics-two-y-axis-1-l.png" class="visible-light"/>
    <figcaption>Difficult to read</figcaption>
</figure>

We need to create a second *y* axis that would provide a proper reading of the
values of the second series.

To do this, we need to add the definition of a *layout* object that can describe this
second axis and set this object to the chart control's [*layout*](../chart.md#p-layout)
property.

Here is what the definition of this object looks like:
```python
layout = {
    "yaxis2": {
      # Second axis overlays with the first y axis
      "overlaying": "y",
      # Place the second axis on the right
      "side": "right",
      # and give it a title
      "title": "Second y axis"
    },
    "legend": {
      # Place the legend above chart
      "yanchor": "bottom"
    }
}
```

This additional axis stands in the 'y' direction, to the right of the graph, and
has its own title.

To attach our second trace to that axis, we need to change our control definition,
so the *layout* dictionary is set to the [*layout*](../chart.md#p-layout) property
of the chart control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=x|y[1]=y1|y[2]=y2|yaxis[2]=y2|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="x" y[1]="y1" y[2]="y2" yaxis[2]="y2" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="x", y[1]="y1", y[2]="y2", yaxis[2]="y2", layout="{layout}")
        ```

See how we leverage the property [*yaxis*](../chart.md#p-yaxis), indicating that the
indexed trace (2) relies on the axis we have created in the chart layout.

The resulting plot is far more relevant:
<figure>
    <img src="../basics-two-y-axis-2-d.png" class="visible-dark" />
    <img src="../basics-two-y-axis-2-l.png" class="visible-light"/>
    <figcaption>Second <i>y</i> axis</figcaption>
</figure>

### Using a time series {data-source="gui:doc/examples/charts/basics-timeline.py"}

Many charts will represent data that is based on a timeline. Taipy allows you
to define an *x* axis that represents a time range.

Pandas comes in handy in this situation: in a single line of code, you can create a
series of dates based on a start date and a frequency.

Here is how you could display data based on time. In our example, we will use one
random value for each hour on a given day:
```python
data = {
    "Date": pandas.date_range("2023-01-04", periods=24, freq="H"),
    "Value": pandas.Series(numpy.random.randn(24))
}
```

Creating a chart that relies on the time series (in the *dates* column of the DataFrame)
is pretty straightforward:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=Date|y=Value|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="Date" y="Value">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="Date", y="Value")
        ```

And the result is exactly what you expect:
<figure>
    <img src="../basics-timeline-d.png" class="visible-dark" />
    <img src="../basics-timeline-l.png" class="visible-light"/>
    <figcaption>Timeline</figcaption>
</figure>
