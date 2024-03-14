---
title: <tt>layout</tt>
hide:
  - navigation
---

<!-- Category: blocks -->
Organizes its children into cells in a regular grid.

The _columns_ property follows the [CSS standard](https://developer.mozilla.org/en-US/docs/Web/CSS/grid-template-columns) syntax.
If the _columns_ property contains only digits and spaces, it is considered as flex-factor unit:
"1 1" => "1fr 1fr"

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
<td nowrap><code id="p-columns"><u><bold>columns</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>str</code></td>
<td nowrap>"1 1"</td>
<td><p>The list of weights for each column.<br/>For example, `"1 2"` creates a 2 column grid:
<ul>
<li>1fr</li>
<li>2fr</li>
</ul><br/>The creation of multiple same size columns can be simplified by using the multiply sign eg. "5*1" is equivalent to "1 1 1 1 1".</p></td>
</tr>
<tr>
<td nowrap><code id="p-columns[mobile]">columns[mobile]</code></td>
<td><code>str</code></td>
<td nowrap>"1"</td>
<td><p>The list of weights for each column, when displayed on a mobile device.<br/>The syntax is the same as for <i>columns</i>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-gap">gap</code></td>
<td><code>str</code></td>
<td nowrap>"0.5rem"</td>
<td><p>The size of the gap between the columns.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-columns" title="Jump to the default property documentation."><code>columns</code></a> is the default property for this visual element.</p>

# Styling

All the layout blocks are generated with the "taipy-layout" CSS class. You can use this class
name to select the layout blocks on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides specific classes that you can use to style layout
blocks:

- *align-columns-top*<br/>
  Aligns the content to the top of each column.
- *align-columns-center*<br/>
  Aligns the content to the center of each column.
- *align-columns-bottom*<br/>
  Aligns the content to the bottom of each column.
- *align-columns-stretch*<br/>
  Gives all columns the height of the highest column.

Additional classes are defined for the [`part`](part.md) block element when inserted in
a layout block. Please see the [section on styling](part.md#stylekit-support) for parts
for more details.

# Usage

## Default layout

The default layout contains 2 columns in desktop mode and 1 column in mobile mode.

!!! example "Definition"

    === "Markdown"

        ```
        <|layout|

        <|{some_content}|>

        |>
        ```
  
    === "HTML"

        ```html
        <taipy:layout>

            <taipy:text>{some_content}</taipy:text>

        </taipy:layout>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.layout()
            tgb.text("{some_content}")
        ```

## Specifying gap

The *gap* between adjacent cells is set by default to 0.5rem and can be specified using the
[*gap*](#p-gap) property.

!!! example "Definition"

    === "Markdown"

        ```
        <|layout|gap=20px|
        ...
        <|{some_content}|>
        ...
        |>
        ```
  
    === "HTML"

        ```html
        <taipy:layout gap="20px">
            ...
            <taipy:text>{some_content}</taipy:text>>
            ...
        </taipy:layout>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.layout(gap="20px")
            tgb.text("{some_content}")
        ```

## Layout with a central "greedy" column

You can use the `fr` CSS unit so that the middle column use all the available space.

!!! example "Definition"

    === "Markdown"

        ```
        <|layout|columns=50px 1fr 50px|

        <|1st column content|>

        <|2nd column content|>

        <|3rd column content|>

        <|1st column and second row content|>

        ...
        |>
        ```
  
    === "HTML"

        ```html
        <taipy:layout columns="50px 1fr 50px">
            <taipy:part>
                <taipy:text>1st column content</taipy:text>
            </taipy:part>
            <taipy:part>
                <taipy:text>2nd column content</taipy:text>
            </taipy:part>
            <taipy:part>
                <taipy:text>3rd column content</taipy:text>
            </taipy:part>
            <taipy:part>
                <taipy:text>1st column and second row content</taipy:text>
            </taipy:part>
            ...
        </taipy:layout>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.layout(columns="50px 1fr 50px")
            with tgb.part()
                tgb.text("1st column content")
            with tgb.part()
                tgb.text("2nd column content")
            with tgb.part()
                tgb.text("3rd column content")
            with tgb.part()
                tgb.text("1st column and second row content")
        ```

## Different layout for desktop and mobile devices

The [*columns[mobile]*](#p-columns[mobile]) property allows to specify a different layout when
running on a mobile device.

!!! example "Definition"

    === "Markdown"

        ```
        <|layout|columns=50px 1fr 50px|columns[mobile]=1 1|

        <|1st column content|>

        <|2nd column content|>

        <|3rd column content or 2nd row 1st column on mobile|>

        <|1st column and second row content or 2nd row 2nd column on mobile|>

        ...
        |>
        ```
  
    === "HTML"

        ```html
        <taipy:layout columns="50px 1fr 50px" columns[mobile]="1 1">
            <taipy:part>
                <taipy:text>1st column content</taipy:text>
            </taipy:part>
            <div>
                <taipy:text>2nd column content</taipy:text>
            </div>
            <taipy:part>
                <taipy:text>3rd column content or 2nd row 1st column on mobile</taipy:text>
            </taipy:part>
            <taipy:part>
                <taipy:text>1st column and second row content or 2nd row 2nd column on mobile</taipy:text>
            </taipy:part>
            ...
        </taipy:layout>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        with tgb.layout(columns="50px 1fr 50px", columns[mobile]="1 1")
            with tgb.part()
                tgb.text("1st column content")
            with tgb.part()
                tgb.text("2nd column content")
            with tgb.part()
                tgb.text("3rd column content or 2nd row 1st column on mobile")
            with tgb.part()
                tgb.text("1st column and second row content or 2nd row 2nd column on mobile")
        ```
