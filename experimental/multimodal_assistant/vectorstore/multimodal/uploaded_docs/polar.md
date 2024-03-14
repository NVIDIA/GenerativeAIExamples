---
hide:
  - navigation
---

# Polar charts

Polar charts are a common variation of circular graphs. They are used when relationships between
data points can be better visualized in terms of radiuses and angles.

In a polar chart, a series is represented by a trace connecting points in the polar
coordinate system. Each data point is determined by the distance from the pole (the radial
coordinate) and the angle from the origin direction (the angular coordinate).

To create polar charts with Taipy, you must set the [*type*](../chart.md#p-type) property
of the chart control to "scatterpolar", and set the [*r*](../chart.md#p-r) and
[*theta*](../chart.md#p-theta) properties to the data you want to display.

## Key properties

| Name            | Value            | Notes   |
| --------------- | -------------------------- | ------------------ |
| [*type*](../chart.md#p-type)       | `scatterpolar`  |  |
| [*r*](../chart.md#p-r)             | radial values   |  |
| [*theta*](../chart.md#p-theta)     | angular values  |  |
| [*options*](../chart.md#p-options) | dictionary  | `subplot` is used to set the name of a trace so it can be used in the *layout* property.<br/>`fill` can be used to fill traces.  |
| [*layout*](../chart.md#p-layout)   | dictionary  | `showlegend` can be set to False to hide the legend.<br/>`polar*` properties can specify specific layout parameters for a specific trace (see *options*.*subplot*).  |

## Examples

### Simple polar chart {data-source="gui:doc/examples/charts/polar-simple.py"}

A typical use case for polar charts is when you have a parametric
equation to represent, based on an angular value.

Here is an example of such a chart. We are creating a parametric curve that will
result in a nice-looking polar chart:
```python
# One data point for each degree
theta = range(0, 360)

# Parametric equation that draws a shape (source Wolfram Mathworld)
def draw_heart(angle):
    a = math.radians(angle)
    sa = math.sin(a)
    return 2-2*sa+sa*(math.sqrt(math.fabs(math.cos(a)))/(sa+1.4))

data = {
    # Create the heart shape
    "r": [draw_heart(angle) for angle in theta],
    "theta": theta
}
```

The *data* object is built with a linear range of values for *theta* and
a computed series of *r* values.

We can use this object in the definition of the chart we want to display:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|mode=lines|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" mode="lines">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", mode="lines")
        ```

We don't need to explicitly set the [*r*](../chart.md#p-r) and [*theta*](../chart.md#p-theta)
properties because *data* has two data sets, with the respective names.

Note that we set [*mode*](../chart.md#p-mode) to "lines" to keep only the
lines of the trace and no markers on every data point.

Here is the result:
<figure>
    <img src="../polar-simple-d.png" class="visible-dark" />
    <img src="../polar-simple-l.png" class="visible-light"/>
    <figcaption>Simple polar chart</figcaption>
</figure>

### Areas {data-source="gui:doc/examples/charts/polar-area.py"}

Filling an area in a polar chart is only a matter of setting the *fill* property of
the value assigned to the [*options*](../chart.md#p-options) property of the chart control.

Here is an example that uses the same data set (in *data*) as in the previous example:
```python
options = {
    "fill": "toself"
}

layout = {
    # Hide the legend
    "showlegend": False,
    "polar": {
        # Hide the angular axis
        "angularaxis": {
            "visible": False
        },
        # Hide the radial axis
        "radialaxis": {
            "visible": False
        }
    }
}
```

The *options* object forces the trace to be filled.<br/>
*layout* is configured to remove all axis information as well as the legend.

The chart control definition is:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|mode=none|layout={layout}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" mode="none" layout="{layout}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", mode="none", layout="{layout}", options="{options}")
        ```

Here is the resulting rendering:
<figure>
    <img src="../polar-area-d.png" class="visible-dark" />
    <img src="../polar-area-l.png" class="visible-light"/>
    <figcaption>Area in a polar chart</figcaption>
</figure>

### Multiple traces {data-source="gui:doc/examples/charts/polar-multiple.py"}

Several traces can be displayed in the same polar chart. The [*r*](../chart.md#p-r)
indexed property can refer to different data.

Here is how to create several traces:
```python
# One data point for each degree
theta = range(0, 360)

# Create a rose-like shaped radius-array
def create_rose(n_petals):
    return [math.cos(math.radians(n_petals*angle)) for angle in theta]

data = {
    "theta": theta,
    "r1": create_rose(2),
    "r2": create_rose(3),
    "r3": create_rose(4)
}

# We want three traces in the same chart
r = ["r1", "r2", "r3"]

layout = {
    # Hide the legend
    "showlegend": False,
    "polar": {
        # Hide the angular axis
        "angularaxis": {
            "visible": False
        },
        # Hide the radial axis
        "radialaxis": {
            "visible": False
        }
    }
}
```

Three traces are used, stored in the array *r*.

The *layout* object ensures that only the traces will be rendered.

Here is the chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|mode=lines|r={r}|theta=theta|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" mode="lines" r="{r}" theta="theta" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", mode="lines", r="{r}", theta="theta", layout="{layout}")
        ```

Here is what the chart looks like:
<figure>
    <img src="../polar-multiple-d.png" class="visible-dark" />
    <img src="../polar-multiple-l.png" class="visible-light"/>
    <figcaption>Multiple traces</figcaption>
</figure>

### Specifying the angular range {data-source="gui:doc/examples/charts/polar-sectors.py"}

It may be necessary not to display the entire 360° of the chart but instead select a
range of angles to represent: a *sector*.

Here is some code that does that:
```python
# Sample small plot definition
trace = {
    "r": [1, 2, 3, 4, 1],
    "theta": [0, 40, 80, 120, 160],
}

# The same data is used in both traces
data = [trace, trace]

# Naming the subplot is mandatory to get them both in
# the same chart
options = [
    {
        "subplot": "polar",
    },
    {
        "subplot": "polar2"
    }
]

layout = {
    # Hide the legend
    "showlegend": False,
    # Restrict the angular values for second trace
    "polar2": {
        "sector": [30, 130]
    },
}
```

We use two traces: the first uses the complete circle, the second uses only a sector, 
as defined in the *layout* object.<br/>
Note that for the layout to be correctly applied, you need to name the subplots
(as done in the *options* object) with names that start with "polar", then reference
these names in the *layout* object.

The chart control definition can now be written:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|layout={layout}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" layout="{layout}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", layout="{layout}", options="{options}")
        ```

Here are our two traces, gathered in the same chart:
<figure>
    <img src="../polar-sector-d.png" class="visible-dark" />
    <img src="../polar-sector-l.png" class="visible-light"/>
    <figcaption>Specifying a sector</figcaption>
</figure>

### Angular axis settings {data-source="gui:doc/examples/charts/polar-angular-axis.py"}

The angular axis can be tuned to set its origin wherever needed. It can
also be oriented, and the angular values can appear in different units.

Here is a demonstration of these capabilities:
```python
# Create a star shape
data = {
        "r": [3, 1] * 5 + [3],
        "theta": list(range(0, 360, 36)) + [0]
    }

options=[
    # First plot is filled with a yellow-ish color
    {
        "subplot": "polar",
        "fill": "toself",
        "fillcolor": "#E4FF87"
    },
    # Second plot is filled with a blue-ish color
    {
        "subplot": "polar2",
        "fill": "toself",
        "fillcolor": "#709BFF"
    }
]

layout = {
    "polar": {
        # This actually is the default value
        "angularaxis": {
            "direction": "counterclockwise",
        },
    },
    "polar2": {
        "angularaxis": {
            # Rotate the axis 180° (0 is on the left)
            "rotation": 180,
            # Orient the axis clockwise
            "direction": "clockwise",
            # Show the angles as radians
            "thetaunit": "radians"
        },
    },
    # Hide the legend
    "showlegend": False,
}
```

The two traces have very different settings for their angular axis.

The chart control definition is straightforward:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|layout={layout}|options={options}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" layout="{layout}" options="{options}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", layout="{layout}", options="{options}")
        ```

The two traces appear in the chart, mirroring one another:
<figure>
    <img src="../polar-angular-axis-d.png" class="visible-dark" />
    <img src="../polar-angular-axis-l.png" class="visible-light"/>
    <figcaption>Customizing the angular axis</figcaption>
</figure>

### Setting tick texts {data-source="gui:doc/examples/charts/polar-tick-texts.py"}

You can also customize what the tick texts are: what text is at what location on the axis.

Here is an example that uses a chart control to show the current time in a way that looks like
a wall clock:
```python
def generate_hand_shapes():
    # Retrieve and store the current, local time
    time_now = datetime.now()
    hours = time_now.hour
    minutes = time_now.minute
    seconds = time_now.second

    # Compute the angle that represents the hours
    hours_angle = 360 * ((hours % 12) / 12 + (minutes % 60) / 60 / 60 + (seconds % 60) / 60 / 60 / 60)
    # Short and thick hand for the hours
    hours_hand = {
        "r": [0, 4, 5, 4, 0],
        "a": [0, hours_angle-7, hours_angle, hours_angle+7, 0]
    }

    # Compute the angle that represents the minutes
    minutes_angle = 360 * ((minutes % 60) / 60 + (seconds % 60) / 60 / 60)
    # Longer and slighly thinner hand for the minutes
    minutes_hand = {
        "r": [0, 6, 8, 6, 0],
        "a": [0, minutes_angle-4, minutes_angle, minutes_angle+4, 0]
    }

    # Compute the angle that represents the seconds
    seconds_angle = 360 * (seconds % 60) / 60
    # Even longer and thinner hand for the seconds
    seconds_hand = {
        "r": [0, 8, 10, 8, 0],
        "a": [0, seconds_angle-2, seconds_angle, seconds_angle+2, 0]
    }
    # Build and return the whole data set
    return [
        hours_hand,
        minutes_hand,
        seconds_hand
    ]

# Initialize the data set with the current time
data = generate_hand_shapes()

layout = {
    "polar": {
        "angularaxis": {
            "rotation": 90,
            "direction": "clockwise",
            # One tick every 30 degrees
            "tickvals": list(numpy.arange(0., 360., 30)),
            # Text value for every tick
            "ticktext": [
                "XII", "I", "II", "III", "IV", "V",
                "VI", "VII", "VIII", "IX", "X", "XI"
            ]
        },
        "radialaxis": {
            "angle": 90,
            "visible": False,
            "range": [0, 12]
        }
    },
    "showlegend": False
}

# Options to be used for all three traces
base_opts = {"fill": "toself"}
# Specific for hours
hours_opts = dict(base_opts)
hours_opts["fillcolor"] = "#FF0000"
# Specific for minutes
minutes_opts = dict(base_opts)
minutes_opts["fillcolor"] = "#00FF00"
# Specific for seconds
seconds_opts = dict(base_opts)
seconds_opts["fillcolor"] = "#0000FF"

# Store all the chart control properties in a single object
properties = {
    # Don't show data point markers
    "mode": "lines",
    # Data for the hours
    "theta[1]": "0/a",
    "r[1]": "0/r",
    # Data for the minutes
    "theta[2]": "1/a",
    "r[2]": "1/r",
    # Data for the seconds
    "theta[3]": "2/a",
    "r[3]": "2/r",
    # Options for the three traces
    "options[1]": hours_opts,
    "options[2]": minutes_opts,
    "options[3]": seconds_opts,
    "line": {"color": "black"},
    "layout": layout
}

# Update time on every refresh
def on_navigate(state, page):
    state.data = generate_hand_shapes()
    return page
```

All the properties for the chart control are stored in the *properties* dictionary, so
the chart control definition can be concise.

Note how we use the [*on_navigate()*](../../callbacks.md#navigation-callback) callback function
to refresh the data so that every refresh of the display will compute and display the current
time.

Here is the very simple chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scatterpolar|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scatterpolar" properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scatterpolar", properties="{properties}")
        ```

The chart control will display the current local time on every refresh:
<figure>
    <img src="../polar-tick-texts-d.png" class="visible-dark" />
    <img src="../polar-tick-texts-l.png" class="visible-light"/>
    <figcaption>Custom tick texts</figcaption>
</figure>
