---
title: <tt>file_selector</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Allows uploading a file content.

The upload can be triggered by pressing a button, or drag-and-dropping a file on top of the control.

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
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The path or the list of paths of the uploaded files.</p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The label of the button.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of the function that will be triggered.<br/>All the parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (optional[str]): the identifier of the button.</li>
<li>payload (dict): a dictionary that contains the key "action" set to the name of the action that triggered this callback.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-multiple">multiple</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If set to True, multiple files can be uploaded.</p></td>
</tr>
<tr>
<td nowrap><code id="p-extensions">extensions</code></td>
<td><code>str</code></td>
<td nowrap>".csv,.xlsx"</td>
<td><p>The list of file extensions that can be uploaded.</p></td>
</tr>
<tr>
<td nowrap><code id="p-drop_message">drop_message</code></td>
<td><code>str</code></td>
<td nowrap>"Drop here to Upload"</td>
<td><p>The message that is displayed when the user drags a file above the button.</p></td>
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

All the file selector controls are generated with the "taipy-file_selector" CSS class. You can use this class
name to select the file selector controls on your page and apply style.

# Usage

## Default behavior

The variable specified in _content_ is populated by a local filename when the transfer is completed.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_selector|>
        ```

    === "HTML"

        ```html
        <taipy:file_selector>{content}</taipy:file_selector>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_selector("{content}")
        ```

## Standard configuration

The [*label*](#p-label) property can be set to a label shown besides the standard icon.<br/>
The function name provided as [*on_action*](#p-on_action) is called when the transfer is
completed.<br/>
The [*extensions*](#p-extensions) property can be used as a list of file name extensions that is
used to filter the file selection box. This filter is not enforced: the user can select and upload
any file.<br/>
Upon dragging a file over the button, the value of the [*drop_message*](#p-drop_message) property
is displayed as a temporary label for the button.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_selector|label=Select File|on_action=function_name|extensions=.csv,.xlsx|drop_message=Drop Message|>
        ```

    === "HTML"

        ```html
        <taipy:file_selector label="Select File" on_action="function_name" extensions=".csv,.xlsx" drop_message="Drop Message">{content}</taipy:file_selector>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_selector("{content}", label="Select File", on_action=function_name, extensions=".csv,.xlsx", drop_message="Drop Message")
        ```

## Multiple files upload

The user can transfer multiple files at once by setting the [*multiple*](#p-multiple) property to
True.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_selector|multiple|>
        ```

    === "HTML"

        ```html
        <taipy:file_selector multiple>{content}</taipy:file_selector>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_selector("{content}", multiple=True)
        ```
