---
title: <tt>tree</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A control that allows for selecting items from a hierarchical view of items.

Each item is represented by a string, an image, or both.

The tree can let the user select multiple items.

A filtering feature is available to display only a subset of the items.

You can use an arbitrary type for all the items (see the [example](#binding-to-a-list-of-objects)).


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
<td nowrap><code id="p-expanded">expanded</code></td>
<td><code>bool|str[]</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>If Boolean and False, only one node can be expanded at one given level. Otherwise this should be set to an array of the node identifiers that need to be expanded.</p></td>
</tr>
<tr>
<td nowrap><code id="p-multiple">multiple</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, the user can select multiple items by holding the <code>Ctrl</code> key while clicking on items.</p></td>
</tr>
<tr>
<td nowrap><code id="p-select_leafs_only">select_leafs_only</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, the user can only select leaf nodes.</p></td>
</tr>
<tr>
<td nowrap><code id="p-row_height">row_height</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The height, in CSS units, of each row.</p></td>
</tr>
<tr>
<td nowrap><code id="p-filter">filter</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, this control is combined with a filter input area.</p></td>
</tr>
<tr>
<td nowrap><code id="p-width">width</code></td>
<td><code>str|int</code></td>
<td nowrap>"360px"</td>
<td><p>The width, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str|int</code></td>
<td nowrap></td>
<td><p>The height, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-dropdown">dropdown</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, the list of items is shown in a dropdown menu.<br/><br/>You cannot use the filter in that situation.</p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code></td>
<td nowrap>None</td>
<td><p>The label associated with the selector when in dropdown mode.</p></td>
</tr>
<tr>
<td nowrap><code id="p-mode">mode</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>Define the way the selector is displayed:<ul><li>&quot;radio&quot;: list of radio buttons</li><li>&quot;check&quot;: list of check buttons</li><li>any other value: selector as usual.</p></td>
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

All the tree controls are generated with the "taipy-tree" CSS class. You can use this class
name to select the tree controls on your page and apply style.

# Usage

## Display a list of string

You can create a tree on a series of strings:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|tree|lov=Item 1;Item 2;Item 3|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="Item 1;Item 2;Item 3">{value}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{value}", lov="Item 1;Item 2;Item 3")
        ```

## Display with filter and multiple selection

You can add a filter input field that lets you display only strings that match the filter value.

The following tree definition will create a tree control that shows the filter selection
(setting the [*filter*](#p-filter) property to True) and allows users to select multiple items
(setting the [*multiple*](#p-multiple) property to True):
!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|tree|lov=Item 1;Item 2;Item 3|filter|multiple|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="Item 1;Item 2;Item 3" filter multiple>{value}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{value}", lov="Item 1;Item 2;Item 3", filter=True, multiple=True)
        ```

## Display a list of tuples

The [*lov*](#p-lov) property value can be defined so that the tree displays labels and icons
while reflecting the selection by identifiers:
!!! example "Definition"

    === "Markdown"

        ```
        <|{sel}|tree|lov={[("id1", "Label 1", [("id1.1", "Label 1.1"), ("id1.2", "Label 1.2")]), ("id2", Icon("/images/icon.png", "Label 2")), ("id3", "Label 3", [("id3.1", "Label 3.1"), ("id3.2", "Label 3.2")])]}|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="{[('id1', 'Label 1', [('id1.1', 'Label 1.1'), ('id1.2', 'Label 1.2')]), ('id2', Icon('/images/icon.png', 'Label 2')), ('id3', 'Label 3', [('id3.1', 'Label 3.1'), ('id3.2', 'Label 3.2')])]}">
        {sel}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{sel}", lov="{[('id1', 'Label 1', [('id1.1', 'Label 1.1'), ('id1.2', 'Label 1.2')]), ('id2', Icon('/images/icon.png', 'Label 2')), ('id3', 'Label 3', [('id3.1', 'Label 3.1'), ('id3.2', 'Label 3.2')])]}")
        ```

## Manage expanded nodes

The property [*expanded*](#p-expanded) must be used to control the expanded/collapse state of the
nodes. By default, the user can expand or collapse nodes.<br/>
If [*expanded*](#p-expanded) is set to False, there can be only one expanded node at any given
level of the tree:  if a node is expanded at a certain level and the user clicks on another node at
the same level, the first node will be automatically collapsed.

The [*expanded*](#p-expanded) property can also hold a list of node identifiers that are expanded.

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|tree|lov=Item 1;Item 2;Item 3|not expanded|>

        <|{value}|tree|lov=Item 1;Item 2;Item 3|expanded=Item 2|>
        ```

    === "HTML"

        ```html
        <taipy:tree value="{value}" lov="Item 1;Item 2;Item 3" expanded="False" />

        <taipy:tree value="{value}" lov="Item 1;Item 2;Item 3" expanded="Item 2" />
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("value", lov="Item 1;Item 2;Item 3", expanded=False)
        tgb.tree("value", lov="Item 1;Item 2;Item 3", expanded="Item 2")
        ```

## Display a tree of dictionary entries

The tree control has a predefined adapter that can display the definition of a dictionary
structure set to the [*lov*](#p-lov) property as long as each dictionary entry has an *id* and
a *label* key, as well as a *children* key that would hold, in a list, the children of a given
entry. Each child has the same constraints: the *id*, label*, and *children* keys must be
present.<br/>
An entry with no children needs to set an empty list as the value of its *children* key.

Here is an example. Assuming your Python code has created a list of dictionaries:
```python
users = [
    {"id": "231", "label": "Johanna", "year": 1987, "children": [{"id": "231.1", "label": "Johanna's son", "year": 2006}]},
    {"id": "125", "label": "John",    "year": 1979, "children": []},
    {"id": "4",   "label": "Peter",   "year": 1968, "children": []},
    {"id": "31",  "label": "Mary",    "year": 1974, "children": []}
    ]

user_sel = users[2]
```

The definition of a tree control that can represent this data is as simple as:
!!! example "Definition"

    === "Markdown"

        ```
        <|{user_sel}|tree|lov={users}|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="{users}">{user_sel}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{user_sel}", lov="{users}")
        ```

## Display a list of objects with the built-in adapter

Objects with attributes *id*, *label*, and *children* (set to a list) can be dealt with
automatically by the built-in *lov* adapter of the tree control.

Assuming your Python code has created a list of such objects:
```python
class User:
    def __init__(self, id, label, birth_year, children):
        self.id, self.label, self.birth_year, self.children = (id, label, birth_year, children)

users = [
    User(231, "Johanna", 1987, [User(231.1, "Johanna's son", 2006, [])]),
    User(125, "John",    1979, []),
    User(4,   "Peter",   1968, []),
    User(31,  "Mary",    1974, [])
    ]

user_sel = users[2]
```

If you want to create a tree control that lets users pick a specific user, you
can use the following control definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{user_sel}|tree|lov={users}|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="{users}">{user_sel}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{user_sel}", lov="{users}")
        ```

## Display a hierarchy of arbitrary objects

The [*adapter*](#p-adapter) property can be set to a function that transforms an arbitrary object
to a representation that the tree control can use: a tuple where the first element is an
identifier of the object (used in the [*value*](#p-value) property), the second element represents
the item's label, and the third element is a list to child objects.

Assuming your Python code has created a list of objects:
```python
class User:
    def __init__(self, id, name, birth_year, children):
        self.id, self.name, self.birth_year, self.children = (id, name, birth_year, children)

users = [
    User(231, "Johanna", 1987, [User(231.1, "Johanna's son", 2006, [])]),
    User(125, "John",    1979, []),
    User(4,   "Peter",   1968, []),
    User(31,  "Mary",    1974, [])
    ]

user_sel = users[2]
```

In this example, we use the Python list *users* as the tree's *list of values*.
Because the control needs a way to convert the list items (which are instances of the class
*User*) into a string that can be displayed, we are using an *adapter*: a function that converts
an object whose type must be provided to the *type* property to a tuple.

In our situation, the adapter can be a lambda function that returns
the adapted tuple for each object in the hierarchy:
!!! example "Definition"

    === "Markdown"

        ```
        <|{user_sel}|tree|lov={users}|type=User|adapter={lambda u: (u.id, u.name, u.children)}|>
        ```

    === "HTML"

        ```html
        <taipy:tree lov="{users}" type="User" adapter="{lambda u: (u.id, u.name, u.children)}">{user_sel}</taipy:tree>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.tree("{user_sel}", lov="{users}", type="User", adapter="{lambda u: (u.id, u.name, u.children)}")
        ```


