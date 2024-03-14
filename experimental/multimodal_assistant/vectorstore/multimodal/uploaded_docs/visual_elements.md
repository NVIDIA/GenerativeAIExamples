[Download Step 2](./../src/step_02.zip){: .tp-btn target='blank' }
[Download the entire code](./../src/src.zip){: .tp-btn .tp-btn--accent target='blank' }

!!! warning "For Notebooks"

    The Notebook is available [here](../tutorial.ipynb). In Taipy GUI,
    the process to execute a Jupyter Notebook is different from executing a Python Script.


You can incorporate various visual elements into the basic code demonstrated in Step 1. In this
step, we will illustrate how to utilize visual elements such as charts, sliders, tables, and
more within the graphical interface.

## Visual elements

When using the Mardown syntax, Taipy augments it with the concept of
**[visual elements](../../../../manuals/gui/viselements/index.md)**. A visual element is a
Taipy graphical object displayed on the client. It can be a
[slider](../../../../manuals/gui/viselements/slider.md), a
[chart](../../../../manuals/gui/viselements/chart.md), a
[table](../../../../manuals/gui/viselements/table.md), an
[input](../../../../manuals/gui/viselements/input.md), a
[menu](../../../../manuals/gui/viselements/menu.md), etc. Check the list
[here](../../../../manuals/gui/viselements/controls.md).

Every visual element follows a similar syntax:

=== "Markdown"
    ```
    <|{variable}|visual_element_name|param_1=param_1|param_2=param_2| ... |>
    ``` 
=== "Python"
    ```python
    tgb.visual_element_name("{variable}", param_1=param_1, param_2=param_2, ...)
    ``` 
    
    The inclusion of *variable* within `"{...}"` tells Taipy to show and use the 
    real-time value of *variable*. Rather than re-executing the entire script, 
    Taipy intelligently adjusts only the necessary elements of the GUI to reflect 
    changes, ensuring a responsive and performance-optimized user experience.

For example, a [slider](../../../../manuals/gui/viselements/slider.md) is written this way :


=== "Markdown"
    ```
    <|{variable}|slider|min=min_value|max=max_value|>
    ``` 
=== "Python"
    ```python
    tgb.slider("{variable}", min=min_value, max=max_value, ...)
    ``` 

To include each visual element you want in your web page, you should incorporate the syntax
mentioned above within your markdown string, which represents your page.
For example, at the beginning of the page, if you want to display:

- a Python variable *text*

- an input that will "visually" modify the value of __text__.

Here is the overall syntax:

=== "Markdown"
    ```
    <|{text}|>
    <|{text}|input|>
    ```
=== "Python"
    ```python
    tgb.text("{text}")
    tgb.input("{text}")
    ``` 


Here is the combined code:

=== "Markdown"
    ```python
    from taipy.gui import Gui

    text = "Original text"

    page = """
    # Getting started with Taipy GUI

    My text: <|{text}|>

    <|{text}|input|>
    """

    Gui(page).run(debug=True)
    ```
=== "Python"
    ```python
    from taipy.gui import Gui
    import taipy.gui.builder as tgb

    text = "Original text"

    with tgb.Page() as page:
        tgb.text("Getting started with Taipy GUI", class_name="h1")
        tgb.text("My text: {text}")

        tgb.input("{text}")

    Gui(page).run(debug=True)
    ```

![Visual Elements](images/result.png){ width=90% : .tp-image-border }
