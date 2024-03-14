---
hide:
  - navigation
---

# Map plots

Taipy leverages Plotly's capabilities of plotting data on top of maps.

The data points to plot must then be stored in the [*lat*](../chart.md#p-lat) and
[*lon*](../chart.md#p-lon) properties of the chart control, whose type must be
set to *scattergeo*.<br/>
You can find the full description of *scattergeo* plots on the Plotly reference
manual for [*scattergeo* traces](https://plotly.com/javascript/reference/scattergeo/).

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `scattergeo`          |  |
| [*lat*](../chart.md#p-lat)        | Latitude values           | In degrees North.  |
| [*lon*](../chart.md#p-lon)        | Longitude values           | In degrees East.  |
| [*layout*](../chart.md#p-layout)  | dictionary  | *geo* can be used for specific settings for *scattergeo* plots. See [*geo* property of *layout*](https://plotly.com/javascript/reference/layout/geo/#layout-geo) for details.  |

## Examples

### Simple map {data-source="gui:doc/examples/charts/map-simple.py"}

Here is a simple example demonstrating how to plot a line between two
georeferenced locations.

The code that defines all necessary data structures looks like this:
```python
# Flight start and end locations
data = {
    # Hartsfield-Jackson Atlanta International Airport 
    # to
    # Aéroport de Paris-Charles de Gaulle
    "lat": [33.64, 49.01],
    "lon": [-84.44, 2.55],
}

layout = {
    # Chart title
    "title": "ATL to CDG",
    # Hide legend
    "showlegend": False,
    # Focus on relevant area
    "geo": {
        "resolution": 50,
        "showland": True,
        "showocean": True,
        "landcolor": "4a4",
        "oceancolor": "77d",
        "lataxis": {
            "range": [20, 60]
        },
        "lonaxis": {
            "range": [-100, 20]
        }
    }
}

# Flight displayed as a thick, red plot
line = {
    "width": 5,
    "color": "red"
}
```

In the dictionary stored in *layout["geo"]*, you can spot a handful of settings
tuning how the map is rendered under the line.

The chart definition uses all those objects to create the control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scattergeo|mode=lines|lat=lat|lon=lon|line={line}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scattergeo" mode="lines" lat="lat" lon="lon" line="{line}" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scattergeo", mode="lines", lat="lat", lon="lon", line="{line}", layout="{layout}")
        ```

The control renders as shown here:
<figure>
    <img src="../map-simple-d.png" class="visible-dark" />
    <img src="../map-simple-l.png" class="visible-light"/>
    <figcaption>Flight path</figcaption>
</figure>

### Multiple paths {data-source="gui:doc/examples/charts/map-lines.py"}

If you need to display several distinct paths on top of a map, you must create a trace
for each.

In this example, we have a series of flight descriptions in the *flights* array.
Each flight is described with its origin and destination airports (using their
IATA - International Air Transport Association - codes) and how many of these flights
are available on a given period (in the *traffic* property).

We can locate every airport using the *airports* dictionary that associates the
IATA code of an airport with its latitude and longitude.

For every defined flight, we create a new element in the array *data* used as
the data source for the chart control. Each of these elements contains the origin
and destination location of every route.<br/>
Each of these elements is handled by the chart control as a specific trace: *data[0]*
defines the path for trace 1, *data[1]* defines the path for trace 2, and so on.

The dictionary *properties* holds all the information that the chart control uses (including
its type). The association of the trace data to the element index in *data* is
done by adding the *lat[n]* and *lon[n]* keys to the dictionary.

Here is the complete code:
```python
airports = {
    "AMS": {"lat": 52.31047296675518, "lon": 4.76819929439927},
    "ATL": {"lat": 33.64086185344307, "lon": -84.43600501711686},
    ...
    "XIY": {"lat": 34.437119809208546, "lon": 108.7573508575816}
}

flights = [
    {"from": "ATL", "to": "DFW", "traffic": 580},
    {"from": "ATL", "to": "MIA", "traffic": 224},
    ...
    {"from": "SLC", "to": "DFW", "traffic": 280}
]

data = []
max_traffic = 0
for flight in flights:
    airport_from = airports[flight["from"]]
    airport_to = airports[flight["to"]]
    # Define data source to plot this flight
    data.append({
        "lat": [airport_from["lat"], airport_to["lat"]],
        "lon": [airport_from["lon"], airport_to["lon"]]
    })
    # Store the maximum traffic
    if flight["traffic"] > max_traffic:
        max_traffic = flight["traffic"]

properties = {
    # Chart data
    "data": data,
    # Chart type
    "type": "scattergeo",
    # Keep lines only
    "mode": "lines",
    # Flights display as redish lines
    "line": {
        "width": 2,
        "color": "E22"
    },
    "layout": {
        # Focus on the USA region
        "geo": {
            "scope": "usa"
        }
    }
}

# Set the proper data source and opacity for each trace
for i, flight in enumerate(flights):
    # lat[trace_index] = "[index_in_data]/lat"
    properties[f"lat[{i+1}]"] = f"{i}/lat"
    # lon[trace_index] = "[index_in_data]/lon"
    properties[f"lon[{i+1}]"] = f"{i}/lon"
    # Set flight opacity (max traffic -> max opacity)
    # Hide legend for all flights
    properties[f"options[{i+1}]"] = {
        "opacity": flight["traffic"]/max_traffic,
        "showlegend": False
    }
```

Because the *properties* holds everything that the chart control needs, the
control definition is really short:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|properties={properties}|>
        ```

    === "HTML"

        ```html
        <taipy:chart properties="{properties}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", properties="{properties}")
        ```

Here is how the chart control is displayed:
<figure>
    <img src="../map-lines-d.png" class="visible-dark" />
    <img src="../map-lines-l.png" class="visible-light"/>
    <figcaption>US flights</figcaption>
</figure>

### Bubbles on map {data-source="gui:doc/examples/charts/map-bubbles.py"}

You may need to represent some value at their appropriate location.

In the following code, the array *cities* holds a series of cities with their location
and human population.<br/>
We create a Pandas DataFrame that holds the full information, where we add two
columns that the chart control can use to build the bubbles themselves:
```python
cities = [
    {"name": "Tokyo", "lat": 35.6839, "lon": 139.7744, "population": 39105000},
    {"name": "Jakarta", "lat": -6.2146, "lon": 106.8451, "population": 35362000},
    ...
    {"name": "Xinyang", "lat": 32.1264, "lon": 114.0672, "population": 6109106},
]

# Convert to Pandas DataFrame
data = pandas.DataFrame(cities)

# Add a column holding the bubble size:
#   Min(population) -> size =  5
#   Max(population) -> size = 60
solve = numpy.linalg.solve([[data["population"].min(), 1], [data["population"].max(), 1]],
                           [5, 60])
data["size"] = data["population"].apply(lambda p: p*solve[0]+solve[1])

# Add a column holding the bubble hover texts
# Format is "<city name> [<population>]"
data["text"] = data.apply(lambda row: f"{row['name']} [{row['population']}]", axis=1)

marker = {
    # Use the "size" column to set the bubble size
    "size": "size"
}

layout = {
    "geo": {
        "showland": True,
        "landcolor": "4A4"
    }
}
```

See how the new columns named "size" and "text" are computed from the whole DataFrame,
holding generated data that the chart control can automatically convert to visual
information.

Here is how the chart control is defined:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=scattergeo|mode=markers|lat=lat|lon=lon|marker={marker}|text=text|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="scattergeo" mode="markers" lat="lat" lon="lon" marker="{marker}" text="text" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="scattergeo", mode="markers", lat="lat", lon="lon", marker="{marker}", text="text", layout="{layout}")
        ```

Here is the resulting chart display:
<figure>
    <img src="../map-bubbles-d.png" class="visible-dark" />
    <img src="../map-bubbles-l.png" class="visible-light"/>
    <figcaption>Populated cities</figcaption>
</figure>
