---
hide:
  - navigation
---

# Histograms

A histogram is a graphical representation that arranges a group of data into
user-specified ranges. Similar to a [bar chart](bar.md), a histogram converts
a data series into an easily interpreted visual by grouping many data points into logical ranges or *bins*.<br/>
Histograms are typically used to approximately represent the distribution of
some data.

To create a histogram, the chart control must have its [*type*](../chart.md#p-type)
property for a trace set to "histogram".

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `histogram`          |  |
| [*x*](../chart.md#p-x)            | x values           |  |
| [*y*](../chart.md#p-y)            | y values           |  |
| [*layout*](../chart.md#p-layout)  | dictionary  | *barmode* can be used to indicate how to show values in the same bin. |
| [*options*](../chart.md#p-options)  | dictionary  | *cumulative* can be used to accumulate data count.<br/>*histnorm* can be set to a value that normalizes data.<br/>*histfunc* can indicate a binning function. |

## Examples

### Simple histogram {data-source="gui:doc/examples/charts/histogram-simple.py"}

The simplest histogram would use a data set and represent the number of
data points that fall in a given bin (between two fixed values).

Let us create an array of random numbers that represent a Gaussian distribution:
```python
data = [random.gauss(0, 5) for i in range(1000)]
```

Now the chart control definition can be as simple as:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram")
        ```

This would produce the image below:
<figure>
    <img src="../histogram-simple-d.png" class="visible-dark" />
    <img src="../histogram-simple-l.png" class="visible-light"/>
    <figcaption>Simple histogram</figcaption>
</figure>

Note that the label under the x axis appears as '0'. That's because we
did not name our data set.<br/>
To have a more appealing x axis label, we could have defined *data*
as a dictionary:
```python
data = {
  "Input": [random.gauss(0, 5) for i in range(1000)]
}
```

Then Taipy would have been able to extract the name of the data set and
use it as the axis label (as you can see in the following example).

### Horizontal histogram {data-source="gui:doc/examples/charts/histogram-horizontal.py"}

To display a histogram horizontally (where the values count appear in horizontal bars),
we can simply set the data set as the value of the [*y*](../chart.md#p-y) property
of the chart control (instead of [*x*](../chart.md#p-x)).

Let us create a data set (same as above, really):
```python
data = {
    "Count": [random.random() for i in range(100)]
}
```

And use it in your chart control, as a *y* value this time:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|y=Count|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" y="Count">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", y="Count")
        ```

The resulting chart looks as follows:
<figure>
    <img src="../histogram-horizontal-d.png" class="visible-dark" />
    <img src="../histogram-horizontal-l.png" class="visible-light"/>
    <figcaption>Horizontal histogram</figcaption>
</figure>

### Overlying data sets {data-source="gui:doc/examples/charts/histogram-overlay.py"}

You can display several data sets in the same histogram. One way of representing
this would be to overlay the two histogram displays (and apply some transparency
so that all data sets remain visible).

To overlay the data set traces, you need to set the *barmode* property of
[*layout*](../chart.md#p-layout) to "overlay".


Let us create an array of two random data sets then prepare the objects that customize
the histogram chart:
```python
# Data is made of two random data sets
data = [
    {
        "x": [random.random() + 1 for i in range(100)]
    },
    {
        "x": [random.random() + 1.1 for i in range(100)]
    }
]

options = [
    # First data set is displayed with semi-transparent, green bars
    {
        "opacity": 0.5,
        "marker": { "color": "green" }
    },
    # Second data set is displayed with semi-transparent, gray bars
    {
        "opacity": 0.5,
        "marker": { "color": "#888" }
    }
]

layout = {
    # Overlay the two histograms
    "barmode": "overlay",
    # Hide the legend
    "showlegend": False
}
```

And let's define our chart using these settings:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", options="{options}", layout="{layout}")
        ```

Here is what the resulting chart looks like:
<figure>
    <img src="../histogram-overlay-d.png" class="visible-dark" />
    <img src="../histogram-overlay-l.png" class="visible-light"/>
    <figcaption>Overlaid data sets</figcaption>
</figure>

### Stacked data sets {data-source="gui:doc/examples/charts/histogram-stacked.py"}

Histograms can also represent different data sets accumulating their bin
counts on top of one another.<br/>
The *barmode* property of the value set to the [*layout*](../chart.md#p-layout) must
be set to "stack" to achieve this.

Using the two random data sets defined by:
```python
# Array of two data sets
data = {
    "A": [random.random() for i in range(200)],
    "B": [random.random() for i in range(200)]
}

# Names of the two traces
names  = [
    "A samples",
    "B samples"
]

layout = {
    # Make the histogram stack the data sets
    "barmode": "stack"
}
```

The chart control definition would reference those objects:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|x[1]=A|x[2]=B|name={names}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" x[1]="A" x[2]="B" name="{names}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", x[1]="A", x[2]="B", name="{names}", layout="{layout}")
        ```

To result in the following figure:
<figure>
    <img src="../histogram-stacked-d.png" class="visible-dark" />
    <img src="../histogram-stacked-l.png" class="visible-light"/>
    <figcaption>Stacked data sets</figcaption>
</figure>

### Cumulative histogram {data-source="gui:doc/examples/charts/histogram-cumulative.py"}

Histograms can also represent the sum of the number of observations, bin after
bin.<br/>
Taipy can represent such a histogram using the *cumulative* property of the value set
to the [*options*](../chart.md#p-options) chart control property.

```python
# Random data set
data = [random.random() for i in range(500)]

options = {
    # Enable the cumulative histogram
    "cumulative": {
        "enabled": True
    }
}
```

The chart control is defined as:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", options="{options}")
        ```

The resulting chart looks like this:
<figure>
    <img src="../histogram-cumulative-d.png" class="visible-dark" />
    <img src="../histogram-cumulative-l.png" class="visible-light"/>
    <figcaption>Cumulative histogram</figcaption>
</figure>

It's no surprise to see the count grow to 500, which is the size of
our initial data set.

### Normalized histogram {data-source="gui:doc/examples/charts/histogram-normalized.py"}

Instead of displaying the count of bins, histograms can also be customized to display
the proportion of each bin.<br/>
To achieve this, set the *histnorm* property of the value set to the
[*options*](../chart.md#p-options) chart control property to what would be relevant
in your situation (see the
[histnorm documentation](https://plotly.com/javascript/reference/#histogram2d-histnorm)
on the Plotly site for details).

We can define a random data set and the histogram options with this code:
```python
# Random data set
data = [random.random() for i in range(100)]

# Normalize to show bin probabilities
options = {
    "histnorm": "probability"
}
```

And use those in the definition for our histogram chart:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", options="{options}")
        ```

Here is what the chart looks like:
<figure>
    <img src="../histogram-normalize-d.png" class="visible-dark" />
    <img src="../histogram-normalize-l.png" class="visible-light"/>
    <figcaption>Normalized histogram</figcaption>
</figure>

### Specifying the binning function {data-source="gui:doc/examples/charts/histogram-binning-function.py"}

Histograms usually represent the count of observations for each bin. However, you
may want to reflect other information on the data set, such as how many times
a given bin appears in the data instead of the usual cumulated quantity in each
bin.

Here is the code that we can use to reflect that functionality:
```python
# Initial data set. y = count_of(x)
samples = {
    "x": ["Apples", "Apples", "Apples", "Oranges", "Bananas", "Oranges"],
    "y": [5, 10, 3, 8, 5, 2]
}

# Create a data set array to allow for two traces
data = [ samples, samples ]

# Gather those settings in a single dictionary
properties = {
    # 'x' of the first trace is the 'x' data from the first element of data
    "x[1]": "0/x",
    # 'y' of the first trace is the 'y' data from the first element of data
    "y[1]": "0/y",
    # 'x' of the second trace is the 'x' data from the second element of data
    "x[2]": "1/x",
    # 'y' of the second trace is the 'y' data from the second element of data
    "y[2]": "1/y",
    # Data set colors
    "color": ["#cd5c5c", "#505070"],
    # Data set names (for the legend)
    "name": ["Count", "Sum"],
    # Configure the binning functions
    "options": [
        # First trace: count the bins
        {"histfunc": "count"},
        # Second trace: sum the bin occurences
        {"histfunc": "sum"}
    ],
    # Set x axis name
    "layout": {"xaxis": {"title": "Fruit"}}
}
```

Note what *options* indicates: the first trace will represent how many instances of
the bin name (the name of the fruit, in *x*) appear in the first data set. The second
trace will sum the *y* values for each bin.

Because there are quite a few settings, we group them in a single dictionary that we
can then use as the value to the property [*properties*](../chart.md#p-properties) of
the chart control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", properties="{properties}")
        ```

The page shows:
<figure>
    <img src="../histogram-binning-function-d.png" class="visible-dark" />
    <img src="../histogram-binning-function-l.png" class="visible-light"/>
    <figcaption>Different binning-functions</figcaption>
</figure>

### Tuning bins {data-source="gui:doc/examples/charts/histogram-nbins.py"}

Histograms can be customized to force the number of bins that Plotly
computes when facing data sets.<br/>
Use the *nbinsx* property of the dictionary set to the
[*options*](../chart.md#p-options) chart control property to tune that
number.

Here is the code we are using in this example:
```python
# Random set of 100 samples
samples = { "x": [random.gauss() for i in range(100)] }

# Use the same data for both traces
data = [ samples, samples ]

options = [
    # First data set displayed as green-ish, and 5 bins
    {
        "marker": {"color": "#4A4"},
        "nbinsx": 5
    },
    # Second data set displayed as red-ish, and 25 bins
    {
        "marker": {"color": "#A33"},
        "nbinsx": 25
    }
]

layout = {
    # Overlay the two histograms
    "barmode": "overlay",
    # Hide the legend
    "showlegend": False
}
```

We will use those objects in the definition for the chart control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=histogram|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="histogram" options="{options}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="histogram", options="{options}", layout="{layout}")
        ```

To generate the following chart:
<figure>
    <img src="../histogram-nbins-d.png" class="visible-dark" />
    <img src="../histogram-nbins-l.png" class="visible-light"/>
    <figcaption>Tuning the number of bins</figcaption>
</figure>

We can see that the green trace accumulates the values represented in the
red one.
