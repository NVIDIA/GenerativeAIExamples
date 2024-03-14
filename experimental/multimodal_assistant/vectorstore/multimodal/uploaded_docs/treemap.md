---
hide:
  - navigation
---

# Treemaps

Treemaps charts display data as rectangles whose surface is proportional to the value to be
represented.<br/>
Data can be organized hierarchically, where branches of the tree are represented by rectangles
containing smaller nested rectangles representing sub-branches.

The property [*type*](../chart.md#p-type) of the chart control must be set to "treemap"
if you need a Treemap chart.

## Key properties

| Name            | Value            | Notes   |
| --------------- | -------------------------- | ---------------------- |
| [*type*](../chart.md#p-type)       | `treemap`                        |  |
| [*labels*](../chart.md#p-labels)   | Labels of the rectangles.        | This is mandatory. |
| [*values*](../chart.md#p-values)   | Values to represent.             | See below. |
| [*parents*](../chart.md#p-parents) | Identifiers of each data parent. | See below. |

<!--
TODO| [*options*](../chart.md#p-options)  | dictionary  | `colorscale` can be used to set a color scale.<br/>`showscale` can be set to False to hide the color scale.  |
TODO| [*layout*](../chart.md#p-layout)    | dictionary  | `annotations` can be used to add specific text information to a cell.  |
-->

Important notes:

- the [*labels*](../chart.md#p-labels) property must be an array of unique values.<br/>
- The [*parents*](../chart.md#p-parents) property can be set to a series of strings that can be whether
  an empty string or a value in the [*labels*](../chart.md#p-labels) property.<br/>
  An empty string indicates that the corresponding (at the same index) item in the *labels* array
  will be located at the root of the treemap.<br/>
  A non-empty value will create a rectangle for the corresponding item (at the same index) as a child
  of the rectangle created for this label.<br/>
  If [*parents*](../chart.md#p-parents) is not set, all data points are considered at the root
  level.
- You must set at least [*values*](../chart.md#p-values) or [*parents*](../chart.md#p-parents) in
  order to display something relevant.

## Examples

### Simple treemap {data-source="gui:doc/examples/charts/treemap-simple.py"}

A common use of treemap charts is to display a dataset as a set of rectangles, each with a
size that is proportional to a value from the dataset.

Here is an example where we create a treemap where rectangles reflect the few first Fibonacci
numbers:
```python
# Data set: the first 10 elements of the Fibonacci sequence
n_numbers = 10
fibonacci = [0, 1]
for i in range(2, n_numbers):
    fibonacci.append(fibonacci[i-1]+fibonacci[i-2])

data = {
    "index": [i for i in range(1, n_numbers+1)],
    "fibonacci": fibonacci
```

Here is how the chart control is declared:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=treemap|labels=index|values=fibonacci|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="treemap" labels="index" values="fibonacci">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="treemap", labels="index", values="fibonacci")
        ```

And this is what the resulting chart looks like:
<figure>
    <img src="../treemap-simple-d.png" class="visible-dark"  width="80%"/>
    <img src="../treemap-simple-l.png" class="visible-light" width="80%"/>
    <figcaption>Fibonacci numbers</figcaption>
</figure>

### Hierarchical data {data-source="gui:doc/examples/charts/heatmap-hierarchical.py"}

A very common use of treemap charts is to represent hierarchical structure: each child element is
represented as a rectangle within its parent's rectangle.<br/>
In this situation, you need to provide the [*labels*](../chart.md#p-labels) and
[*parents*](../chart.md#p-parents) properties of the chart control, and these arrays need to be the
same size. Each element of the *parents* array indicates the name of the parent rectangle for the
corresponding element in *labels*.<br/>
Setting the *parents* value to an empty string indicates that the element should be at the
root level.

Here is a short example demonstrating this use case:
```python
# Partial family tree of the British House of Windsor
# Source: https://en.wikipedia.org/wiki/Family_tree_of_the_British_royal_family
tree = {
    "name": ["Queen Victoria",
             "Princess Victoria", "Edward VII", "Alice", "Alfred",
             ...
             "Charles III", "Anne", "Andrew",
            ],
    "parent": ["",
               "Queen Victoria", "Queen Victoria", "Queen Victoria", "Queen Victoria",
               ...
               "Elizabeth II", "Elizabeth II", "Elizabeth II"
            ]

}
```

In this dataset, the first element of the *name* array, labeled "Queen Victoria", is stored at the
root level since the first element of the *parent* array is set to an empty string.

Here is the chart control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{tree}|chart|type=treemap|labels=name|parents=parent|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="treemap" labels="name" parents="parent">{tree}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{tree}", type="treemap", labels="name", parents="parent")
        ```

The *tree.name* and *tree.parent* arrays are used respectively in the
[*labels*](../chart.md#p-labels) and [*parents*](../chart.md#p-parents) properties.

Here is the resulting chart:
<figure>
    <img src="../treemap-hierarchical-d.png" class="visible-dark" />
    <img src="../treemap-hierarchical-l.png" class="visible-light" />
    <figcaption>Partial family tree of British monarchs</figcaption>
</figure>

Note that clicking in a given rectangle gets the chart to drill into that specific data point.
The chart then represents the path to the selected area as a breadcrumbs bar at the top so
the user can return to any level.
<figure>
    <img src="../treemap-hierarchical2-d.png" class="visible-dark" />
    <img src="../treemap-hierarchical2-l.png" class="visible-light" />
    <figcaption>Drilling down</figcaption>
</figure>

### Hierarchical values {data-source="gui:doc/examples/charts/treemap-hierarchical-values.py"}

Treemap charts can be used to represent data with rectangles that have a size proportional to
values and are organized hierarchically.<br/>
This feature makes it easy to spot data points with higher values in the hierarchical tree since
they appear as a bigger rectangle in the given category rectangle.

Here is a short example demonstrating this use case: we want to represent the largest countries
of all continents, where the rectangle used for each country would be nested within the rectangle
that represents a continent and where the size of the country's rectangle is proportional to
the surface of the country.

Here is the initial data set we will be working with, stored as a dictionary:
```python
# Major countries and their surface (in km2), for every continent
# Source: https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_area
continents = {
    "Africa": [
        { "name": "Algeria", "surface": 2381741},
        { "name": "Dem. Rep. Congo", "surface": 2344858},
        { "name": "Sudan", "surface": 1886068},
        { "name": "Libya", "surface": 1759540},
        { "name": "Chad", "surface": 1284000}
    ],
    ...
    "Antarctica": [
        { "name": "Whole", "surface": 14200000}
    ]
}
```

We need to convert that dictionary to a format that is applicable for the chart control: a set of
arrays where each array stores the relevant information in a flat manner.

Here is the code that transforms the *continents* into precisely that:
```python
name=[]
surface=[]
continent=[]

for continent_name, countries in continents.items():
  # Create continent in root rectangle
  name.append(continent_name)
  surface.append(0)
  continent.append("")
  # Create countries in that continent rectangle
  for country in countries:
    name.append(country["name"])
    surface.append(country["surface"])
    continent.append(continent_name)

data = {
  "names": name,
  "surfaces": surface,
  "continent": continent
}
```

We iterate over the dictionary and store the data that the treemap chart will represent for each
continent and each country for that continent.<br/>
Finally, we create the *data* variable that holds all the information in the proper format.

The chart control definition uses this dataset:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=treemap|labels=names|values=surfaces|parents=continent|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="treemap" labels="names" values="surfaces" parents="continent">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="treemap", labels="names", values="surfaces", parents="continent")
        ```

Here is what the chart looks like on the page:
<figure>
    <img src="../treemap-hierarchical-values-d.png" class="visible-dark" />
    <img src="../treemap-hierarchical-values-l.png" class="visible-light" />
    <figcaption>Hierarchically organized values</figcaption>
</figure>

With this sort of treemaps, we can spot immediately the element that holds the greater value in
a given category (each continent, in our situation).
