---
title: <tt>text</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Displays a value as a static text.

Note that in order to create a `text` control, you don't need to specify the control name
in the text template. See the documentation for [Controls](controls.md) for more details.

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
<td nowrap>""</td>
<td><p>The value displayed as text by this control.</p></td>
</tr>
<tr>
<td nowrap><code id="p-raw">raw</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If set to True, the component renders as an HTML &lt;span&gt; element without any default style.</p></td>
</tr>
<tr>
<td nowrap><code id="p-mode">mode</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>Define the way the text is processed:<ul><li>&quot;raw&quot;: synonym for setting the *raw* property to True</li><li>&quot;pre&quot;: keeps spaces and new lines</li><li>&quot;markdown&quot; or &quot;md&quot;: basic support for Markdown.</p></td>
</tr>
<tr>
<td nowrap><code id="p-format">format</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The format to apply to the value.<br/>See below.</p></td>
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

The [*format*](#p-format) property uses a format string like the ones used by the string *format()*
function of Python.

If the value is a `date` or a `datetime`, then [*format*](#p-format) can be set to a date/time
formatting string.

# Styling

All the text controls are generated with the "taipy-text" CSS class. You can use this class name to
select the text controls on your page and apply style.

# Usage

## Display value

You can represent a variable value as a simple, static text:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|>
        ```
  
    === "HTML"

        ```html
        <taipy:text>{value}</taipy:text>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.text("{value}")
        ```

## Formatted output

If your value is a floating point value, you can use the [*format*](#p-format) property to indicate
what the output format should be used.

To display a floating point value with two decimal places:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|text|format=%.2f|>
        ```

    === "HTML"

        ```html
        <taipy:text format="%.2f">{value}</taipy:text>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.text("{value}", format="%.2f")
        ```
