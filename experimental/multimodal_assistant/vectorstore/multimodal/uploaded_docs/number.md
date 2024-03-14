---
title: <tt>number</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A kind of [`input`](input.md) that handles numbers.

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
<td><p>The numerical value represented by this control.</p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code></td>
<td nowrap>None</td>
<td><p>The label associated with the input.</p></td>
</tr>
<tr>
<td nowrap><code id="p-change_delay">change_delay</code></td>
<td><code>int</code></td>
<td nowrap><i>App config</i></td>
<td><p>Minimum time between triggering two calls to the <i>on_change</i> callback.<br/>The default value is defined at the application configuration level by the <strong>change_delay</strong> configuration option. if None, the delay is set to 300 ms.<br/>If set to -1, the input change is triggered only when the user presses the Enter key.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>Name of a function that is triggered when a specific key is pressed.<br/>The parameters of that function are all optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (str): the identifier of the input.</li>
<li>payload (dict): the details on this callback's invocation.<br/>
This dictionary has the following keys:
<ul>
<li>action: the name of the action that triggered this callback.</li>
<li>args (list):
<ul><li>key name</li><li>variable name</li><li>current value</li></ul>
</li>
</ul>
</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-action_keys">action_keys</code></td>
<td><code>str</code></td>
<td nowrap>"Enter"</td>
<td><p>Semicolon (';')-separated list of supported key names.<br/>Authorized values are Enter, Escape, F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12.</p></td>
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

All the number controls are generated with the "taipy-number" CSS class. You can use this class
name to select the number controls on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides a specific class that you can use to style number controls:

* *fullwidth*<br/>
    If a number control uses the *fullwidth* class, then it uses the whole available
    horizontal space.

# Usage

## Simple

You can create a `number` input field bound to a numerical variable with the following content:

!!! example "Definition"

    === "Markdown"

        ```
        <|{value}|number|>
        ```

    === "HTML"

        ```html
        <taipy:number>{value}</taipy:number>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.number("{value}")
        ```
