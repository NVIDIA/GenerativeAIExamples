---
title: <tt>file_download</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Allows downloading of a file content.

The content to be sent to the user's browser can be a file, a URL, or any data stored as
a buffer of bytes.<br/>
The content can be dynamically generated when the user requests it.

!!! note "Image format"
    Note that if the content is provided as a buffer of bytes, it can be converted
    to image content if and only if you have installed the
    [`python-magic`](https://pypi.org/project/python-magic/) Python package (as well
    as [`python-magic-bin`](https://pypi.org/project/python-magic-bin/) if your
    platform is Windows).
    
The download can be triggered when clicking on a button or can be performed automatically (see the
[*auto* property](#p-auto)).

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
<td><code>path|file|URL|ReadableBuffer|None</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The content to transfer.<br/>If this is a string, a URL, or a file, then the content is read from this source.<br/>If a readable buffer is provided (such as an array of bytes...), and to prevent the bandwidth from being consumed too much, the way the data is transferred depends on the <i>data_url_max_size</i> parameter of the application configuration (which is set to 50kB by default):
<ul>
<li>If the buffer size is smaller than this setting, then the raw content is generated as a data URL, encoded using base64 (i.e. <code>"data:&lt;mimetype&gt;;base64,&lt;data&gt;"</code>).</li>
<li>If the buffer size exceeds this setting, then it is transferred through a temporary file.</li>
</ul>If this property is set to None, that indicates that dynamic content is generated. Please take a look at the examples below for details on dynamic generation.</p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The label of the button.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_action">on_action</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the download is terminated (or on user action if <i>content</i> is None).<br/>All the parameters of that function are optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (optional[str]): the identifier of the button.</li>
<li>payload (dict): the details on this callback's invocation.<br/>
This dictionary has two keys:
<ul>
<li>action: the name of the action that triggered this callback.</li>
<li>args: A list of two elements: <i>args[0]</i> reflects the <i>name</i> property and <i>args[1]</i> holds the file URL.</li>
</ul>
</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-auto">auto</code></td>
<td><code>bool</code></td>
<td nowrap>False</td>
<td><p>If True, the download starts as soon as the page is loaded.</p></td>
</tr>
<tr>
<td nowrap><code id="p-render">render</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>If True, the control is displayed.<br/>If False, the control is not displayed.</p></td>
</tr>
<tr>
<td nowrap><code id="p-bypass_preview">bypass_preview</code></td>
<td><code>bool</code></td>
<td nowrap>True</td>
<td><p>If False, allows the browser to try to show the content in a different tab.<br/>The file download is always performed.</p></td>
</tr>
<tr>
<td nowrap><code id="p-name">name</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>A name proposition for the file to save, that the user can change.</p></td>
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

All the file download controls are generated with the "taipy-file_download" CSS class. You can use this class
name to select the file download controls on your page and apply style.

# Usage

## Default behavior

Allows downloading *content* when content is a file path or some content.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_download|>
        ```

    === "HTML"

        ```html
        <taipy:file_download>{content}</taipy:file_download>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_download("{content}")
        ```

## Standard configuration

The [*label*](#p-label) property can be set to specify the label used as the button text next to
the download icon.

The function name provided as [*on_action*](#p-on_action) is called when the download is done
(except if [*content*](#p-content) was set to None, as show in the *dynamic content* examples below).

The [*name*](#p-name) property is used as the default file name proposed to the user when
saving the downloaded file (depending on the browser validation rules).

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_download|label=Download File|on_action=function_name|name=filename|>
        ```

    === "HTML"

        ```html
        <taipy:file_download label="Download File" on_action="function_name" name="filename">{content}</taipy:file_download>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_download("{content}", label="Download File", on_action=function_name, name="filename")
        ```

## Preview file in the browser

The file content can be visualized in the browser (if supported and in another tab) by setting
[*bypass_preview*](#p-bypass_preview) to False.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_download|don't bypass_preview|>
        ```

    === "HTML"

        ```html
        <taipy:file_download bypass_preview="false">{content}</taipy:file_download>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_download("{content}", bypass_preview=False)
        ```

## Automatic download

The file content can be downloaded automatically (when the page shows and when the content is set)
when [*auto*](#p-auto) is set to True.

!!! example "Definition"

    === "Markdown"

        ```
        <|{content}|file_download|auto|>
        ```

    === "HTML"

        ```html
        <taipy:file_download auto>{content}</taipy:file_download>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_download("{content}", auto=True)
        ```

## Dynamic content {data-source="gui:doc/examples/controls/file_download-dynamic.py"}

There are situations when the content to be downloaded cannot or should not be ready before the
user presses the download button.<br/>
This happens, for example, if some data generation process needs to query live data or if this
process takes a lot of time and depends on user-defined parameters. In this situation, you may not
want to spend time and resources generating data that may not be used after all.

The property [*content*](#p-content) of the `file_download` control can be set to None to handle
these circumstances. In this case, the [*on_action*](#p-on_action) callback is invoked immediately
after the user has pressed the download button and is in charge of generating the data then
triggering the download operation.

Here is an example of such a situation: an algorithm can generate the digits of the number Pi with
a requested number of digits.<br/>
A [`slider` control](slider.md) lets the user interactively pick the desired precision and a
`file_download` control allows to download a CSV file that contains all the generated digits.<br/>
Generating  all those digits every time the user moves the slider knob would waste CPU time.
We really want to generate the data only when the user presses the download button.

Here is some code that achieves that:
```py
# Initial precision
precision = 10

def pi(precision: int) -> list[int]:
    """Compute Pi to the required precision.

    Adapted from https://docs.python.org/3/library/decimal.html
    """
    saved_precision = getcontext().prec # Save precision
    getcontext().prec = precision
    three = Decimal(3)      # substitute "three=3.0" for regular floats
    lasts, t, s, n, na, d, da = 0, three, 3, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n+na, na+8
        d, da = d+da, da+32
        t = (t * n) / d
        s += t
    digits = []
    while s != 0:
        integral = int(s)
        digits.append(integral)
        s = (s - integral) * 10
    getcontext().prec = saved_precision
    return digits

# Generate the digits, save them in a CSV file content, and trigger a download action
# so the user can retrieve them
def download_pi(state):
    digits = pi(state.precision)
    buffer = io.StringIO()
    buffer.write("index,digit\n")
    for i, d in enumerate(digits):
        buffer.write(f"{i},{d}\n")
    download(state, content=bytes(buffer.getvalue(), "UTF-8"), name="pi.csv")

```

The variable *precision* is bound to a slider on the page: its value is updated (in the
user's `State^`), and there is no callback triggered when the slider knob moves. Only the
state variable is updated for later use.

The function *download_pi()* is invoked as the [*on_action*](#p-on_action) callback for the
`file_download` control, that has its [*content*](#p-content) property set to None. As a result,
when the user presses the download button, *download_pi()* gets immediately invoked so the data
can be generated. The data can be downloaded to the user's browser using an explicit call to the
function `download()^`, where we convert the string content to a byte buffer using the `bytes()`
function.

The control definition looks like this:

!!! example "Definition"

    === "Markdown"

        ```
        <|{None}|file_download|on_action=download_pi|>
        ```

    === "HTML"

        ```html
        <taipy:file_download on_action="download_pi">{None}</taipy:file_download>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.file_download("{None}", on_action=download_pi)
        ```

## Content in a temporary file {data-source="gui:doc/examples/controls/file_download-dynamic-temp-file.py"}

In the previous example, we could generate and store all our data in a buffer and then send it so
Taipy would create a data URL to handle the transfer.<br/>
There are situations where this is not possible or inefficient. Then, a temporary file must be
created.<br/>
But then, after the transfer is performed, we want to remove that file from the server filesystem
since it is no longer needed.

To achieve that, we can use the *on_action* parameter of the function `download()^`: it gets
invoked when the transfer is done, so you can perform any task that should be executed after the
file transfer.

Here is some code that demonstrates this. It is a slightly modified version of the example
above, where instead of creating a `io.StringIO` buffer to hold the data, we create a
temporary file where we write everything.<br/>
The data generation function (*pi()*) and the control definition remain the same.<br/>
Here are the changes to the code compared to the example above:
```py
# Stores the path to the temporary file
temp_path = None

# Remove the temporary file
def clean_up(state):
    os.remove(state.temp_path)

# Generate the digits, save them in a CSV temporary file, then trigger a download action
# for that file.
def download_pi(state):
    digits = pi(state.precision)
    with NamedTemporaryFile("r+t", suffix=".csv", delete=False) as temp_file:
        state.temp_path = temp_file.name
        temp_file.write("index,digit\n")
        for i, d in enumerate(digits):
            temp_file.write(f"{i},{d}\n")
    download(state, content=temp_file.name, name="pi.csv", on_action=clean_up)
```

In the new implementation of *download_pi()*, we create a temporary file to write the data we
want to send.<br/>
The path to this file is saved in the *state* object. This is made possible because the variable
*temp_path* was declared so that *state* knows about it.<br/>
The call to `download()^` now sets the content to be transferred to the temporary file path and
sets the *on_action* parameter that indicates that, when the file transfer is performed, the
function *clean_up()* should be called.<br/>
In *clean_up()*, we simply delete the temporary file, retrieving its path name from the provided
*state*.
