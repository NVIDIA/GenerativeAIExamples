---
hide:
  - navigation
---

# Candlestick charts

Candlestick charts are commonly used in the stock market business. For a given
period, the open and close prices of some stock are represented as a
vertical bar, and vertical line emerging from that box shows the maximum and minimum
values of that stock for the period.

Taipy creates a candlestick chart when the control's [*type*](../chart.md#p-type)
property is set to "candlestick".

## Key properties

| Name            | Value            | Notes   |
| --------------- | -------------------------- | ------------------ |
| [*type*](../chart.md#p-type)       | `candlestick`  |  |
| [*x*](../chart.md#p-x)             | x values       |  |
| [*open*](../chart.md#p-open)       | Open values    |  |
| [*close*](../chart.md#p-close)     | Close values   |  |
| [*low*](../chart.md#p-low)         | Low values     |  |
| [*high*](../chart.md#p-high)       | High values    |  |
| [*options*](../chart.md#p-options) | dictionary | `decreasing` and `increasing` can be used to customize the rendering of candlesticks.  |
| [*layout](../chart.md#p-layout)    | dictionary | `xaxis` can be used to define how what the *x* axis should display and how.  |

## Examples

### Simple candlestick chart {data-source="gui:doc/examples/charts/candlestick-simple.py"}

The following example creates a candlestick chart for the AAPL stock price. It shows all
the relevant daily information for an entire month.

Note that we use the Python [*yfinance* package](https://pypi.org/project/yfinance/)
to query the historical data:
```python
# Extraction of a month of stock data for AAPL using the
# yfinance package (see https://pypi.org/project/yfinance/).
ticker = yfinance.Ticker("AAPL")
# The returned value is a Pandas DataFrame.
stock = ticker.history(interval="1d", start="2018-08-01", end="2018-08-31")
# Copy the DataFrame's index to a new column
stock["Date"] = stock.index
```

The *x* axis will be appropriately labeled "Date", thanks to the additional
column.

The chart definition is the following:
!!! example "Definition"

    === "Markdown"

        ```
        <|{stock}|chart|type=candlestick|x=Date|open=Open|close=Close|low=Low|high=High|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="candlestick" x="Date" open="Open" close="Close" low="Low" high="High">{stock}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{stock}", type="candlestick", x="Date", open="Open", close="Close", low="Low", high="High")
        ```

The chart is displayed like this:
<figure>
    <img src="../candlestick-simple-d.png" class="visible-dark" />
    <img src="../candlestick-simple-l.png" class="visible-light"/>
    <figcaption>Simple candlestick chart</figcaption>
</figure>

### Styling candlestick charts {data-source="gui:doc/examples/charts/candlestick-styling.py"}

By default, Plotly creates green candlestick bars when the value grows (when *close* is
greater than *open*) and red candlestick bars when the value decreases.<br/>

Here is some code that applies colors of our choosing to the candlesticks. This code
also removes the *range slider* (the thin candlestick overview under the main area):
```python
# Extraction of a few days of stock historical data for AAPL using
# the yfinance package (see https://pypi.org/project/yfinance/).
# The returned value is a Pandas DataFrame.
ticker = yfinance.Ticker("AAPL")
stock = ticker.history(interval="1d", start="2018-08-18", end="2018-09-10")
# Copy the DataFrame index to a new column
stock["Date"] = stock.index

options = {
    # Candlesticks that show decreasing values are orange
    "decreasing": {
        "line": {
            "color": "orange"
        }
    },
    # Candlesticks that show decreasing values are blue
    "increasing": {
        "line": {
            "color": "blue"
        }
    }
}

layout = {
    "xaxis": {
        # Hide the range slider
        "rangeslider": {
            "visible": False
        }
    }
}
```

The data set is similar yet smaller than in the first example.

We have added two dictionaries (*options* and *layout*) that let us
customize how the chart is ultimately rendered.

We use these dictionaries in the chart definition:
!!! example "Definition"

    === "Markdown"

        ```
        <|{stock}|chart|type=candlestick|x=Date|open=Open|close=Close|low=Low|high=High|options={options}|layout={layout}|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="candlestick" x="Date" open="Open" close="Close" low="Low" high="High" options="{options}" layout="{layout}">{stock}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{stock}", type="candlestick", x="Date", open="Open", close="Close", low="Low", high="High", options="{options}", layout="{layout}")
        ```

This is what the customized candlestick chart looks like:
<figure>
    <img src="../candlestick-styling-d.png" class="visible-dark" />
    <img src="../candlestick-styling-l.png" class="visible-light"/>
    <figcaption>Styling candlestick charts</figcaption>
</figure>

### Using a time series {data-source="gui:doc/examples/charts/candlestick-timeseries.py"}

So far, the *x* values were taken from the Pandas DataFrame that was built by the
[*yfinance*](https://pypi.org/project/yfinance/) API: the *index* of the DataFrame
contains a series of *Timestamp* instances from the Pandas library.

You can create your own time series using the common *datetime* type that are
available in all Python implementations in the *datetime* package:
```python
# Retrieved history:
# (Open, Close, Low, High)
stock_history = [
    (311.05, 311.00, 310.75, 311.33),
    (308.53, 308.31, 307.72, 309.00),
    (307.35, 306.24, 306.12, 307.46),
    ...
    (299.42, 300.50, 299.42, 300.50),
    (300.70, 300.65, 300.32, 300.75),
    (300.65, 299.91, 299.91, 300.76)
]
start_date = datetime.datetime(year=2022, month=10, day=21)
period = datetime.timedelta(seconds=4 * 60 * 60)  # 4 hours

data = {
    # Compute date series
    "Date": [start_date+n*period for n in range(0, len(stock_history))],
    # Extract open values
    "Open": [v[0] for v in stock_history],
    # Extract close values
    "Close": [v[1] for v in stock_history],
    # Extract low values
    "Low": [v[2] for v in stock_history],
    # Extract high values
    "High": [v[3] for v in stock_history]
}
```

The chart definition is straightforward:
!!! example "Definition"

    === "Markdown"

        ```
        <|{stock}|chart|type=candlestick|x=Date|open=Open|close=Close|low=Low|high=High|>
        ```

    === "HTML"

        ```html
        <taipy:chart type="candlestick" x="Date" open="Open" close="Close" low="Low" high="High">{stock}</taipy:chart>
        ```

    === "Python"

        ```python
        import taipy.gui.builder as tgb
        ...
        tgb.chart("{stock}", type="candlestick", x="Date", open="Open", close="Close", low="Low", high="High")
        ```

As you can see, Taipy deals with *datetime* objects as well as specific
types from Pandas, transparently.

Here is the result:
<figure>
    <img src="../candlestick-timeseries-d.png" class="visible-dark" />
    <img src="../candlestick-timeseries-l.png" class="visible-light"/>
    <figcaption>Using a time series</figcaption>
</figure>
