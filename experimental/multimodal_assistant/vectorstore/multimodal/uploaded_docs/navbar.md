---
title: <tt>navbar</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A navigation bar control.

This control is implemented as a list of links.

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
<td nowrap><code id="p-lov"><u><bold>lov</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>dict[str, any]</code></td>
<td nowrap></td>
<td><p>The list of pages. The keys should be:
<ul>
<li>page id (start with "/")</li>
<li>or full URL</li>
</ul>
The values are labels. See the <a href="../../binding/#list-of-values">section on List of Values</a> for details.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-lov" title="Jump to the default property documentation."><code>lov</code></a> is the default property for this visual element.</p>

# Styling

All the navbar controls are generated with the "taipy-navbar" CSS class. You can use this class
name to select the navbar controls on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides a specific class that you can use to style navbar controls:

* *fullheight*<br/>
  Ensures the tabs fill the full height of their container (in a header bar for example).

# Usage

## Defining a default navbar

The list of all pages registered in the Gui instance is used to build the navbar.

!!! example "Definition"

    === "Markdown"

        ```
        <|navbar|>
        ```

    === "HTML"

        ```html
        <taipy:navbar/>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.navbar()
        ```

## Defining a custom navbar

The [*lov*](#p-lov) property is used to define the list of elements that are displayed.<br/>
If a lov element id starts with "http", the page is opened in another tab.

!!! example "Definition"

    === "Markdown"

        ```
        <|navbar|lov={[("page1", "Page 1"), ("http://www.google.com", "Google")]}|>
        ```

    === "HTML"

        ```html
        <taipy:navbar lov="{[('page1', 'Page 1'), ('http://www.google.com', 'Google')]}"/>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.navbar(lov="{[('page1', 'Page 1'), ('http://www.google.com', 'Google')]}")
        ```
