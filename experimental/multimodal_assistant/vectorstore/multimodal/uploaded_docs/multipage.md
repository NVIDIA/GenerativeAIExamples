[Download Step 7](./../src/step_07.zip){: .tp-btn target='blank' }
[Download the entire code](./../src/src.zip){: .tp-btn .tp-btn--accent target='blank' }

!!! warning "For Notebooks"

    The "Getting Started" Notebook is available [here](../tutorial.ipynb). In Taipy GUI,
    the process to execute a Jupyter Notebook is different from executing a Python Script.


Taipy significantly simplifies the process of building a multi-page application. To create a 
multi-page application, you need to define a dictionary of pages. In this example, we will
create three pages: a *root* page and two additional pages (page 1 & page 2). We will incorporate
visual elements, such as a menu or navbar, on the root page to facilitate navigation between
page 1 and page 2.

Note that you can create pages differently using Markdown, Python or HTML. You 
could have one page created with Markdown and another with the Python API.

=== "Markdown"
    ```python
    from taipy import Gui

    # Add a navbar to switch from one page to the other
    root_md = """
    <|navbar|>
    # Multi-page application
    """
    page1_md = "## This is page 1"
    page2_md = "## This is page 2"

    pages = {
        "/": root_md,
        "page1": page1_md,
        "page2": page2_md
    }
    Gui(pages=pages).run()
    ```
=== "Python"
    ```python
    from taipy import Gui
    import taipy.gui.builder as tgb

    # Add a navbar to switch from one page to the other
    with tgb.Page() as root_page:
        tgb.navbar()
        tgb.text("Multi-page application", class_name="h1")

    with tgb.Page() as page_1:
        tgb.text("This is page 1", class_name="h2")
    with tgb.Page() as page_2:
        tgb.text("This is page 1", class_name="h2")

    pages = {
        "/": root_page,
        "page1": page1,
        "page2": page2
    }
    Gui(pages=pages).run()
    ```

## Navigating between pages

- [menu](../../../../manuals/gui/viselements/menu.md): creates a menu on the left to 
navigate through the pages.

