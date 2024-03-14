---
title: <tt>date</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A control that can display and specify a formatted date, with or without time.

!!! warning "Warning on Windows"

    When you are using dates earlier than January 1st, 1970 (the UNIX epoch) in a date control on a
    Windows system, you may receive a warning in the console where the script was run, indicating a
    raised exception in `datetime.astimezone()`.<br/>
    This is a known problem in the Python implementation, referenced in the
    [Python issue tracker](https://bugs.python.org/issue36759), that Taipy has no workaround for.

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
<td nowrap><code id="p-date"><u><bold>date</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>datetime</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The date that this control represents and can modify.<br/>It is typically bound to a <code>datetime</code> object.</p></td>
</tr>
<tr>
<td nowrap><code id="p-with_time">with_time</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>Whether or not to show the time part of the date.</p></td>
</tr>
<tr>
<td nowrap><code id="p-format">format</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The format to apply to the value. See below.</p></td>
</tr>
<tr>
<td nowrap><code id="p-editable">editable</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>Shows the date as a formatted string if not editable.</p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The label associated with the input.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-date" title="Jump to the default property documentation."><code>date</code></a> is the default property for this visual element.</p>

# Details

The [*format*](#p-format) property lets you indicate how to display the date object set to the
[*date*](#p-date) property. Note that the format is used only when [*editable*](#p-editable) is set
to False (the date control is read-only).<br/>
This property can be set to a format string that is consumed by the
[date-fns.format()](https://date-fns.org/docs/format) function. The documentation for this
function provides all the different format strings you might need.<br/>
For more information, you can look at the [formatting example](#formatting-the-date) below.

# Styling

All the date controls are generated with the "taipy-date" CSS class. You can use this class
name to select the date selectors on your page and apply style.

### [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides a specific class that you can use to style date selectors:

* *fullwidth*<br/>
    If a date selector uses the *fullwidth* class, then it uses the whole available
    horizontal space.

# Usage

## Using only the date

Assuming a variable *date* contains a Python `datetime` object:
```python
import datetime

date = datetime.datetime(1789, 7, 14, 17, 5, 12)
```

You can create a date selector that represents it with the following definition:

!!! example "Definition"

    === "Markdown"

        ```
        <|{date}|date|>
        ```

    === "HTML"

        ```html
        <taipy:date>{date}</taipy:date>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.date("{date}")
        ```

The resulting control appears on the page similarly to:

<figure>
    <img src="../date-simple-d.png" class="visible-dark" />
    <img src="../date-simple-l.png" class="visible-light"/>
    <figcaption>A date selector</figcaption>
    </figure>

Note that because the [*with_time*](#p-with_time) property is set to False by default, only the
date part of the *date* object is displayed.

## Using the full date and time

If you do need to use the time, you can set the [*with_time*](#p-with_time) property to True.<br/>
Keeping the definition of the *date* object from the example above, we can change the definition
of the control to:

!!! example "Definition"

    === "Markdown"

        ```
        <|{date}|date|with_time|>
        ```

    === "HTML"

        ```html
        <taipy:date with_time>{date}</taipy:date>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.date("{date}", with_time=True)
        ```

Then the date selector shows like this:
<figure>
    <img src="../date-with_time-d.png" class="visible-dark" />
    <img src="../date-with_time-l.png" class="visible-light"/>
    <figcaption>A date and time selector</figcaption>
</figure>

## Formatting the date

To format the date on the page, you must set the [*editable*](#p-editable) property to False.<br/>
Here is a definition of a read-only date selector control using the same *date* variable definition
as above:

!!! example "Definition"

    === "Markdown"

        ```
        <|{date}|date|not editable|>
        ```

    === "HTML"

        ```html
        <taipy:date editable="false">{date}</taipy:date>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.date("{date}", editable=False)
        ```

Here is how the control is displayed:
<figure>
    <img src="../date-not_editable-d.png" class="visible-dark" />
    <img src="../date-not_editable-l.png" class="visible-light"/>
    <figcaption>A read-only date selector</figcaption>
</figure>

When not editable, the `date` control looks just like a [`text`](text.md) control showing the
date object.<br/>
You can, however, control how to display that object by setting the [*format*](#p-format) property
to a formatting string as documented in the [date-fns.format()](https://date-fns.org/docs/format)
function.<br/>
Here is the definition of the `date` control where the [*format*](#p-format) property is set. Note
that, according to the [date-fns.format() documentation](https://date-fns.org/docs/format):

- "eeee" is replaced by the name of the day of the week
- "LLLL" is replaced by the name of the month
- "do" is replaced by the day of the month (including st, nd, and so forth)
- "y" is replaced by the year

!!! example "Definition"

    === "Markdown"

        ```
        <|{date}|date|not editable|format=eeee LLLL do, y|>
        ```

    === "HTML"

        ```html
        <taipy:date editable="false" format="eeee LLLL do, y">{date}</taipy:date>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.date("{date}", editable=False, format="eeee LLLL do, y")
        ```

The formatted date appears in the control:
<figure>
    <img src="../date-format-d.png" class="visible-dark" />
    <img src="../date-format-l.png" class="visible-light"/>
    <figcaption>A formatted date</figcaption>
</figure>
