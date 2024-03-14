[Download the code](./../src/src.zip){: .tp-btn target='blank' }

The Scenario Page is a part of the application designed for creating and 
customizing prediction scenarios using time series data. End-users can modify different parameters 
for the prediction, such as the prediction date, maximum capacity, 
and the number of predictions. This page also includes a chart displaying historical data 
and predictions generated using both machine learning and baseline methods.

![Scenario Page](images/result.png){ width=90% : .tp-image-border }

The Scenario Page is constructed using a combination of Markdown and Python code. Below is a detailed explanation.

# Markdown

The following Markdown corresponds to the `pages/scenario/scenario.md`file.

```markdown
# Create your scenario:

<|layout|columns=3 1 1 1 1|
<|{scenario}|scenario_selector|>

**Prediction date** <br/>
<|{day}|date|active={scenario}|not with_time|>

**Max capacity** <br/>
<|{max_capacity}|number|active={scenario}|>

**Number of predictions** <br/>
<|{n_predictions}|number|active={scenario}|>

<br/> <|Save|button|on_action=save|active={scenario}|>
|>
 
<|{scenario}|scenario|on_submission_change=submission_change|>

<|{predictions_dataset}|chart|x=Date|y[1]=Historical values|type[1]=bar|y[2]=Predicted values ML|y[3]=Predicted values Baseline|>

# Data Node Exploration

<|layout|columns=1 5|
<|{data_node}|data_node_selector|>

<|{data_node}|data_node|>
|>
```

The Markdown section outlines the arrangement and elements of the Scenario Page. It consists of the following components:

- **Scenario Selector**: `<|{scenario}|scenario_selector|>`

A component (a dropdown) that allows users to select different scenarios. The selected scenario will affect the values of other components on the page. The scenario value is used in other elements so selecting a scenario affects the other elements.

- **Prediction Date**: `<|{day}|date|...|>`

A date picker where users can select the date for which they want to make predictions. The selected date will be used for both machine learning and baseline predictions.

- **Max Capacity**: `<|{max_capacity}|number|...|>`

A number input field where users can set the maximum capacity value. This value is used to cap the predictions if they exceed the specified maximum.

- **Number of Predictions**: `<|{n_predictions}|number|...|>`

A number input field where users can set the desired number of predictions to be made.

- **Save Button**: `<|Save|button|on_action=save|active={scenario}|>`

A button that triggers the "save" action when clicked. It is used to save the selected scenario and parameter values.

- **Scenario Section**: `<|{scenario}|scenario|on_submission_change=submission_change|>`

A section that displays information about the currently selected scenario. It includes details about the scenario, properties, and the ability to delete or submit the scenario. When the scenario status is changed, `submission_change` is called with information on the scenario.

- **Predictions Chart**: `<|{predictions_dataset}|chart|...|>`

A chart that displays historical values and the predicted values obtained from machine learning and baseline methods. It shows how well the predictions align with the historical data.

- **Data Node Exploration**: `<|{data_node}|data_node_selector|> <|{data_node}|data_node|>`

This is where the detailed information and history about the selected data node is presented. Depending on the nature of the data node, this could display raw data in a tabular format, visualizations, texts, or dates. If the format allows it, the user can directly write new values in the data node.


# Python Code

The following Python code corresponds to the `pages/scenario/scenario.py` file. It initializes and manages the state of the Scenario Page.

```python
from taipy.gui import Markdown, notify
import datetime as dt
import pandas as pd


scenario = None
data_node = None
day = dt.datetime(2021, 7, 26)
n_predictions = 40
max_capacity = 200
predictions_dataset = {"Date":[0], 
                       "Predicted values ML":[0],
                       "Predicted values Baseline":[0],
                       "Historical values":[0]}

def submission_change(state, submittable, details: dict):
    if details['submission_status'] == 'COMPLETED':
        notify(state, "success", 'Scenario completed!')
        state['scenario'].on_change(state, 'scenario', state.scenario)
    else:
        notify(state, "error", 'Something went wrong!')

def save(state):
    print("Saving scenario...")
    # Get the currently selected scenario

    # Conversion to the right format
    state_day = dt.datetime(state.day.year, state.day.month, state.day.day)

    # Change the default parameters by writing in the Data Nodes
    state.scenario.day.write(state_day)
    state.scenario.n_predictions.write(int(state.n_predictions))
    state.scenario.max_capacity.write(int(state.max_capacity))
    notify(state, "success", "Saved!")
    

def on_change(state, var_name, var_value):
    if var_name == "scenario" and var_value:
        state.day = state.scenario.day.read()
        state.n_predictions = state.scenario.n_predictions.read()
        state.max_capacity = state.scenario.max_capacity.read()
        
        if state.scenario.full_predictions.is_ready_for_reading:
            state.predictions_dataset = state.scenario.full_predictions.read()
        else:
            state.predictions_dataset = predictions_dataset



scenario_page = Markdown("pages/scenario/scenario.md")
```


It includes the following components:

- **Global Variables**:

The global variables *scenario*, *data_node*, *day*, *n_predictions*, *max_capacity*, and *predictions_dataset* are defined. These variables store the initial state of the application.

- **Save Function**:

The `save` function is used as a callback. It is in charge of preserving the current scenario state.  is in charge of preserving the current scenario state. 
When the user clicks the "Save" button, this function gets activated. 
It receives the page's state as input, converts the date format to the correct one, 
adjusts the scenario parameters accordingly, and then informs the user with a success message.

- **Submission Status Change**

The `submission_change` function is designed to handle feedback when a scenario submission completes. It takes in the current state, the submitted object, and details regarding the submission. If the submission is successful ('*COMPLETED*'), it sends a success notification to the user and triggers an update on the *scenario* object. In the event of a failure, it provides an error notification, alerting the user that something went wrong.

- **On Change Function**:

The `on_change` function is called whenever any variable on the page undergoes a value change. 
It keeps track of alterations in the *scenario* variable and adjusts the other variables accordingly. 
It also verifies if the *full_predictions* are available for reading and updates the *predictions_dataset* accordingly.

- **Scenario Page Initialization**:

The *scenario_page* variable is initialized as a Markdown object, representing the content of the Scenario Page.

It provides an interactive interface for users to create and customize different scenarios for time series predictions. It allows users to select prediction dates, 
set maximum capacity, and choose the number of predictions to make. The page also presents a chart to visualize the historical data and the predicted values from 
both machine learning and baseline methods. Users can save their selected scenarios to use them for further analysis and comparison. 

# Connection to the entire application

Use the `on_change` function created in the *scenario* page; it has to be called in the global `on_change` (main script) of the application. 
This global function is called whenever a variable changes on the user interface. 

In your main script:

```python
def on_change(state, var_name: str, var_value):
    state['scenario'].on_change(state, var_name, var_value)
```