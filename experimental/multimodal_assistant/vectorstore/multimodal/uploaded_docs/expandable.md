---
title: <tt>expandable</tt>
hide:
  - navigation
---

<!-- Category: blocks -->
Displays its child elements in a collapsible area.

Expandable is a block control.

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
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>Title of this block element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-expanded">expanded</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>If True, the block is expanded, and the content is displayed.<br/>If False, the block is collapsed and its content is hidden.</p></td>
</tr>
<tr>
<td nowrap><code id="p-partial">partial</code></td>
<td><code>Partial</code></td>
<td nowrap></td>
<td><p>A Partial object that holds the content of the block.<br/>This should not be defined if <i>page</i> is set.</p></td>
</tr>
<tr>
<td nowrap><code id="p-page">page</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The page name to show as the content of the block.<br/>This should not be defined if <i>partial</i> is set.</p></td>
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
  </tbody>
</table>

<p><sup id="dv">(&#9733;)</sup><a href="#p-value" title="Jump to the default property documentation."><code>value</code></a> is the default property for this visual element.</p>

# Styling

All the expandable blocks are generated with the "taipy-expandable" CSS class. You can use this class
name to select the expandable blocks on your page and apply style.

# Usage

## Defining a title and managing expanded state

The default property [*title*](#p-title) defines the title shown when the visual element is
collapsed.

!!! example "Definition"

    === "Markdown"

        ```
        <|Title|expandable|expand={expand}|>
        ```

    === "HTML"

        ```html
        <taipy:expandable expand="{expand}">Title</taipy:expandable>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.expandable("Title", expand="{expand}")
        ```

## Content as block

The content of `expandable` can be specified as the block content.

!!! example "Definition"

    === "Markdown"

        ```
        <|Title|expandable|
            ...
            <|{some_content}|>
            ...
        |>
        ```
  
    === "HTML"

        ```html
        <taipy:expandable title="Title">
            ...
            <taipy:text>{some_content}</taipy:text>
            ...
        </taipy:expandable>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.expandable("Title")
            tgb.text("{some_content}")
        ```

## Expandable with page

The content of the expandable can be specified as an existing page name using the [*page*](#p-page)
property.

!!! example "Definition"

    === "Markdown"

        ```
        <|Title|expandable|page=page_name|>
        ```

    === "HTML"

        ```html
        <taipy:expandable page="page_name">Title</taipy:expandable>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.expandable("Title", page="page_name")
        ```

## Expandable with partial

The content of the expandable can be specified as a `Partial^` instance using the
[*partial*](#p-partial) property.

!!! example "Definition"

    === "Markdown"

        ```
        <|Title|expandable|partial={partial}|>
        ```

    === "HTML"

        ```html
        <taipy:expandable partial="{partial}">Title</taipy:expandable>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.expandable("Title", partial="{partial}")
        ```
