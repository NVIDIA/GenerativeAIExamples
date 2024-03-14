---
title: <tt>table</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Displays a data set as tabular data.

# Properties


<table>
<thead>
    <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Default</th>
    <th>Description</th>
    </tr>
</thead>
<tbody>
<tr>
<td nowrap><code id="p-data"><u><bold>data</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>any</code><br/><i>dynamic</i></td>
<td nowrap><i>Required</i></td>
<td><p>The data to be represented in this table.</p></td>
</tr>
<tr>
<td nowrap><code id="p-page_size">page_size</code></td>
<td><code>int</code></td>
<td nowrap>100</td>
<td><p>For a paginated table, the number of visible rows.</p></td>
</tr>
<tr>
<td nowrap><code id="p-allow_all_rows">allow_all_rows</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>For a paginated table, adds an option to show all the rows.</p></td>
</tr>
<tr>
<td nowrap><code id="p-show_all">show_all</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>For a paginated table, show all the rows.</p></td>
</tr>
<tr>
<td nowrap><code id="p-auto_loading">auto_loading</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, the data will be loaded on demand.</p></td>
</tr>
<tr>
<td nowrap><code id="p-width[column_name]">width[<i>column_name</i>]</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The width, in CSS units, of the indicated column.</p></td>
</tr>
<tr>
<td nowrap><code id="p-selected">selected</code></td>
<td><code>list[int]|str</code></td>
<td nowrap></td>
<td><p>The list of the indices of the rows to be displayed as selected.</p></td>
</tr>
<tr>
<td nowrap><code id="p-page_size_options">page_size_options</code></td>
<td><code>list[int]|str</code></td>
<td nowrap>[50, 100, 500]</td>
<td><p>The list of available page sizes that users can choose from.</p></td>
</tr>
<tr>
<td nowrap><code id="p-columns">columns</code></td>
<td><code>str|list[str]|dict[str, dict[str, str|int]]</code></td>
<td nowrap><i>shows all columns when empty</i></td>
<td><p>The list of the column names to display.
<ul>
<li>str: Semicolon (';')-separated list of column names.</li>
<li>list[str]: The list of column names.</li>
<li>dict: A dictionary with entries matching: {"col name": {format: "format", index: 1}}.<br/>
if <i>index</i> is specified, it represents the display order of the columns.
If <i>index</i> is not specified, the list order defines the index.<br/>
If <i>format</i> is specified, it is used for numbers or dates.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-date_format">date_format</code></td>
<td><code>str</code></td>
<td nowrap>"MM/dd/yyyy"</td>
<td><p>The date format used for all date columns when the format is not specifically defined.</p></td>
</tr>
<tr>
<td nowrap><code id="p-number_format">number_format</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The number format used for all number columns when the format is not specifically defined.</p></td>
</tr>
<tr>
<td nowrap><code id="p-group_by[column_name]">group_by[<i>column_name</i>]</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>Indicates, if True, that the given column can be aggregated.<br/>See <a href="#aggregation">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-apply[column_name]">apply[<i>column_name</i>]</code></td>
<td><code>str</code></td>
<td nowrap>"first"</td>
<td><p>The name of the aggregation function to use.<br/>This is used only if <i>group_by[column_name]</i> is set to True.<br/>See <a href="#aggregation">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-style">style</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>Allows the styling of table lines.<br/>See <a href="#dynamic-styling">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-style[column_name]">style[<i>column_name</i>]</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>Allows the styling of table cells.<br/>See <a href="#dynamic-styling">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-tooltip">tooltip</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of the function that must return a tooltip text for a cell.<br/>See <a href="#cell-tooltips">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-tooltip[column_name]">tooltip[<i>column_name</i>]</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of the function that must return a tooltip text for a cell.<br/>See <a href="#cell-tooltips">below</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-width">width</code></td>
<td><code>str</code></td>
<td nowrap>"100%"</td>
<td><p>The width, in CSS units, of this table control.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str</code></td>
<td nowrap>"80vh"</td>
<td><p>The height, in CSS units, of this table control.</p></td>
</tr>
<tr>
<td nowrap><code id="p-filter">filter</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>Indicates, if True, that all columns can be filtered.</p></td>
</tr>
<tr>
<td nowrap><code id="p-filter[column_name]">filter[<i>column_name</i>]</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>Indicates, if True, that the indicated column can be filtered.</p></td>
</tr>
<tr>
<td nowrap><code id="p-nan_value">nan_value</code></td>
<td><code>str</code></td>
<td nowrap>""</td>
<td><p>The replacement text for NaN (not-a-number) values.</p></td>
</tr>
<tr>
<td nowrap><code id="p-nan_value[column_name]">nan_value[<i>column_name</i>]</code></td>
<td><code>str</code></td>
<td nowrap>""</td>
<td><p>The replacement text for NaN (not-a-number) values for the indicated column.</p></td>
</tr>
<tr>
<td nowrap><code id="p-editable">editable</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>Indicates, if True, that all columns can be edited.</p></td>
</tr>
<tr>
<td nowrap><code id="p-editable[column_name]">editable[<i>column_name</i>]</code></td>
<td><code>bool</code></td>
<td nowrap>editable</td>
<td><p>Indicates, if False, that the indicated column cannot be edited when editable is True.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_edit">on_edit</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when a cell edition is validated.<br/>All parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the name of the tabular data variable.</li>
<li>payload (dict): the details on this callback's invocation.<br/>
This dictionary has the following keys:
<ul>
<li>index (int): the row index.</li>
<li>col (str): the column name.</li>
<li>value (any): the new cell value cast to the type of the column.</li>
<li>user_value (str): the new cell value, as it was provided by the user.</li>
<li>tz (str): the timezone if the column type is date.</li>
</ul>
</li>
</ul><br/>If this property is not set, the user cannot edit cells.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_delete">on_delete</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when a row is deleted.<br/>All parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the name of the tabular data variable.</li>
<li>payload (dict): the details on this callback's invocation.<br/>
This dictionary has the following keys:
<ul>
<li>index (int): the row index.</li>
</ul>
</li>
</ul><br/>If this property is not set, the user cannot delete rows.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_add">on_add</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the user requests a row to be added.<br/>All parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the name of the tabular data variable.</li>
<li>payload (dict): the details on this callback's invocation.<br/>This dictionary has the following keys:
<ul>
<li>index (int): the row index.</li>
</ul>
</li>
</ul><br/>If this property is not set, the user cannot add rows.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the user selects a row.<br/>All parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the name of the tabular data variable.</li>
<li>payload (dict): the details on this callback's invocation.<br/>This dictionary has the following keys:
<ul>
<li>action: the name of the action that triggered this callback.</li>
<li>index (int): the row index.</li>
<li>col (str): the column name.</li></ul></li></ul>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-size">size</code></td>
<td><code>str</code></td>
<td nowrap>"small"</td>
<td><p>The size of the rows.<br/>Valid values are "small" and "medium".</p></td>
</tr>
<tr>
<td nowrap><code id="p-rebuild">rebuild</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>False</td>
<td><p>If set to True, this allows to dynamically refresh the  columns.</p></td>
</tr>
<tr>
<td nowrap><code id="p-lov[column_name]">lov[<i>column_name</i>]</code></td>
<td><code>list[str]|str</code></td>
<td nowrap></td>
<td><p>The list of values of the indicated column.</p></td>
</tr>
<tr>
<td nowrap><code id="p-active">active</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>Indicates if this component is active.<br/>An inactive component allows no user interaction.</p></td>
</tr>
<tr>
<td nowrap><code id="p-id">id</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The identifier that will be assigned to the rendered HTML component.</p></td>
</tr>
<tr>
<td nowrap><code id="p-properties">properties</code></td>
<td><code>dict[str, any]</code></td>
<td nowrap></td>
<td><p>Bound to a dictionary that contains additional properties for this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-class_name">class_name</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The list of CSS class names that will be associated with the generated HTML Element.<br/>These class names will be added to the default <code>taipy-&lt;element_type&gt;</code>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-hover_text">hover_text</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The information that is displayed when the user hovers over this element.</p></td>
</tr>
  </tbody>
