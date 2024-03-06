[Download Step 1](./../src/step_01.zip){: .tp-btn target='blank' }
[Download the entire code](./../src/src.zip){: .tp-btn .tp-btn--accent target='blank' }

!!! warning "For Notebooks"

    The Notebook is available [here](../tutorial.ipynb). In Taipy GUI,
    the process to execute a Jupyter Notebook is different from executing a Python Script.


You only need one line of code to create your first Taipy web page. Just create a `Gui^` object
with a string and run it.

In the console, you'll find a client link. All you need to do is copy and paste it into your web
browser to open your first Taipy page!


```python
from taipy import Gui

Gui(page="# Getting started with *Taipy*").run(debug=True) # use_reloader=True
```

The run method accepts different useful parameters:

- _debug_: instructs Taipy to operate in debug mode. This means Taipy will provide a 
stack trace of the errors within the application—a valuable feature during 
development.

![Debug mode](images/debug_mode.png){ width=80% : .tp-image-border }

- _use_reloader_: By default, the page won't refresh on its own after you make a code 
modification. If you want to alter this behavior, you can set the *use_reloader* to 
True. The application will automatically reload when you make changes to a file in 
your application and save it.

- _port_: If you wish to run multiple servers concurrently, you can modify the server 
port number (5000 by default).

Other parameters of the `run()` method can be found
[here](../../../../manuals/gui/configuration.md#configuring-the-gui-instance).


Keep in mind that you have the option to format your text. Taipy uses different ways to create
pages: [Markdown](../../../../manuals/gui/pages/index.md#using-markdown),
[HTML](../../../../manuals/gui/pages/index.md#using-html) or
[Python code](../../../../manuals/gui/pages/builder.md). Here is the Markdown syntax to style your
text  and more. Therefore, `#` creates a title, `##` makes a subtitle. Put your text in `*` for
*italics* or in `**` to have it in **bold**.


![First Web Page](images/result.png){ width=90% : .tp-image-border }
