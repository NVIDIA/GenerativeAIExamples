---
hide:
  - navigation
---

# Error bars

Error bars are located on data points and indicate the correctness of the value shown.
It is typically used when the data set is made of samples produced with measurement
devices that generate known observational errors. The measurement error
is usually both random and systematic (due to a miscalibrated instrument).

Error bars can be applied to [*line charts*](line.md),
[*scatter charts*](scatter.md) and [*bar charts*](bar.md).
To create error bars, you must provide the chart control with an [*options*](../chart.md#p-options)
value where the *error_x* or *error_y* keys are set to a valid value. Please refer to the
[Plotly documentation on error bars](https://plotly.com/javascript/reference/#scatter-error_x)
for a complete description of these settings.

## Key properties

| Name            | Value            | Notes   |
| --------------- | -------------------------- | ------------------ |
| [*type*](../chart.md#p-type)       | `scatter` or `bar`  |  |
| [*options*](../chart.md#p-options) | dictionary  | `error_x` or `error_y` add error bars to a trace.  |

## Examples

### Simple error bars {data-source="gui:doc/examples/charts/error-bars-simple.py"}

The example shown here creates two traces in the same chart: one is a perfect sine trace,
and the other is the same sine trace, except that the *y* values of its data points are
displaced randomly in a range that we define (in *error_ranges*).

Here is the code that implements that:
```python
# Number of samples
max_x = 20
# x values: [0..max_x-1]
x = range(0, max_x)
# Generate random sampling error margins
error_ranges = [random.uniform(0, 5) for _ in x]
# Compute a perfect sine wave
perfect_y = [10*math.sin(4*math.pi*i/max_x) for i in x]
# Compute a sine wave impacted by the sampling error
# The error is between ±error_ranges[x]/2
y = [perfect_y[i]+random.uniform(-error_ranges[i]/2, error_ranges[i]/2) for i in x]

# The chart data is made of the three series
data = {
    "x": x,
    "y1": y,
    "y2": perfect_y,
}

options = {
    # Create the error bar information:
    "error_y": {
        "type": "data",
        "array": error_ranges
    }
}
```

The chart control definition sets *y[1]* and *y[2]* to represent the two series (respectively
*y* and *perfect_y*):
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|x=x|y[1]=y1|y[2]=y2|options[1]={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart x="x" y[1]="y1" y[2]="y2" options[1]="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", x="x", y[1]="y1", y[2]="y2", options[1]="{options}")
        ```

Note how the *options* dictionary is set for the first trace only: we do not want error bars
to appear on our *perfect sine* graph.

Here is the result:
<figure>
    <img src="../error-bars-simple-d.png" class="visible-dark"  />
    <img src="../error-bars-simple-l.png" class="visible-light" />
    <figcaption>Simple error bars</figcaption>
</figure>

### Asymmetric error bars {data-source="gui:doc/examples/charts/error-bars-asymmetric.py"}

The previous example uses an error range applied to every data point. The error
bar of each data point would represent the whole error range as a segment centered on
the data point itself.<br/>
There are situations where the values of the measurement error on both sides of the data points
are not equal. We call these *asymmetric errors*, and the error bars can reflect that: they will
be longer on the side of the data points where the error value is more significant compared to
the error value on the other side.

Here is an example that demonstrates how to implement this. This example uses a
[bar chart](bar.md) that is displayed horizontally. Obviously the error bar has to be horizontal
as well.

The code is the following:
```python
# Number of samples
n_samples = 10
# y values: [0..n_samples-1]
y = range(0, n_samples)

data = {
    # The x series is made of random numbers between 1 and 10
    "x": [random.uniform(1, 10) for i in y],
    "y": y
}

options = {
    "error_x": {
        "type": "data",
        # Allows for a 'plus' and a 'minus' error data
        "symmetric": False,
        # The 'plus' error data is a series of random numbers
        "array": [random.uniform(0, 5) for i in y],
        # The 'minus' error data is a series of random numbers
        "arrayminus": [random.uniform(0, 2) for i in y],
        # Color of the error bar
        "color": "red"
    }
}
```

Note how the *options* dictionary is a bit lengthier compared to the one in the previous example:

- The setting of the *symmetric* property to True allows for the use of both the *array* series
  and *arrayminus* (that will be displayed with an error bar drawn under or to the left of the
  data point);
- The *color* property indicates the color used to draw the error bars.

Here is the chart control definition that is used:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|x=x|y=y|orientation=h|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" x="x" y="y" orientation="h" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", x="x", y="y", orientation="h", options="{options}")
        ```

The *orientation* property is set to "h" so the bar chart is displayed horizontally.

The resulting image looks like this:
<figure>
    <img src="../error-bars-asymmetric-d.png" class="visible-dark" />
    <img src="../error-bars-asymmetric-l.png" class="visible-light"/>
    <figcaption>Asymmetric error bars</figcaption>
</figure>
