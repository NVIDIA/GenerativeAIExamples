---
title: <tt>toggle</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A series of toggle buttons that the user can select.

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
<td><code>any</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>Bound to the selection value.</p></td>
</tr>
<tr>
<td nowrap><code id="p-theme">theme</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If set, this toggle control acts as a way to set the application Theme (dark or light).</p></td>
</tr>
<tr>
<td nowrap><code id="p-allow_unselect">allow_unselect</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If set, this allows de-selection and the value is set to unselected_value.</p></td>
</tr>
<tr>
<td nowrap><code id="p-mode">mode</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>Define the way the toggle is displayed:<ul><li>&quot;theme&quot;: synonym for setting the *theme* property to True</li></ul></p></td>
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

# Details

Each button is represented by a string, an image or both.

You can use an arbitrary type for all the items (see the [example](#use-arbitrary-objects)).

# Styling

All the toggle controls are generated with the "taipy-toggle" CSS class. You can use this class
name to select the toggle controls on your page and apply style.

The [Stylekit](../styling/stylekit.md) also provides specific CSS classes that you can use to style
toggle controls:

- *relative*<br/>
  Resets the theme toggle position in the page flow (especially for the theme mode toggle).
- *nolabel*<br/>
  Hides the toggle control's label.
- *taipy-navbar*<br/>
  Gives the toggle control the look and feel of a [`navbar`](navbar.md).

# Usage

## Display a list of string

You can create a list of toggle buttons from a series of strings:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|toggle|lov=Item 1;Item 2;Item 3|>
        ```

    === "HTML"

        ```html
        <taipy:toggle lov="Item 1;Item 2;Item 3">{value}</taipy:toggle>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.toggle("{value}", lov="Item 1;Item 2;Item 3")
        ```

## Unselect value

In a toggle control, all buttons might be unselected. Therefore there is no value selected.
In that case, the value of the property [*unselected_value*](#p-unselected_value) is assigned if
specified.

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|toggle|lov=Item 1;Item 2;Item 3|unselected_value=No Value|>
        ```

    === "HTML"

        ```html
        <taipy:toggle lov="Item 1;Item 2;Item 3" unselected_value="No Value">{value}</taipy:toggle>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.toggle("{value}", lov="Item 1;Item 2;Item 3", unselected_value="No Value")
        ```

## Display a list of tuples

A toggle control that returns an id while selecting a label or `Icon^`.

!!! example "Definition"

    === "Markdown"

        ```
        <|{sel}|toggle|lov={[("id1", "Label 1"), ("id2", Icon("/images/icon.png", "Label 2"),("id3", "Label 3")]}|>
        ```

    === "HTML"

        ```html
        <taipy:toggle lov="{[('id1', 'Label 1'), ('id2', Icon('/images/icon.png', 'Label 2'),('id3', 'Label 3')]}">{sel}</taipy:toggle>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.toggle("{sel}", lov="{[('id1', 'Label 1'), ('id2', Icon('/images/icon.png', 'Label 2'),('id3', 'Label 3')]}")
        ```

## Use arbitrary objects

Assuming your Python code has created a list of objects:
```py3
class User:
    def __init__(self, id, name, birth_year):
        self.id, self.name, self.birth_year = (id, name, birth_year)

users = [
    User(231, "Johanna", 1987),
    User(125, "John", 1979),
    User(4,   "Peter", 1968),
    User(31,  "Mary", 1974)
    ]

user_sel = users[2]
```

If you want to create a toggle control that lets you pick a specific user, you
can use the following fragment:

!!! example "Definition"

    === "Markdown"

        ```
        <|{user_sel}|toggle|lov={users}|type=User|adapter={lambda u: (u.id, u.name)}|>
        ```

    === "HTML"

        ```html
        <taipy:toggle lov="{users}" type="User" adapter="{lambda u: (u.id, u.name)}">{user_sel}</taipy:toggle>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.toggle("{user_sel}", lov="{users}", type="User", adapter="{lambda u: (u.id, u.name)}")
        ```

In this example, we are using the Python list *users* as the toggle's *list of values*.
Because the control needs a way to convert the list items (which are instances of the class
*User*) into a string that can be displayed, we are using an *adapter*: a function that converts
an object, whose type must be provided to the [*type*](#p-type) property, to a tuple. The first
element of the tuple is used to reference the selection (therefore those elements should be unique
among all the items) and the second element is the string that turns out to be displayed.
