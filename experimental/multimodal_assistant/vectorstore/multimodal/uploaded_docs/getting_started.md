---
title: Getting Started with Taipy
hide:
  - navigation
---

Dive into Taipy with this beginner-friendly guide. Learn to install, configure, and create your
first application with ease.

![Dynamic Chart Application](images/result.png){width=80% : .tp-image-border }

# Installation with pip

1. **Prerequisites**: Ensure you have Python (**version 3.8 or later**) and
    [pip](https://pip.pypa.io) installed.

2. **Installation Command**: Run the following in your terminal or command prompt:
    ``` console
    pip install taipy
    ```

For alternative installation methods or if you're lacking Python or pip, refer to the
[installation page](../installation/index.md).

# Build a graphical interface

In this section, you'll create an application that includes a slider to adjust a 
parameter, which in turn affects a data visualization chart. This example 
demonstrates how Taipy can be used to create interactive and dynamic web 
applications.

!!! example "GUI creation"

    === "Markdown"

        Taipy pages can be defined in multiple ways: Markdown, Html or Python. *page* is the Markdown representation of the page.

        ```python linenums="1"
        from taipy.gui import Gui
        from math import cos, exp

        value = 10

        page = """
        # Taipy *Getting Started*

        Value: <|{value}|text|>

        <|{value}|slider|on_change=on_slider|>

        <|{data}|chart|>
        """

        def on_slider(state):
            state.data = compute_data(state.value)

        def compute_data(decay:int)->list:
            return [cos(i/6) * exp(-i*decay/600) for i in range(100)]

        data = compute_data(value)

        if __name__ == "__main__":
            Gui(page).run(title="Dynamic chart")
        ```

    === "Python"

        Taipy pages can be defined in multiple ways: Markdown, Html or Python. *page* is built through
        the Page Builder API.

        ```python linenums="1"
        from taipy.gui import Gui 
        import taipy.gui.builder as tgb
        from math import cos, exp

        value = 10

        def compute_data(decay:int)->list:
            return [cos(i/6) * exp(-i*decay/600) for i in range(100)]

        def on_slider(state):
            state.data = compute_data(state.value)

        with tgb.Page() as page:
            tgb.text(value="Taipy Getting Started", class_name="h1")
            tgb.text(value="Value: {value}")
            tgb.slider(value="{value}", on_change=on_slider)
            tgb.chart(data="{data}") 

        data = compute_data(value)

        if __name__ == "__main__":
            Gui(page=page).run(title="Dynamic chart")
        ```

Now, let’s explain the key elements of this code:

**Visual elements**

Taipy offers various visual elements that can interact with your Python variables and
environment. It allows you to display variables, modify them, and interact with the application.

Here is a generic example of one: `<|{variable}|visual_element_type|...|>` with Markdown or
`tgb.visual_element_type("{variable}", ...)` with the Python API. *variable* is
the main property of the visual element and is usually what is displayed or modified through the
visual element.

In our initial example:

- *value* is bound to a slider and a text, allowing the user’s input to be directly 
stored in the *value* variable.
- *data* is created through in *compute_data()* function and is updated depending on the  
slider's value. It is represented in the application as a chart.


## Interactivity Through Actions

Actions, like `on_change=on_slider`, allow visual elements like slider or input 
to trigger specific functions.

```python
def on_slider(state):
    state.data = compute_data(state.value)
```

Every callback, including *on_slider()*, receives a `State^` object as its first parameter.
This state represents a user's connection and is used to read and set variables while
the user is interacting with the application. It makes it possible for Taipy to handle multiple
users simultaneously.

*state.value* is specific to the user who interacts with the application. 
This design ensures that each user's actions are separate and efficiently 
controlled, while other variables could be global variables.

![State illustration](images/state_illustration.png){width=70% : .tp-image-border }

In the *on_slider()* function, the *value* selected by the user on the interface is
propagated to the *data* variable. The outcome is then used to update the chart.

```python
if __name__ == "__main__":
    Gui(page=page).run(title="Dynamic chart")
```

This code starts the UI server, which makes the interface active and functional.

![Dynamic Chart Application](images/dynamic_chart.gif){width=70% : .tp-image-border }

---

For more realistic and advanced use cases, check out our
[Gallery](../gallery/index.md), or [Manuals](../manuals/index.md) pages.

<div class="tp-row tp-row--gutter-sm">
  <div class="tp-col-12 tp-col-md-4 d-flex">
    <a class="tp-content-card tp-content-card--primary" href="../tutorials/fundamentals/1_understanding_gui/">
      <header class="tp-content-card-header">
        <img class="tp-content-card-icon--small" src="images/visualize.svg">
        <h3>Understanding GUI</h3>
      </header>
      <div class="tp-content-card-body">
        <p>
          Get the core concepts on how to create a Taipy application.
        </p>
      </div>
    </a>
  </div>

  <div class="tp-col-12 tp-col-md-4 d-flex">
    <a class="tp-content-card tp-content-card--alpha" href="../tutorials/fundamentals/2_scenario_management_overview/">
      <header class="tp-content-card-header">
        <img class="tp-content-card-icon--small" src="images/scenario.svg">
        <h3>Manage Data and Scenarios</h3>
      </header>
      <div class="tp-content-card-body">
        <p>
          Uncover strategies for effective scenario and data management.
        </p>
      </div>
    </a>
  </div>

  <div class="tp-col-12 tp-col-md-4 d-flex">
    <a class="tp-content-card tp-content-card--beta" href="../tutorials">
      <header class="tp-content-card-header">
        <img class="tp-content-card-icon--small" src="images/icon-tutorials.svg">
        <h3>Tutorials</h3>
      </header>
      <div class="tp-content-card-body">
        <p>
          Follow tutorials to take your Taipy applications further.
        </p>
      </div>
    </a>
  </div>
</div>