=== "Markdown"
    ```
    <|menu|label=Menu|lov={lov_pages}|on_action=on_menu|>`
    ```
=== "Python"
    ```python
    tgb.menu(label="Menu", lov=[...], on_action=on_menu)
    ```

For example, this code creates a menu with two options:

=== "Markdown"
    ```python
    from taipy.gui import Gui, navigate


    root_md="<|menu|label=Menu|lov={[('Page-1', 'Page 1'), ('Page-2', 'Page 2')]}|on_action=on_menu|>"
    page1_md="## This is page 1"
    page2_md="## This is page 2"


    def on_menu(state, action, info):
        page = info["args"][0]
        navigate(state, to=page)


    pages = {
        "/": root_md,
        "Page-1": page1_md,
        "Page-2": page2_md
    }

    Gui(pages=pages).run()
    ```
=== "Python"
    ```python
    from taipy import Gui
    import taipy.gui.builder as tgb


    def on_menu(state, action, info):
        page = info["args"][0]
        navigate(state, to=page)

    # Add a navbar to switch from one page to the other
    with tgb.Page() as root_page:
        tgb.menu(label="Menu", 
                 lov=[('Page-1', 'Page 1'), ('Page-2', 'Page 2')], 
                 on_action=on_menu)

    with tgb.Page() as page_1:
        tgb.text("This is page 1", class_name="h2")
    with tgb.Page() as page_2:
        tgb.text("This is page 1", class_name="h2")

    pages = {
        "/": root_page,
        "page1": page1,
        "page2": page2
    }
    Gui(pages=pages).run()
    ```

![Menu](images/menu.png){ width=40% : .tp-image-border }

- [navbar](../../../../manuals/gui/viselements/navbar.md): creates an element to navigate 
through the Taipy pages by default

=== "Markdown"
    ```python
    from taipy import Gui

    # Add a navbar to switch from one page to the other
    root_md = "<|navbar|>"
    page1_md = "## This is page 1"
    page2_md = "## This is page 2"

    pages = {
        "/": root_md,
        "page1": page1_md,
        "page2": page2_md
    }
    Gui(pages=pages).run()
    ```
=== "Python"
    ```python
    from taipy import Gui
    import taipy.gui.builder as tgb

    # Add a navbar to switch from one page to the other
    with tgb.Page() as root_page:
        tgb.navbar()
        tgb.text("Multi-page application", class_name="h1")

    with tgb.Page() as page_1:
        tgb.text("This is page 1", class_name="h2")
    with tgb.Page() as page_2:
        tgb.text("This is page 1", class_name="h2")

    pages = {
        "/": root_page,
        "page1": page1,
        "page2": page2
    }
    Gui(pages=pages).run()
    ```

![Navbar](images/navbar.png){ width=40% : .tp-image-border }


## Back to the code

The Markdown created in our previous steps will be the first page (named _page_) of the application.

![Previous Markdown](images/first_markdown.png){ width=90% : .tp-image-border }

Then, let’s create our second page, which contains a page to analyze an entire text.

=== "Markdown"
    ```python
    # Second page

    dataframe2 = dataframe.copy()
    path = ""
    treatment = 0

    page_file = """
    <|{path}|file_selector|extensions=.txt|label=Upload .txt file|on_action=analyze_file|> <|Downloading {treatment}%...|>


    <|Table|expandable|
    <|{dataframe2}|table|>
    |>

    <|{dataframe2}|chart|type=bar|x=Text|y[1]=Score Pos|y[2]=Score Neu|y[3]=Score Neg|y[4]=Overall|color[1]=green|color[2]=grey|color[3]=red|type[4]=line|height=800px|>
    """

    def analyze_file(state):
        state.dataframe2 = dataframe2
        state.treatment = 0
        with open(state.path,"r", encoding="utf-8") as f:
            data = f.read()
            # split lines and eliminates duplicates
            file_list = list(dict.fromkeys(data.replace("\n", " ").split(".")[:-1]))


        for i in range(len(file_list)):
            text = file_list[i]
            state.treatment = int((i+1)*100/len(file_list))
            temp = state.dataframe2.copy()
            scores = analyze_text(text)
            temp.loc[len(temp)] = scores
            state.dataframe2 = temp

        state.path = None
    ```
=== "Python"
    ```python
    # Second page

    dataframe2 = dataframe.copy()
    path = ""
    treatment = 0

    def analyze_file(state):
        state.dataframe2 = dataframe2
        state.treatment = 0
        with open(state.path,"r", encoding="utf-8") as f:
            data = f.read()
            # split lines and eliminates duplicates
            file_list = list(dict.fromkeys(data.replace("\n", " ").split(".")[:-1]))


        for i in range(len(file_list)):
            text = file_list[i]
            state.treatment = int((i+1)*100/len(file_list))
            temp = state.dataframe2.copy()
            scores = analyze_text(text)
            temp.loc[len(temp)] = scores
            state.dataframe2 = temp

        state.path = None

    with tgb.Page() as page_file:
        tgb.file_selector("{path}", extensions=".txt", label="Upload .txt file",
                        on_action=analyze_file)
        tgb.text("Downloading {treatment}%...")

        with tgb.expandable("Table"):
            tgb.table("{dataframe2}")

        tgb.chart("{dataframe2}", type="bar", x="Text",
                y__1="Score Pos", y__2="Score Neu",  y__3="Score Neg", y__4="Overall",
                color__1="green", color__2="grey", color__3="red", type__4="line",
                height="800px")
    ```


This little code below assembles our previous page and this new page. The `navbar` in the root
page is also visible on both pages allowing for easy switching between pages.

```python
# One root page for common content
# The two pages that were created
pages = {"/":"<|toggle|theme|>\n<center>\n<|navbar|>\n</center>",
         "line":page,
         "text":page_file}

Gui(pages=pages).run()
```

![Multi-Pages](images/result.png){ width=90% : .tp-image-border }
