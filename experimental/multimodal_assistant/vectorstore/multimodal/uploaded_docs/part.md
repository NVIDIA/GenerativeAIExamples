---
title: <tt>part</tt>
hide:
  - navigation
---

<!-- Category: blocks -->
Displays its children in a block.

The `part` block is used to group visual elements into a single element.
This allows to show or hide them in one action and be placed as a unique element in a
[`Layout`](layout.md) cell.

There is a simplified Markdown syntax to create a `part`, where the element name is optional:

`<|` just before the end of the line indicates the beginning of a `part` element;
`|>` at the beginning of a line indicates the end of the `part` definition.

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
<td nowrap><code id="p-class_name"><u><bold>class_name</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>A list of CSS class names, separated by white spaces, that will be associated with the generated HTML Element.<br/>These class names are added to the default <code>taipy-part</code>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-render">render</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>If True, this part is visible on the page.<br/>If False, the part is hidden and its content is not displayed.</p></td>
</tr>
<tr>
<td nowrap><code id="p-page">page</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The page to show as the content of the block (page name if defined or a URL in an <i>iframe</i>).<br/>This should not be defined if <i>partial</i> is set.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The height, in CSS units, of this block.</p></td>
</tr>
<tr>
<td nowrap><code id="p-content">content</code></td>
<td><code>any</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The content provided to the part. See the documentation section on content providers.</p></td>
</tr>
<tr>
<td nowrap><code id="p-partial">partial</code></td>
<td><code>Partial</code></td>
<td nowrap></td>
<td><p>A Partial object that holds the content of the block.<br/>This should not be defined if <i>page</i> is set.</p></td>
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
<td nowrap><code id="p-hover_text">hover_text</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The information that is displayed when the user hovers over this element.</p></td>
</tr>
  </tbody>
</table>

<p><sup id="dv">(&#9733;)</sup><a href="#p-class_name" title="Jump to the default property documentation."><code>class_name</code></a> is the default property for this visual element.</p>

# Styling

All the part blocks are generated with the "taipy-part" CSS class. You can use this class
name to select the part blocks on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides specific classes that you can use to style part
blocks:

- *align-item-top*<br/>
  If this part block is inside a [`layout`](layout.md) block, this CSS class aligns the part
  content to the top of the layout column it belongs to.
- *align-item-center*<br/>
  If this part block is inside a [`layout`](layout.md) block, this CSS class vertically aligns
  the part content to the center of the layout column it belongs to.
- *align-item-bottom*<br/>
  If this part block is inside a [`layout`](layout.md) block, this CSS class vertically aligns
  the part content to the bottom of the layout column it belongs to.
- *align-item-stretch*<br/>
  If this part block is inside a [`layout`](layout.md) block, this CSS class 
  gives the part the same height as the highest item in the row where this part
  appears in the layout.

The Stylekit also has several classes that can be used to style part blocks,
as described in the [Styled Sections](../styling/stylekit.md#styled-sections)
documentation.<br/>
Because the default property of the *part* block is *class_name*, you can use the
Markdown short syntax for parts:

```
<|card|
...
(card content)
...
|>
```

Creates a `part` that has the [*card*](../styling/stylekit.md#card) class defined
in the Stylekit.

# Usage

## Grouping controls

The most straightforward use of the `part` block is to group different visual elements in a single
element to make it easy to manipulate.

!!! example "Definition"
    === "Markdown"
        ```
        <|
        ...
        <|{some_content}|>
        ...
        |>
        ```

    === "HTML"
        ```html
        <taipy:part>
            ...
            <taipy:text>{some_content}</taipy:text>
            ...
        </taipy:part>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.part()
            tgb.text("{some_content}")
        ```

## Showing and hiding controls

If you set the [*render*](#p-render) property to False, the `part` is not rendered
at all:

!!! example "Page content"
    === "Markdown"
        ```
        <|part|don't render|
        ...
        <|{some_content}|>
        ...
        |>
        ```

    === "HTML"
        ```html
        <taipy:part render="false">
            ...
            <taipy:text>{some_content}</taipy:text>
            ...
        </taipy:part>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.part(render=False)
            tgb.text("{some_content}")
        ```

If the value of [*render*](#p-render) is bound to a Boolean value, the `part` will show or hide its
elements according to the value of the bound variable.

## Styling parts

The default property name of the `part` block is [*class_name*](#p-class_name). This allows setting
a CSS class to a `part` with a very simple Markdown syntax:

!!! example "Markdown content"
    ```
    <|css-class|
    ...
    (part content)
    ...
    |>
    ```

This creates a `part` block that is applied the *css-class* CSS class defined in the
application stylesheets.

## Part showing a page

The content of the part can be specified as an existing page name or an URL using the *page*
property.

You can embed an existing Taipy GUI page within another page using the [*page*](#p-page) property,
setting it to a page name.<br/>
If your application has registered the *page_name* page, you can show it on another page using the
following page definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|part|page=page_name|>
        ```

    === "HTML"

        ```html
        <taipy:part page="page_name"/>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.part(page="page_name")
        ```

You can also embed an external web page, setting the [*page*](#p-page) property to the URL
(starting with `http://` or `https://`) you want to render:

!!! example "Definition"
    === "Markdown"
        ```
        Here is the Wikipedia home page:
        <|part|page=https://www.wikipedia.org/|height=500px|>
        ```

    === "HTML"
        ```html
        <p>Here is the Wikipedia home page:</p>
        <taipy:part page="https://www.wikipedia.org/" height="500px"/>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.html("p", "Here is the Wikipedia home page:")
        with tgb.part(page="https://www.wikipedia.org/", height="500px")

The resulting page will be displayed as this:
<figure class="tp-center">
    <img src="../part-url-d.png" class="visible-dark"  width="80%"/>
    <img src="../part-url-l.png" class="visible-light" width="80%"/>
    <figcaption>Embedding an external web page</figcaption>
</figure>

Note that you may have to tune the value of the [*height*](#p-height) property since the external
page  controls the layout if you omit it. This would be set to a CSS dimension value (typically
"100%" when the part appears inside a [`layout`](layout.md) block).

## Part showing a partial

The content of the part can be specified as a `Partial^` instance using the [*partial*](#p-partial)
property.

!!! example "Definition"

    === "Markdown"

        ```
        <|part|partial={partial}|>
        ```

    === "HTML"

        ```html
        <taipy:part partial="{partial}"/>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.part(partial="{partial}")
        ```
