---
title: <tt>slider</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Displays and allows the user to set a value within a range.

The range is set by the values `min` and `max` which must be integer values.

If the [*lov*](#p-lov) property is used, then the slider can be used to select a value among the
different choices.


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
<td nowrap><code id="p-value"><u><bold>value</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>int|float|int[]|float[]|str|str[]</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The value that is set for this slider.<br/>If this slider is based on a <i>lov</i> then this property can be set to the lov element.<br/>This value can also hold an array of numbers to indicate that the slider reflects a range (within the [<i>min</i>,<i>max</i>] domain) defined by several knobs that the user can set independently.<br/>If this slider is based on a <i>lov</i> then this property can be set to an array of lov elements. The slider is then represented with several knobs, one for each lov value.</p></td>
</tr>
<tr>
<td nowrap><code id="p-min">min</code></td>
<td><code>int|float</code></td>
<td nowrap>0</td>
<td><p>The minimum value.<br/>This is ignored when <i>lov</i> is defined.</p></td>
</tr>
<tr>
<td nowrap><code id="p-max">max</code></td>
<td><code>int|float</code></td>
<td nowrap>100</td>
<td><p>The maximum value.<br/>This is ignored when <i>lov</i> is defined.</p></td>
</tr>
<tr>
<td nowrap><code id="p-step">step</code></td>
<td><code>int|float</code></td>
<td nowrap>1</td>
<td><p>The step value: the gap between two consecutive values the slider set. It is a good practice to have (<i>max</i>-<i>min</i>) being divisible by <i>step</i>.<br/>This property is ignored when <i>lov</i> is defined.</p></td>
</tr>
<tr>
<td nowrap><code id="p-text_anchor">text_anchor</code></td>
<td><code>str</code></td>
<td nowrap>"bottom"</td>
<td><p>When the <i>lov</i> property is used, this property indicates the location of the label.<br/>Possible values are:
<ul>
<li>"bottom"</li>
<li>"top"</li>
<li>"left"</li>
<li>"right"</li>
<li>"none" (no label is displayed)</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-labels">labels</code></td>
<td><code>bool|dict</code></td>
<td nowrap></td>
<td><p>The labels for specific points of the slider.<br/>If set to True, this slider uses the labels of the <i>lov</i> if there are any.<br/>If set to a dictionary, the slider uses the dictionary keys as a <i>lov</i> key or index, and the associated value as the label.</p></td>
</tr>
<tr>
<td nowrap><code id="p-continuous">continuous</code></td>
<td><code>bool</code></td>
<td nowrap>True</td>
<td><p>If set to False, the control emits an on_change notification only when the mouse button is released, otherwise notifications are emitted during the cursor movements.<br/>If <i>lov</i> is defined, the default value is False.</p></td>
</tr>
<tr>
<td nowrap><code id="p-change_delay">change_delay</code></td>
<td><code>int</code></td>
<td nowrap><i>App config</i></td>
<td><p>Minimum time between triggering two <i>on_change</i> calls.<br/>The default value is defined at the application configuration level by the <strong>change_delay</strong> configuration option. if None or 0, there's no delay.</p></td>
</tr>
<tr>
<td nowrap><code id="p-width">width</code></td>
<td><code>str</code></td>
<td nowrap>"300px"</td>
<td><p>The width, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The height, in CSS units, of this element.<br/>It defaults to the <i>width</i> value when using the vertical orientation.</p></td>
</tr>
<tr>
<td nowrap><code id="p-orientation">orientation</code></td>
<td><code>str</code></td>
<td nowrap>"horizontal"</td>
<td><p>The orientation of this slider.<br/>Valid values are "horizontal" or "vertical".</p></td>
</tr>
<tr>
<td nowrap><code id="p-lov">lov</code></td>
<td><code>dict[str, any]</code></td>
<td nowrap></td>
<td><p>The list of values. See the <a href="../../binding/#list-of-values">section on List of Values</a> for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-adapter">adapter</code></td>
<td><code>Function</code></td>
<td nowrap>`lambda x: str(x)`</td>
<td><p>The function that transforms an element of <i>lov</i> into a <i>tuple(id:str, label:str|Icon)</i>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-type">type</code></td>
<td><code>str</code></td>
<td nowrap><i>Type of first lov element</i></td>
<td><p>Must be specified if <i>lov</i> contains a non-specific type of data (ex: dict).<br/><i>value</i> must be of that type, <i>lov</i> must be an iterable on this type, and the adapter function will receive an object of this type.</p></td>
</tr>
<tr>
<td nowrap><code id="p-value_by_id">value_by_id</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If False, the selection value (in <i>value</i>) is the selected element in <i>lov</i>. If set to True, then <i>value</i> is set to the id of the selected element in <i>lov</i>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_change">on_change</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the value is updated.<br/>The parameters of that function are all optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the variable name.</li>
<li>value (any): the new value.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-propagate">propagate</code></td>
<td><code>bool</code></td>
<td nowrap><i>App config</i></td>
<td><p>Allows the control's main value to be automatically propagated.<br/>The default value is defined at the application configuration level.<br/>If True, any change to the control's value is immediately reflected in the bound application variable.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-value" title="Jump to the default property documentation."><code>value</code></a> is the default property for this visual element.</p>

# Styling

All the slider controls are generated with the "taipy-slider" CSS class. You can use this class
name to select the sliders on your page and apply style.

# Usage

## Selecting a value in a range {data-source="gui:doc/examples/controls/slider-simple.py"}

A numeric value can easily be represented and interacted with using the following content:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|slider|>
        ```

    === "HTML"

        ```html
        <taipy:slider>{value}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{value}")
        ```

The page contains a slider that looks like this:
<figure>
    <img src="../slider-simple-d.png" class="visible-dark" />
    <img src="../slider-simple-l.png" class="visible-light"/>
    <figcaption>A simple slider</figcaption>
</figure>

The user can pick the slider knob and move it around to select a value within the default range
[0, 100].

## Setting the slider range {data-source="gui:doc/examples/controls/slider-range.py"}

You can specify, in the [*min*](#p-min) and [*max*](#p-max) properties, what bounds the selected
value should be constrained to:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|slider|min=1|max=10|>
        ```

    === "HTML"

        ```html
        <taipy:slider min="1" max="10">{value}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{value}", min="1", max="10")
        ```

The resulting slider looks like this:
<figure>
    <img src="../slider-range-d.png" class="visible-dark" />
    <img src="../slider-range-l.png" class="visible-light"/>
    <figcaption>Custom range</figcaption>
</figure>

## Changing orientation {data-source="gui:doc/examples/controls/slider-orientation.py"}

A slider can also be vertical if the [*orientation*](#p-orientation) property is set to a string
beginning with the letter "v".

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|slider|orientation=vert|>
        ```

    === "HTML"

        ```html
        <taipy:slider orientation="vert">{value}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{value}", orientation="vert")
        ```

And now the slider is displayed vertically:
<figure>
    <img src="../slider-orientation-d.png" class="visible-dark" />
    <img src="../slider-orientation-l.png" class="visible-light"/>
    <figcaption>Changing the default orientation</figcaption>
</figure>

## Select among a list of values {data-source="gui:doc/examples/controls/slider-lov.py"}

A slider can also allow users to select a value from a list of predefined values.<br/>
To do this, you must set the [*lov*](#p-lov) property to a list of values:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|slider|lov=XXS;XS;S;M;L;XL;XXL|>
        ```

    === "HTML"

        ```html
        <taipy:slider lov="XXS;XS;S;M;L;XL;XXL">{value}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{value}", lov="XXS;XS;S;M;L;XL;XXL")
        ```

Then only those values are accessible by the user:
<figure>
    <img src="../slider-lov-d.png" class="visible-dark" />
    <img src="../slider-lov-l.png" class="visible-light"/>
    <figcaption>List of values</figcaption>
</figure>

## Multi selection {data-source="gui:doc/examples/controls/slider-multiple.py"}

You can use a slider control to display multiple values and let users select each.<br/>
To achieve that, the [*value*](#p-value) property must be initially set to an array containing
the initial values to reflect. The slider will have one knob for each value.<br/>
When the user moves any of the knobs, the [`on_change`](../callbacks.md#variable-value-change)
callback is invoked with the variable value set to an array containing the new selection.

Let's create an initial value for our slider:
```py
values = [20, 40, 80]
```

And use this variable as the [*value*](#p-value) property value:

!!! example "Definition"

    === "Markdown"

        ```
        <|{values}|slider|>
        ```

    === "HTML"

        ```html
        <taipy:slider>{values}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{values}")
        ```

Because the initial value is an array with three values, the slider is displayed with three knobs
that the user can move:
<figure>
    <img src="../slider-multiple-d.png" class="visible-dark" />
    <img src="../slider-multiple-l.png" class="visible-light"/>
    <figcaption>Multiple values</figcaption>
</figure>

## Date range selection {data-source="gui:doc/examples/controls/slider-date-range.py"}

You can create a slider to select a date range, combining the use of the [*lov*](#p-lov) property
with a multi-knob slider.<br/>
Note that this can work only if your base date range (the one the user can pick from) is small enough
or it could be tricky for users to select a specific date.

Here is an example that lets you select a date range taken from an entire year.

You need to initialize an array of date strings that will be shown to the user as knobs are moved
along the slider:

```py
# Create the list of dates (all year 2000)
all_dates = {}
all_dates_str = []
start_date = date(2000, 1, 1)
end_date = date(2001, 1, 1)
a_date = start_date
while a_date < end_date:
    date_str = a_date.strftime("%Y/%m/%d")
    all_dates_str.append(date_str)
    all_dates[date_str] = a_date
    a_date += timedelta(days=1)

# Initial selection: first and last day
dates=[all_dates_str[1], all_dates_str[-1]]
# These two variables are used in text controls
start_sel = all_dates[dates[0]]
end_sel = all_dates[dates[1]]
```

Now, *all_dates_str* contains the list of all dates the user can choose from. We will use that
array as the value of the [*value*](#p-value) property.<br/>
*dates* holds the initial date range selection.

*start_sel* and *end_sel* are string values that can be used in text controls as a visual feedback.<br/>
We need to update these variables when the user picks new dates:

```py
def on_change(state, _, var_value):
    # Update the text controls
    state.start_sel = all_dates[var_value[0]]
    state.end_sel = all_dates[var_value[1]]
```

This callback will receive, in *var_value*, the array of the two selected dates. We can simply update
*start_sel* and *end_sel* accordingly.

The slider control definition is the following:

!!! example "Definition"

    === "Markdown"

        ```
        <|{dates}|slider|lov={all_dates_str}|>
        ```

    === "HTML"

        ```html
        <taipy:slider lov="{all_dates_str}">{dates}</taipy:slider>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.slider("{dates}", lov="{all_dates_str}")
        ```

And this is what this date range picker looks like:
<figure>
    <img src="../slider-date-range-d.png" class="visible-dark" />
    <img src="../slider-date-range-l.png" class="visible-light"/>
    <figcaption>Date range selection</figcaption>
</figure>
