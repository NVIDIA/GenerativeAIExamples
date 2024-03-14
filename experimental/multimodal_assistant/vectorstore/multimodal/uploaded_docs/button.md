---
title: <tt>button</tt>
hide:
  - navigation
---

<!-- Category: controls -->
A control that can trigger a function when pressed.

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
<td nowrap><code id="p-label"><u><bold>label</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>str|Icon</code><br/><i>dynamic</i></td>
<td nowrap>""</td>
<td><p>The label displayed in the button.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the button is pressed.<br/>The parameters of that function are all optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (optional[str]): the identifier of the button.</li>
<li>payload (dict): a dictionary that contains the key "action" set to the name of the action that triggered this callback.</li>
</ul></p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-label" title="Jump to the default property documentation."><code>label</code></a> is the default property for this visual element.</p>

# Styling

All the button controls are generated with the "taipy-button" CSS class. You can use this class
name to select the buttons on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides specific classes that you can use to style buttons:

* *secondary*<br/>*error*<br/>*warning*<br/>*success*<br/>
    Buttons are normally displayed using the value of the *color_primary* Stylekit variable.
    These classes can be used to change the color used to draw the button, respectively, with
    the *color_secondary*, *color_error*, *color_warning* and *color_success* Stylekit variable
    values.

    The Markdown content: 
    ```
    <|Error|button|class_name=error|><|Secondary|button|class_name=secondary|>
    ```

    Renders like this:
    <figure>
      <img src="../button-stylekit_color-d.png" class="visible-dark" />
      <img src="../button-stylekit_color-l.png" class="visible-light"/>
      <figcaption>Using color classes</figcaption>
    </figure>

* *plain*<br/>
    The button is filled with a plain color rather than just outlined.

    The Markdown content: 
    ```
    <|Button 1|button|><|Button 2|button|class_name=plain|>
    ```

    Renders like this:
    <figure>
        <img src="../button-stylekit_plain-d.png" class="visible-dark" />
        <img src="../button-stylekit_plain-l.png" class="visible-light"/>
        <figcaption>Using the <code>plain</code> class</figcaption>
    </figure>

* *fullwidth*: The button is rendered on its own line and expands across the entire available
  width.

# Usage

## Simple button

The button label, which is the button control's default property, is simply displayed as the button
text.

!!! example "Definition"

    === "Markdown"

        ```
        <|Button Label|button|>
        ```

    === "HTML"

        ```html
        <taipy:button>Button Label</taipy:button>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.button("Button Label")
        ```

<figure>
    <img src="../button-simple-d.png" class="visible-dark" />
    <img src="../button-simple-l.png" class="visible-light"/>
    <figcaption>A simple button</figcaption>
</figure>

## Specific action callback

Button can specify a callback function to be invoked when the button is pressed.

If you want some function called *button_pressed()* to be invoked when the user presses a button,
you can define this function as follows:
```py
def button_pressed(state):
  # React to the button press action
```

Then refer to this function in the definition of the control, as the value of the button's
[*on_action*](#p-on_action) property:

!!! example "Definition"

    === "Markdown"

        ```
        <|Button Label|button|on_action=button_pressed|>
        ```

    === "HTML"

        ```html
        <taipy:button on_action="button_pressed">Button Label</taipy:button>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.button("Button Label", on_action=button_pressed)
        ```
