---
hide:
  - navigation
---

# Gantt charts

Although Plotly does not have Gantt chart-specific features, there are ways to display horizontal bar charts with different starting points that can look like a Gantt chart.

Therefore, the basis for creating a chart control representing a Gantt chart, you must
set the [*type*](../chart.md#p-type) property of the control to "bar" and set the
[*orientation*](../chart.md#p-orientation) property to "h".

In a Gantt chart, you have two inescapable traits:

- the *x* axis represents the time.
- the *y* axis holds a list of tasks that are scheduled or a list
    of resources that are assigned different tasks along the time.

Gantt charts are based on a timeline. Working with the Plotly bar charts using
dates and times as an axis value is pretty tricky and needs explanations:

- Every bar represents a time span for a given activity.
- Setting its *y* location is straightforward: the *y* value for that bar is the name of
    the task or the resource it is assigned to.
- Each bar needs two values, indicating when an activity starts and ends. This
    is where things are a bit more complicated:
    - The *base* value for each bar must be set to the date when the activity starts.
    - The *x* value for each bar must be set to a `datetime` value representing
        the duration of the activity relative to January 1st, 1970.

To summarize: if you have a task "T" planned between &lt;date1&gt; and &lt;date2&gt;,
you will have to provide the chart control with:

- *base* = &lt;date1&gt;
- *y* = T
- *x* = date(January 1st, 1970)+&lt;date2&gt;-&lt;date1&gt;

The first example below illustrates this.

By default, the text displayed when hovering over a bar is the contents
of the *base* property. So, in the above situation, the tooltip
would display the start date of a bar you hover over.<br/>
If you need to display the *end* date instead, this is what you need to do:

- The *base* value for each bar must be set to the date when the activity **ends**.
- You must use *negative* time spans: the *x* values would be the duration of the
    activities, **subtracted** from the Unix epoch, January 1st, 1970.<br/>
    I.e.: *x* = date(January 1st, 1970)-&lt;date2&gt;+&lt;date1&gt;

## Key properties

| Name            | Value           | Notes   |
| --------------- | ------------------------- | ------------------ |
| [*type*](../chart.md#p-type)      | `bar`  |  |
| [*x*](../chart.md#p-x)      | series of `datetime`  | The duration of the activities expressed relative to the Unix epoch (January 1st, 1970). See above for details.  |
| [*y*](../chart.md#p-x)      |   | The tasks or the resources.  |
| [*orientation*](../chart.md#p-orientation)      | `h`  | The main axis for Gantt charts is the horizontal axis.  |
| [*base*](../chart.md#p-base)      | series of `datetime`  | The start dates of the activities (or end dates if you use negative time spans).  |

## Examples

### Simple Gantt chart {data-source="gui:doc/examples/charts/gantt-simple.py"}

Here is a simple example of using the chart control to display a Gantt chart.

We want to display, over time, the span of several tasks.

Here is the code that we use:
```python
# Tasks definitions
tasks = ["Plan", "Research", "Design", "Implement", "Test", "Deliver"]
# Task durations, in days
durations = [50, 30, 30, 40, 15, 10]
# Planned start dates of tasks
start_dates = [
    datetime.date(2022, 10, 15), # Plan
    datetime.date(2022, 11,  7), # Research
    datetime.date(2022, 12,  1), # Design
    datetime.date(2022, 12, 20), # Implement
    datetime.date(2023,  1, 15), # Test
    datetime.date(2023,  2,  1)  # Deliver
]

epoch = datetime.date(1970, 1, 1)

data = {
    "start": start_dates,
    "Task": tasks,
    # Compute the time span as a datetime (relative to January 1st, 1970)
    "Date": [epoch+datetime.timedelta(days=d) for d in durations]
}

layout = {
    "yaxis": {
        # Sort tasks from top to bottom
        "autorange": "reversed",
        # Remove title
        "title": {"text": ""}
    },
}
```

The *start* column of the data set should be used as the data source for the
[*base*](../chart.md#p-base) property of the chart control.

The *Date* column (named as such so it appears nicely under the x axis) of *data*
is set to the list of all tasks' duration as a `datetime` object relative to
the Unix epoch: January 1st, 1970.<br/>
This column should be used to set the data source for the control's
[*x*](../chart.md#p-x) property.

Also notice the *layout* object: this is used to make the Gantt chart slightly nicer. In
particular, the ordering of the tasks is reversed; otherwise, the first task would appear
at the bottom of the chart.

Here is how we defined the chart control:
!!! example "Definition"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|orientation=h|y=Task|x=Date|base=start|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="bar" orientation="h" y="Task" x="Date" base="start" layout="{layout}">{data}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{data}", type="bar", orientation="h", y="Task", x="Date", base="start", layout="{layout}")
        ```

The resulting Gantt chart looks like this:
<figure>
    <img src="../gantt-simple-d.png" class="visible-dark" />
    <img src="../gantt-simple-l.png" class="visible-light"/>
    <figcaption>Simple Gantt chart</figcaption>
</figure>

<!--
### Simple Gantt chart

Different resources are displayed by different traces in the same chart.

Here is an example where we represent two resources' tasks, based on the same
_x_ timeline axis:

- The tasks start dates are represented by the _base_ values on the _x_ axis (type is date or datetime ).
- The tasks durations are represented by the _x_ values on the _x_ axis (type is date or datetime). 
  The _x_ values are specified as a time duration i.e. a date where 0 is January 1st 1970 i.e. `date(1970, 1, 1)`. for example to specify a duration of 2 days, one would set the value to date(1970, 1, 3)
- The resources names are represented by the _y_ values. To keep the tasks on the same horizontal line, the _y_ value should be the same.
- The tasks names can by specified by the _text_ or _label_ property.

```py
data = pd.DataFrame({
  "x": [dt.date(1970, 1, 20), dt.date(1970, 1, 10), dt.date(1970, 1, 5)],
  "y": ["Resource 1", "Resource 1", "Resource 1"],
  "label": ["Task 1.1", "Task 1.2", "Task 1.3"],
  "base": [dt.date(2022, 1, 1), dt.date(2022, 2, 1), dt.date(2022, 3, 1)],

  "x1": [dt.date(1970, 1, 3), dt.date(1970, 1, 15), dt.date(1970, 1, 5)],
  "y1": ["Resource 2", "Resource 2", "Resource 2"],
  "base1": [dt.date(2022, 1, 15), dt.date(2022, 2, 1), dt.date(2022, 3, 10)],
  "label1": ["Task 2.1", "Task 2.2", "Task 2.3"]
})
```

The chart definition looks like this:

!!! example "Page content"

    === "Markdown"

        ```
        <|{data}|chart|type=bar|orientation=h|x[1]=x|y[1]=y|base[1]=base|text[1]=label|x[2]=x1|y[2]=y1|base[2]=base1|text[2]=label1|>
        ```
  
    === "HTML"

        ```html
        <taipy:chart type="bar" orientation="h" x[1]="x" y[1]="y" base[1]="base" text[1]="label" x[2]="x1" y[2]="y1" base[2]="base1" text[2]="label1">{data}</taipy:chart>
        ```

And the resulting chart is:

![Gantt like chart](ganttlike1.png)

-->