</table>

<p><sup id="dv">(&#9733;)</sup><a href="#p-data" title="Jump to the default property documentation."><code>data</code></a> is the default property for this visual element.</p>

# Details

## Data types

All the data sets represented in the table control must be assigned to
its [*data*](#p-data) property.

The supported types for the [*data*](#p-data) property are:

- A list of values:<br/>
    When receiving a *data* that is just a series of values, the table is made of a single column holding
    the values at the corresponding index. The column name is then "0".
- A [Pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):<br/>
    Taipy tables then use the same column names as the DataFrame's.
- A dictionary:<br/>
    The value is converted into a Pandas DataFrame where each key/value pair is converted
    to a column named *key* and the associated value. Note that this will work only when
    all the values of the dictionary keys are series that have the same length.
- A list of lists of values:<br/>
    All the lists must be the same length. The table control creates one row for each list in the
    collection.
- A Numpy series:<br/>
    Taipy internally builds a Pandas DataFrame with the provided *data*.
 
## Display modes

The table component supports three display modes:

- *paginated*: you can choose the page size and page size options. The [*allow_all_rows*](#p-allow_all_rows)
  property makes it possible to add an option to show a page with all rows.
- *unpaginated*: all rows and no page are shown. That is the setting when the [*show_all*](#p-show_all)
  property is set to True.
- *auto_loading*: the pages are loaded on demand depending on the visible area. That is the behavior when
  the [*auto_loading*](#p-auto_loading) property is set to True.

## The *rebuild* property

When the application modifies the value of a dynamic property, the impact of the change is
immediately reflected on the application page. However, changing the value of properties that are
*not* dynamic requires that the user refreshes the page manually (or that the application
explicitly calls `navigate()^` with the *force* parameter set to True). This is due to the fact
that the entire front-end component must be entirely re-generated to reflect its new settings
based on the property values.<br/>
The table control provides the [*rebuild*](#p-rebuild) property that, when set to True, triggers
the rebuilding of the table front-end component and refreshes the page.<br/>
Note that this mechanism may hurt the user experience because rebuilding the entire component can
be a somewhat complex operation.

Here is a situation where you may need to use [*rebuild*](#p-rebuild): your application displays
a table, and you want to provide a way to interactively change the order of its columns.<br/>
Here is what the application code would look like:
```python  title="table.py"
from taipy.gui import Gui

# x: [1..5]
x_range = range(1, 6)
data = {
    "X": x_range,
    "Y": [x*x for x in x_range]
}

column_orders = [("X;Y", "Squared"), ("Y;X", "Square root")]
columns = column_orders[0]

page = """
<|{data}|table|columns={columns[0]}|show_all|>

<|{columns}|toggle|lov={column_orders}|>
"""

Gui(page=page).run()
```

The table displays two columns of data, one column holding the square value of the other.
When you run this application, here is what the page looks like:
<figure class="tp-center">
    <img src="../table-rebuild-1-d.png" class="visible-dark"  width="60%"/>
    <img src="../table-rebuild-1-l.png" class="visible-light" width="60%"/>
    <figcaption>Initial display of the application</figcaption>
</figure>

A toggle button lets the user choose whether to represent, in the second column, the square of the
value in the first column or the other way around.<br/>
To implement this, the code is setting the value "X;Y" or "Y;X" to the property
[*columns*](#p-columns).<br/>
Here is what the application looks like just after the user has changed the
value of the toggle button:
<figure class="tp-center">
    <img src="../table-rebuild-2-d.png" class="visible-dark"  width="60%"/>
    <img src="../table-rebuild-2-l.png" class="visible-light" width="60%"/>
    <figcaption>After the columns should be reordered</figcaption>
</figure>

We can see that although the value for the toggle button was properly updated, the table has not
rearranged its columns. That is because the [*columns*](#p-columns) property is *not* dynamic.

Setting the [*rebuild*](#p-rebuild) property to True allows for updating the table on the fly:
let's change the table's Markdown definition to:
```
<|{data}|table|columns={columns[0]}|show_all|rebuild|>
```

If you run the application again, and select the alternative column order in the toggle button,
here is what the page looks like:
<figure class="tp-center">
    <img src="../table-rebuild-3-d.png" class="visible-dark"  width="60%"/>
    <img src="../table-rebuild-3-l.png" class="visible-light" width="60%"/>
    <figcaption>After the columns are reordered</figcaption>
</figure>

Now the table properly reflects the value of the [*columns*](#p-columns) property and no manual
refresh was needed.

Make sure, when you are using the [*rebuild*](#p-rebuild) property, that no performance impact is
so bad that it would ruin the user experience.

# Styling

All the table controls are generated with the "taipy-table" CSS class. You can use this class
name to select the tables on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides a CSS custom property:

- *--table-stripe-opacity*<br/>
  This property contains the opacity applied to odd lines of tables.<br/>
  The default value is 0.5.

The [Stylekit](../styling/stylekit.md) also provides specific CSS classes that you can use to style
tables:

- *header-plain*<br/>
  Adds a plain and contrasting background color to the table header.
- *rows-bordered*<br/>
  Adds a bottom border to each row.
- *rows-similar*<br/>
  Removes the even-odd striped background so all rows have the same background.

## Dynamic styling

You can modify the style of entire rows or specific table cells based on any criteria, including
the table data itself.

When Taipy creates the rows and the cells, it can add a specific CSS class to the generated elements.
This class name is the string returned by the function set to the [*style*](#p-style) property for entire rows,
or [*style[column_name]*](#p-style[column_name]) for specific cells.

The signature of this function depends on which *style* property you use:

   - [*style*](#p-style): this applies to entire rows.<br/>
     The given function expects three optional parameters:
     - *state*: the current state
     - *index*: the index of the row in this table
     - *row*: all the values for this row
   - [*style[column_name]*](#p-style[column_name]): this applies to a specific cell.<br/>
     The given function expects five optional parameters:
     - *state*: the current state
     - *value*: the value of the cell
     - *index*: the index of the row in this table
     - *row*: all the values for this row
     - *column_name*: the name of the column for this cell

Based on these parameters, the function must return a string that defines a CSS class name that will
be added to the CSS classes for this table row or this specific cell.<br/>
The [example](#styling-rows) below shows how this works.

# Usage

## Show tabular data

Suppose you want to display the data set defined as follows:

```python
# x_range = [-10, -6, -2, 2, 6, 10]
x_range = range(-10, 11, 4)

data = {
    "x": x_range,
    # y1 = x*x
    "y1": [x*x for x in x_range],
    # y2 = 100-x*x
    "y2": [100-x*x for x in x_range]
}
```

You can use the following control declaration to display all these numbers
in a table:

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|>
        ```

    === "HTML"

        ```html
        <taipy:table>{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}")
        ```

The resulting image looks like this:
<figure class="tp-center">
    <img src="../table-simple-d.png" class="visible-dark"  width="50%"/>
    <img src="../table-simple-l.png" class="visible-light" width="50%"/>
    <figcaption>A simple table</figcaption>
</figure>

### Large data

The example above had only six lines of data. If we change the *x_range* definition
to create far more data lines, we come up with a table with much more data to display:
```python
# x_range = [-10, -9.98, ..., 9.98, 10.0] - 1000 x values
x_range = [round(20*i/1000-10, 2) for i in range(0, 1001)]

data = {
    "x": large_x_range,
    # y1 = x*x
    "y1": [round(x*x, 5) for x in large_x_range],
    # y2 = 100-x*x
    "y2": [round(100-x*x, 5) for x in large_x_range]
}
```

We can use the same table control definition:

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|>
        ```

    === "HTML"

        ```html
        <taipy:table>{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}")
        ```

To get a rendering looking like this:
<figure class="tp-center">
    <img src="../table-page-d.png" class="visible-dark"  width="50%"/>
    <img src="../table-page-l.png" class="visible-light" width="50%"/>
    <figcaption>Paginated table (partial)</figcaption>
</figure>

Only the first 100 rows (as indicated in the 'Rows per page' selector) are visible.<br/>
The table scroll bar lets you navigate across the 100 first rows.<br/>
You can change how many rows are displayed simultaneously using the
[*page_size*](#p-page_size) and [*page_size_options*](#p-page_size_options) properties.

If you want to display all the rows at the same time, you can change the control definition
to set the [*show_all*](#p-show_all) to True:

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|show_all|>
        ```

    === "HTML"

        ```html
        <taipy:table show_all>{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", show_all=True)
        ```

Now the table displays all the data rows, and the scrollbar lets you navigate among all of
them:
<figure class="tp-center">
    <img src="../table-show_all-d.png" class="visible-dark"  width="50%"/>
    <img src="../table-show_all-l.png" class="visible-light" width="50%"/>
    <figcaption>Showing all the rows (partial)</figcaption>
</figure>

Setting the [*allow_all_rows*](#p-allow_all_rows) property to True for a paginated table
adds the 'All' option to the page size options, so the user can switch from one mode to
the other.

## Show specific columns

If you want to display a specific set of columns, you can use the [*columns*](#p-columns)
property to indicate what columns should be displayed.

Here is how you would define the table control if you want to hide the column *y2*
from the examples above:

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|columns=x;y1|>
        ```

    === "HTML"

        ```html
        <taipy:table columns="x;y1">{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", columns="x;y1")
        ```

And the *y2* column is not displayed any longer:
<figure class="tp-center">
    <img src="../table-columns-d.png" class="visible-dark"  width="50%"/>
    <img src="../table-columns-l.png" class="visible-light" width="50%"/>
    <figcaption>Specifying the visible columns</figcaption>
</figure>

## Styling rows

To give a specific style to a table row, you will use the [*style*](#p-style) property.<br/>
This property holds a function that is invoked when each row is rendered, and it must return
the name of a style, defined in CSS.

Here is how a row styling function can be defined:

```python
def even_odd_style(_1, index, _2):
    if index % 2:
        return "blue-cell"
    else:
        return "red-cell"
```

We only use the second parameter since, in this straightforward case, we do not need the application
*state* (first parameter) or the values in the row (third parameter).<br/>
Based on the row index (received in *index*), this function returns the name of the style to apply
to the row: "blue-cell" if the index is odd, "red-cell" if it is even.

We need to define what these style names mean. This is done in a CSS stylesheet, where the following
CSS content would appear:

```css
.blue-cell>td {
    color: white;
    background-color: blue;
}
.red-cell>td {
    color: yellow;
    background-color: red;
}
```

Note that the style selectors use the CSS child combinator selector "&gt;" to target elements
that hold a `td` element (the cells themselves).

To use this style, we can adjust the control definition used above so it looks like this:

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|style=even_odd_style|>
        ```

    === "HTML"

        ```html
        <taipy:table style="even_odd_style">{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", style=even_odd_style)
        ```

The resulting display will be what we expected:
<figure class="tp-center">
    <img src="../table-rowstyle-d.png" class="visible-dark"  width="50%"/>
    <img src="../table-rowstyle-l.png" class="visible-light" width="50%"/>
    <figcaption>Styling the rows</figcaption>
</figure>

Note that the styling function is so simple that we could have made it a lambda, directly
in the control definition:

!!! example "Alternative definition"
    === "Markdown"
        ```
        <|{data}|table|style={lambda s, idx, r: "blue-cell" if idx % 2 == 0 else "red-cell"}|>
        ```

    === "HTML"
        ```html
        <taipy:table data="{data}" style="{lambda s, idx, r: 'blue-cell' if idx % 2 == 0 else 'red-cell'}" />
        ```

    === "Python"
        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", style="{lambda s, idx, r: 'blue-cell' if idx % 2 == 0 else 'red-cell'}" />
        ```

## Aggregation

To get the aggregation functionality in your table, you must indicate which columns can be aggregated
and how to perform the aggregation.

This is done using the indexed [*group_by*](#p-group_by[column_name]) and
[*apply*](#p-apply[column_name]) properties.

The [*group_by[column_name]*](#p-group_by[column_name]) property, when set to True indicates that the
column *column_name* can be aggregated.

The function provided in the [*apply[column_name]*](#p-apply[column_name]) property indicates how to
perform this aggregation. The value of this property, which is a string, can be:

- A built-in function. Available predefined functions are the following: `count`, `sum`, `mean`, `median`,
  `min`, `max`, `std`, `first` (the default value), and `last`.
- The name of a user-defined function or a lambda function.<br/>
  This function receives a single parameter which is the series to aggregate, and it must return a scalar
  value that would result from the aggregation.

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|group_by[Group column]|apply[Apply column]=count|>
        ```

    === "HTML"

        ```html
        <taipy:table group_by[Group column] apply[Apply column]="count">{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", group_by[Group column]=True, apply[Apply column]="count")
        ```

## Cell tooltips

You can specify a tooltip for specific table cells.

When Taipy creates the cells, it can add a specific tooltip that you would have set as the
return value of the function set to the [*tooltip*](#p-tooltip) or
[*tooltip[column_name]*](#p-tooltip[column_name]) properties.

The signature of this function expects five optional parameters:
- *state*: the current state.
- *value*: the value of the cell.
- *index*: the index of the row in this table.
- *row*: all the values for this row.
- *column_name*: the name of the column for this cell.

Based on these parameters, the function must return a string that defines a tooltip used as the
cell's tooltip text.

!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|table|tooltip={lambda state, val, idx: "A tooltip" if idx % 2 == 0 else "Another tooltip"}|>
        ```

    === "HTML"

        ```html
        <taipy:table tooltip="{lambda state, val, idx: 'A tooltip' if idx % 2 == 0 else 'Another tooltip'}">{data}</taipy:table>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.table("{data}", tooltip="{lambda state, val, idx: 'A tooltip' if idx % 2 == 0 else 'Another tooltip'}")
        ```
