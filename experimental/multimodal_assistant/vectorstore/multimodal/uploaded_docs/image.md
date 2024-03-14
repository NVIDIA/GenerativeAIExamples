---
title: <tt>image</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A control that can display an image.

!!! note "Image format"
    Note that if the content is provided as a buffer of bytes, it can be converted
    to an image content if and only if you have installed the
    [`python-magic`](https://pypi.org/project/python-magic/) Python package (as well
    as [`python-magic-bin`](https://pypi.org/project/python-magic-bin/) if your
    platform is Windows).

You can indicate a function to be called when the user clicks on the image.

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
<td nowrap><code id="p-content"><u><bold>content</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>path|URL|file|ReadableBuffer</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The image source.<br/>If a buffer is provided (string, array of bytes...), and in order to prevent the bandwidth to be consumed too much, the way the image data is transferred depends on the <i>data_url_max_size</i> parameter of the application configuration (which is set to 50kB by default):
<ul>
<li>If the size of the buffer is smaller than this setting, then the raw content is generated as a
  data URL, encoded using base64 (i.e. <code>"data:&lt;mimetype&gt;;base64,&lt;data&gt;"</code>).</li>
<li>If the size of the buffer is greater than this setting, then it is transferred through a temporary
  file.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The label for this image.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the user clicks on the image.<br/>All the parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (optional[str]): the identifier of the button.</li>
<li>payload (dict): a dictionary that contains the key "action" set to the name of the action that triggered this callback.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-width">width</code></td>
<td><code>str|int|float</code></td>
<td nowrap>"300px"</td>
<td><p>The width, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str|int|float</code></td>
<td nowrap></td>
<td><p>The height, in CSS units, of this element.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-content" title="Jump to the default property documentation."><code>content</code></a> is the default property for this visual element.</p>

# Styling

All the image controls are generated with the "taipy-image" CSS class. You can use this class
name to select the image controls on your page and apply style.

The [Stylekit](../styling/stylekit.md) also provides a specific CSS class that you can use to style
images:

- *inline*<br/>
  Displays an image as inline and vertically centered. It would otherwise be displayed as a block.
  This can be relevant when dealing with SVG images.

# Usage

## Default behavior

Shows an image specified as a local file path or as raw content.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|image|>
        ```

    === "HTML"

        ```html
        <taipy:image>{content}</taipy:image>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.image("{content}")
        ```

## Call a function on click

The [*label*](#p-label) property can be set to a label shown over the image.<br/>
The function provided in the [*on_action*](#p-on_action) property is called when the image is
clicked (like with a button).

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|image|label=This is an image|on_action=function_name|>
        ```

    === "HTML"

        ```html
        <taipy:image label="This is an image" on_action="function_name">{content}</taipy:image>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.image("{content}", label="This is an image", on_action=function_name)
        ```
