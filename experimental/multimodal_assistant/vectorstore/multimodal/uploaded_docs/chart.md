---
title: <tt>chart</tt>
hide:
  - navigation
---

<!-- Category: controls -->
Displays data sets in a chart or a group of charts.

The chart control is based on the [plotly.js](https://plotly.com/javascript/)
graphs library.<br/>
Plotly is a graphing library that provides a vast number of visual
representations of datasets with all sorts of customization capabilities. Taipy
exposes the Plotly components through the `chart` control and heavily depends on
the underlying implementation.

!!! tip "Using the Python API for Plotly"

    You may be familiar with the
    [Plotly Open Source Graphing Library for Python](https://plotly.com/python/) or find a piece of
    code written in Python that produces a Plotly chart close to your objective. In this
    situation, consider using the [*figure*](#p-figure) property of the chart control: this property
    lets you define your chart entirely in Python using Plotly's API.<br/>
    Please read the [section of the *figure* property](#the-figure-property) for more information.

There are many types of data representation that one can choose from, listed in the
[Chart types catalog](#chart-types-catalog) section, and each of these utilize specific
sets of the chart control properties.<br/>
For more general information on how to use the Taipy GUI chart control, we may want to look at
these two sections that provide more generic information on the control and how to use it in
specific situations best:

<div class="tp-row tp-row--gutter-sm">

  <div class="tp-col-12 tp-col-md-6 d-flex">
    <a class="tp-content-card tp-content-card--beta" href="../charts/basics/">
      <header class="tp-content-card-header">
        <img class="tp-content-card-icon" src="../chart-basics-icon.svg" width="100px"/>
      </header>
      <div class="tp-content-card-body">
        <h3>Basic concepts</h3>
        <p>
          The core principles of creating charts in Taipy.
        </p>
      </div>
    </a>
  </div>

  <div class="tp-col-12 tp-col-md-6 d-flex">
    <a class="tp-content-card tp-content-card--alpha" href="../charts/advanced/">
      <header class="tp-content-card-header">
        <img class="tp-content-card-icon" src="../chart-advanced.icon.svg" width="80px"/>
      </header>
      <div class="tp-content-card-body">
        <h3>Advanced topics</h3>
        <p>
          Leverage the Plotly library capabilities to provide tailored information and interaction.
        </p>
      </div>
    </a>
  </div>
</div>



# Chart types catalog

Because there are so many different ways of representing data, we have sorted
the chart types supported by Taipy by application category:

<style>
.h3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.h3 a {
  font-weight: 400;
  font-size: 16px;
  line-height: 24px;
  display: flex;
  align-items: center;
}
.h3 a svg {
    fill: #FE462B;
    max-height: 100%;
    width: 1.125em;
    margin-right: 10px;
}
.md-typeset .list:not([hidden]) {
    margin-left: 0;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: stretch;
    justify-content: flex-start;
    list-style: none;
    gap: 16px;
    padding: 0;
}
.list li {
    display: flex;
    margin: 0 !important;
    padding: 0;
    width: 171px;
}
.list a {
    display: flex;
    flex: 0 0 100%;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    gap: 16px;
    border-radius: 4px;
    color: var(--md-default-fg-color);
    background: var(--md-paper-bg-color);
}
.list a>img {
    border: 2px solid currentColor;
    border-radius: 4px;
}
.list span {
    line-height: 17px;
    display: flex;
    flex: 1 1 0;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    font-size: 16px;
}
.list a svg {
    fill: var(--md-typeset-a-color);
    max-height: 100%;
    width: 1.125em;
    margin-left: 10px;
}
</style>
<svg xmlns="http://www.w3.org/2000/svg" display="none">
    <symbol id="rarrow" viewBox="0 0 24 24">
        <path d="M4 11v2h12l-5.5 5.5 1.42 1.42L19.84 12l-7.92-7.92L10.5 5.5 16 11H4z"></path>
    </symbol>
</svg>

<h3 class="h3">Basic charts</h3>
<ul class="list">
    <li><a href="../charts/line">
        <span>Line charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-line-d.png"  class="visible-dark" />
        <img src="../charts/home-line-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/scatter">
        <span>Scatter plots<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-scatter-d.png"  class="visible-dark" />
        <img src="../charts/home-scatter-l.png"  class="visible-light" />
        </a></li>
    <li><a href="../charts/bar">
        <span>Bar charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-bar-d.png"  class="visible-dark" />
        <img src="../charts/home-bar-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/bubble">
        <span>Bubble charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-bubble-d.png"  class="visible-dark" />
        <img src="../charts/home-bubble-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/filled-area">
        <span>Filled areas<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-filled-area-d.png"  class="visible-dark" />
        <img src="../charts/home-filled-area-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/pie">
        <span>Pie charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-pie-d.png"  class="visible-dark" />
        <img src="../charts/home-pie-l.png"  class="visible-light" />
      </a></li>
    <!-- Sunburst charts - sunburst -->
    <!-- Sankey diagram  - sankey   -->
</ul>

<h3 class="h3">Statistical charts</h3>
<ul class="list">
    <li><a href="../charts/histogram">
        <span>Histograms<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-histogram-d.png"  class="visible-dark" />
        <img src="../charts/home-histogram-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/heatmap">
        <span>Heatmaps<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-heatmap-d.png"  class="visible-dark" />
        <img src="../charts/home-heatmap-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/error-bars">
        <span>Error bars<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-error-bars-d.png"  class="visible-dark" />
        <img src="../charts/home-error-bars-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/continuous-error">
        <span>Continuous error<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-continuous-error-d.png"  class="visible-dark" />
        <img src="../charts/home-continuous-error-l.png"  class="visible-light" />
      </a></li>
    <!-- TODO li><a href="../charts/box-plot">
        <span>Box plots<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-box-plot-d.png"  class="visible-dark" />
        <img src="../charts/home-box-plot-l.png"  class="visible-light" />
      </a></li -->
    <!-- Violin plots - violin -->
    <!-- 2D histograms - 2d-histogram -->
    <!-- 2d density plot - 2d-density-->
    <!-- Contour plots - contour -->
</ul>

<h3 class="h3">Scientific charts</h3>
<ul class="list">
    <li><a href="../charts/polar">
        <span>Polar charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-polar-d.png"  class="visible-dark" />
        <img src="../charts/home-polar-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/radar">
        <span>Radar charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-radar-d.png"  class="visible-dark" />
        <img src="../charts/home-radar-l.png"  class="visible-light" />
      </a></li>
</ul>

<h3 class="h3">Financial charts</h3>
<ul class="list">
    <li><a href="../charts/candlestick">
        <span>Candlestick charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-candlestick-d.png"  class="visible-dark" />
        <img src="../charts/home-candlestick-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/funnel">
        <span>Funnel charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-funnel-d.png"  class="visible-dark" />
        <img src="../charts/home-funnel-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/waterfall">
        <span>Waterfall charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-waterfall-d.png"  class="visible-dark" />
        <img src="../charts/home-waterfall-l.png"  class="visible-light" />
      </a></li>
</ul>

<h3 class="h3">Maps</h3>
<ul class="list">
    <li><a href="../charts/map">
        <span>Map plots<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-map-d.png"  class="visible-dark" />
        <img src="../charts/home-map-l.png"  class="visible-light" />
      </a></li>
    <!-- TODO li><a href="../charts/area-map">
        <span>Areas on maps<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-area-map-d.png"  class="visible-dark" />
        <img src="../charts/home-area-map-l.png"  class="visible-light" />
      </a></li -->
    <!-- TODO li><a href="../charts/density-map">
        <span>Density maps<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-density-map-d.png"  class="visible-dark" />
        <img src="../charts/home-density-map-l.png"  class="visible-light" />
      </a></li -->
    <!-- Choropleth maps - choropleth-map -->
</ul>

<h3 class="h3">Specialized charts</h3>
<ul class="list">
    <li><a href="../charts/treemap">
        <span>Treemaps<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-treemap-d.png"  class="visible-dark" />
        <img src="../charts/home-treemap-l.png"  class="visible-light" />
      </a></li>
    <li><a href="../charts/gantt">
        <span>Gantt charts<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><use xlink:href="#rarrow"/></svg></span>
        <img src="../charts/home-gantt-d.png"  class="visible-dark" />
        <img src="../charts/home-gantt-l.png"  class="visible-light" />
      </a></li>
</ul>

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
<td nowrap><code id="p-data"><u><bold>data</bold></u></code><sup><a href="#dv">(&#9733;)</a></sup></td>
<td><code>any</code><br/><i>dynamic</i></td>
<td nowrap><i>Required</i></td>
<td><p>The data object bound to this chart control.<br/>See the section on the <a href="#the-data-property"><i>data</i> property</a> below for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-type">type</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap>scatter</td>
<td><p>Chart type.<br/>See the Plotly <a href="https://plotly.com/javascript/reference/">chart type</a> documentation for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-mode">mode</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap>lines+markers</td>
<td><p>Chart mode.<br/>See the Plotly <a href="https://plotly.com/javascript/reference/scatter/#scatter-mode">chart mode</a> documentation for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-x">x</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>x</i> axis.</p></td>
</tr>
<tr>
<td nowrap><code id="p-y">y</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>y</i> axis.</p></td>
</tr>
<tr>
<td nowrap><code id="p-z">z</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>z</i> axis.</p></td>
</tr>
<tr>
<td nowrap><code id="p-lon">lon</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>longitude</i> value, for 'scattergeo' charts. See <a href="https://plotly.com/javascript/reference/scattergeo/#scattergeo-lon">Plotly Map traces</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-lat">lat</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>latitude</i> value, for 'scattergeo' charts. See <a href="https://plotly.com/javascript/reference/scattergeo/#scattergeo-lat">Plotly Map traces</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-r">r</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>r</i> value, for 'scatterpolar' charts. See <a href="https://plotly.com/javascript/polar-chart/">Plotly Polar charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-theta">theta</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>theta</i> value, for 'scatterpolar' charts. See <a href="https://plotly.com/javascript/polar-chart/">Plotly Polar charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-high">high</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>high</i> value, for 'candlestick' charts. See <a href="https://plotly.com/javascript/reference/candlestick/#candlestick-high">Plotly Candlestick charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-low">low</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>low</i> value, for 'candlestick' charts. See <a href="https://plotly.com/javascript/reference/candlestick/#candlestick-low">Ploty Candlestick charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-open">open</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>open</i> value, for 'candlestick' charts. See <a href="https://plotly.com/javascript/reference/candlestick/#candlestick-open">Plotly Candlestick charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-close">close</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>close</i> value, for 'candlestick' charts. See <a href="https://plotly.com/javascript/reference/candlestick/#candlestick-close">Plotly Candlestick charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-measure">measure</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>measure</i> value, for 'waterfall' charts. See <a href="https://plotly.com/javascript/reference/waterfall/#waterfall-measure">Plotly Waterfall charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-locations">locations</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>locations</i> value. See <a href="https://plotly.com/javascript/choropleth-maps/">Plotly Choropleth maps</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-values">values</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>values</i> value. See <a href="https://plotly.com/javascript/reference/pie/#pie-values">Plotly Pie charts</a> or <a href="https://plotly.com/javascript/reference/funnelarea/#funnelarea-values">Plotly Funnel Area charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-labels">labels</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>labels</i> value. See <a href="https://plotly.com/javascript/reference/pie/#pie-labels">Plotly Pie charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-parents">parents</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>parents</i> value. See <a href="https://plotly.com/javascript/reference/treemap/#treemap-parents">Plotly Treemap charts</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-text">text</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the text associated to the point for the indicated trace.<br/>This is meaningful only when <i>mode</i> has the <i>text</i> option.</p></td>
</tr>
<tr>
<td nowrap><code id="p-base">base</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Column name for the <i>base</i> value. Used in bar charts only.<br/>See the Plotly <a href="https://plotly.com/javascript/reference/bar/#bar-base">bar chart base</a> documentation for details."</p></td>
</tr>
<tr>
<td nowrap><code id="p-title">title</code></td>
<td><code>str</code></td>
<td nowrap></td>
<td><p>The title of this chart control.</p></td>
</tr>
<tr>
<td nowrap><code id="p-render">render</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>True</td>
<td><p>If True, this chart is visible on the page.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_range_change">on_range_change</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The callback function that is invoked when the visible part of the x axis changes.<br/>The function receives three parameters:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>id (optional[str]): the identifier of the chart control.</li>
<li>payload (dict[str, any]): the full details on this callback's invocation, as emitted by <a href="https://plotly.com/javascript/plotlyjs-events/#update-data">Plotly</a>.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-columns">columns</code></td>
<td><code>str|list[str]|dict[str, dict[str, str]]</code></td>
<td nowrap><i>All columns</i></td>
<td><p>The list of column names
<ul>
<li>str: ;-separated list of column names</li>
<li>list[str]: list of names</li>
<li>dict: {"column_name": {format: "format", index: 1}} if index is specified, it represents the display order of the columns.
If not, the list order defines the index</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-label">label</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The label for the indicated trace.<br/>This is used when the mouse hovers over a trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-name">name</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The name of the indicated trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-selected">selected</code></td>
<td><code>dynamic(list[int]|str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The list of the selected point indices  .</p></td>
</tr>
<tr>
<td nowrap><code id="p-color">color</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The color of the indicated trace (or a column name for scattered).</p></td>
</tr>
<tr>
<td nowrap><code id="p-selected_color">selected_color</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The color of the selected points for the indicated trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-marker">marker</code></td>
<td><code>dict[str, any]</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The type of markers used for the indicated trace.<br/>See <a href="https://plotly.com/javascript/reference/scatter/#scatter-marker">marker</a> for details.<br/>Color, opacity, size and symbol can be column name.</p></td>
</tr>
<tr>
<td nowrap><code id="p-line">line</code></td>
<td><code>str|dict[str, any]</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The configuration of the line used for the indicated trace.<br/>See <a href="https://plotly.com/javascript/reference/scatter/#scatter-line">line</a> for details.<br/>If the value is a string, it must be a dash type or pattern (see <a href="https://plotly.com/python/reference/scatter/#scatter-line-dash">dash style of lines</a> for details).</p></td>
</tr>
<tr>
<td nowrap><code id="p-selected_marker">selected_marker</code></td>
<td><code>dict[str, any]</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The type of markers used for selected points in the indicated trace.<br/>See <a href="https://plotly.com/javascript/reference/scatter/#scatter-selected-marker">selected marker for details.</p></td>
</tr>
<tr>
<td nowrap><code id="p-layout">layout</code></td>
<td><code>dict[str, any]</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>The <i>plotly.js</i> compatible <a href="https://plotly.com/javascript/reference/layout/">layout object</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-plot_config">plot_config</code></td>
<td><code>dict[str, any]</code></td>
<td nowrap></td>
<td><p>The <i>plotly.js</i> compatible <a href="https://plotly.com/javascript/configuration-options/"> configuration options object</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-options">options</code></td>
<td><code>dict[str, any]</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The <i>plotly.js</i> compatible <a href="https://plotly.com/javascript/reference/">data object where dynamic data will be overridden.</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-orientation">orientation</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The orientation of the indicated trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-text_anchor">text_anchor</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>Position of the text relative to the point.<br/>Valid values are: <i>top</i>, <i>bottom</i>, <i>left</i>, and <i>right</i>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-xaxis">xaxis</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The <i>x</i> axis identifier for the indicated trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-yaxis">yaxis</code></td>
<td><code>str</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>The <i>y</i> axis identifier for the indicated trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-width">width</code></td>
<td><code>str|int|float</code></td>
<td nowrap>"100%"</td>
<td><p>The width, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-height">height</code></td>
<td><code>str|int|float</code></td>
<td nowrap></td>
<td><p>The height, in CSS units, of this element.</p></td>
</tr>
<tr>
<td nowrap><code id="p-template">template</code></td>
<td><code>dict</code></td>
<td nowrap></td>
<td><p>The Plotly layout <a href="https://plotly.com/javascript/layout-template/">template</a>.</p></td>
</tr>
<tr>
<td nowrap><code id="p-template[dark]">template[dark]</code></td>
<td><code>dict</code></td>
<td nowrap></td>
<td><p>The Plotly layout <a href="https://plotly.com/javascript/layout-template/">template</a> applied over the base template when theme is dark.</p></td>
</tr>
<tr>
<td nowrap><code id="p-template[light]">template[light]</code></td>
<td><code>dict</code></td>
<td nowrap></td>
<td><p>The Plotly layout <a href="https://plotly.com/javascript/layout-template/">template</a> applied over the base template when theme is not dark.</p></td>
</tr>
<tr>
<td nowrap><code id="p-decimator">decimator</code></td>
<td><code>taipy.gui.data.Decimator</code><br/><i>indexed</i></td>
<td nowrap></td>
<td><p>A decimator instance for the indicated trace that will reduce the size of the data being sent back and forth.<br>If defined as indexed, it will impact only the indicated trace; if not, it will apply only the the first trace.</p></td>
</tr>
<tr>
<td nowrap><code id="p-rebuild">rebuild</code></td>
<td><code>bool</code><br/><i>dynamic</i></td>
<td nowrap>False</td>
<td><p>Allows dynamic config refresh if set to True.</p></td>
</tr>
<tr>
<td nowrap><code id="p-figure">figure</code></td>
<td><code>plotly.graph_objects.Figure</code><br/><i>dynamic</i></td>
<td nowrap></td>
<td><p>A figure as produced by plotly.</p></td>
</tr>
<tr>
<td nowrap><code id="p-on_change">on_change</code></td>
<td><code>Callback</code></td>
<td nowrap></td>
<td><p>The name of a function that is triggered when the value is updated.<br/>The parameters of that function are all optional:
<ul>
<li>state (<code>State^</code>): the state instance.</li>
<li>var_name (str): the variable name.</li>
<li>value (any): the new value.</li>
</ul></p></td>
</tr>
<tr>
<td nowrap><code id="p-propagate">propagate</code></td>
<td><code>bool</code></td>
<td nowrap><i>App config</i></td>
<td><p>Allows the control's main value to be automatically propagated.<br/>The default value is defined at the application configuration level.<br/>If True, any change to the control's value is immediately reflected in the bound application variable.</p></td>
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

<p><sup id="dv">(&#9733;)</sup><a href="#p-data" title="Jump to the default property documentation."><code>data</code></a> is the default property for this visual element.</p>

# Details

The chart control has a large set of properties to deal with the many types of charts
it supports and the different kinds of customization that can be defined.

## The *data* property

All the data sets represented in the chart control must be assigned to
its [*data*](#p-data) property.

The supported types for the [*data*](#p-data) property are:

- A list of values:<br/>
    Most chart types use two axes (*x*/*y* or *theta*/*r*). When receiving a *data* that is just
    a series of values, Taipy sets the first axis values to the value index ([0, 1, ...]) and
    the values of the second axis to the values of the collection.
- A [Pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):<br/>
    Taipy charts can be defined by setting the appropriate axis property value to the DataFrame
    column name.
- A dictionary:<br/>
    The value is converted into a Pandas DataFrame where each key/value pair is converted
    to a column named *key* and the associated value. Note that this will work only when
    all the values of the dictionary keys are series that have the same length.
- A list of lists of values:<br/>
    If all the lists have the same length, Taipy creates a Pandas DataFrame with it.<br/>
    If sizes differ, then a DataFrame is created for each list, with a single column
    called "*&lt;index&gt;*/0" where *index* is the index of the current list in the *data*
    array. Then an array is built using all those DataFrames and used as described
    below.
- A Numpy series:<br/>
    Taipy internally builds a Pandas DataFrame with the provided *data*.
- A list of Pandas DataFrames:<br/>
    This can be used when your chart must represent data sets of different sizes. In this case,
    you must set the axis property ([*x*](#p-x), [*y*](#p-y), [*r*](#p-r), etc.) value to a string
    with the format: "*&lt;index&gt;*/*&lt;column&gt;*" where *index* is the index of the DataFrame
    you want to refer to (starting at index 0) and *column* would be the column name of the
    referenced DataFrame.
- A list of dictionaries<br/>
    The *data* is converted to a list of Pandas DataFrames.

## Indexed properties

Chart controls can hold several traces that may display different data sets.<br/>
To indicate properties for a given trace, you will use the indexed properties
(the ones whose type is *indexed(type)*). When setting the value of an indexed
property, you can specify which trace this property should apply to: you will
use the *property_name[index]* syntax, where the indices start at index 1, to
specify which trace is targeted for this property.

Indexed properties can have a default value (using the *property_name* syntax with
no index) which is overridden by any specified indexed property:<br/>
Here is an example where *i_property* is an indexed property:

```
# This value applies to all the traces of the chart control
general_value = <some_value>
# This value applies to only the second trace of the chart control
specific_value = <some_other_value>

page = "<|...|chart|...|i_property={general_value}|i_property[2]={specific_value}|...|>"
```

In the definition for *page*, you can see that the value *general_value* is set to the
property without the index operator ([]) syntax. That means it applies to all the traces
of the chart control.<br/>
*specific_value*, on the other hand, applies only to the second trace.

An indexed property can also be assigned an array, without the index operator syntax.
Then each value of the array is set to the property at the appropriate index, in sequence:

```
values = [
    value1,
    value2,
    value3
]
    
page = "<|...|chart|...|i_property={values}|...|>"
```

is equivalent to

```
page = "<|...|chart|...|i_property[1]={value1}|i_property[2]={value2}|i_property[3]={value3}|...|>"
```

or slightly shorter (and if there are no more than three traces):

```
page = "<|...|chart|...|i_property={value1}|i_property[2]={value2}|i_property[3]={value3}|...|>"
```

## The *figure* property

As mentioned above, the chart control is implemented using the
[plotly.js](https://plotly.com/javascript/) front-end library, and hides part of its complexity
using the control's properties. However [Plotly](https://plotly.com/) comes with the handy
[Plotly for Python](https://plotly.com/python/) library that lets programmers define their charts
entirely in Python.<br/>

If you are familiar with the Plotly Python API or if you have found, among the plethora of
examples available on the Internet, a piece of code that produce something close to your
expectations, you may feel like it can be tricky to mimic that the 'Taipy GUI way', using the chart
control and its properties.<br/>
However you can easily reuse your Python code using the [*figure*](#p-figure) property: this can be
set to an instance of `plotly.graph_objects.Figure`, which is the class used by Plotly Python to
handle the entire definition of a graph. When the chart is rendered on the page, it displays
exactly what was defined using the Plotly Python API.

Please check the
[Plotly Python example](charts/advanced.md#using-the-ploty-python-library)
for more details.

## The *rebuild* property {data-source="gui:doc/examples/charts/example-rebuild.py"}

Some of the chart control's properties may result in Taipy GUI having to entirely reconstruct the
graphical component running on the front-end (the user's browser). The chart control provides some
properties that are *dynamic* and allow for an instant page update. Changing the values of the
other properties is not immediately reflected on the page.<br/>
Setting the value of the [*rebuild*](#p-rebuild) property to True, however, will ensure that the
control is entirely rebuilt on the front-end and refreshed on the page. Using this property will
have an impact on the user experience since it involves a potentially extensive code generation.
Make sure, when you use the *rebuild* property, that the deployment environment can support the
performance hit gracefully for the end users.

Here is an example of how this property can be used.<br/>
Consider the code below:

```python title="chart.py"
from taipy.gui import Gui
import math

# x values: [-10..10]
x_range = range(-10, 11)
data = {
    "X": x_range,
    "Y": [x*x for x in x_range],
    "Y2": [math.cos(2 * math.pi * x / 10) / 360 for x in x_range]
}

types = [("bar", "Bar"), ("line", "Line")]
selected_type = types[0]

page = """
<|{data}|chart|type={selected_type[0]}|x=X|y=Y|>

<|{selected_type}|toggle|lov={types}|>
"""

Gui(page=page).run()
```

This application displays a chart representing two functions of the values stored in the array
*x_range*: the squared value and a cosine function.<br/>
A [`toggle`](toggle.md) control is added to the page to let the user choose the chart type
dynamically: a line chart or a bar chart.

Here is what this application looks like when you run it:
<figure class="tp-center">
    <img src="../chart-rebuild-1-d.png" class="visible-dark"  width="75%"/>
    <img src="../chart-rebuild-1-l.png" class="visible-light" width="75%"/>
    <figcaption>Initial display of the application</figcaption>
</figure>

If the user switches the type in the toggle button, this would be the resulting page:
<figure class="tp-center">
    <img src="../chart-rebuild-2-d.png" class="visible-dark"  width="75%"/>
    <img src="../chart-rebuild-2-l.png" class="visible-light" width="75%"/>
    <figcaption>After the type was switched</figcaption>
</figure>

You can see that although the toggle value was changed, the chart was not impacted by the new
setting. That is because the [*type*](#p-type) property is *not* dynamic.<br/>
To display the chart with the new type setting, one would have to refresh the browser page.

However, Taipy GUI can rebuild and refresh the chart automatically if you set it's
[*rebuild*](#p-rebuild) property to True. The Markdown chart definition can be changed
to:
```
<|{data}|chart|type={selected_type[0]}|x=X|y=Y|rebuild|>
```

If you run the application again, as soon as the user selects the new chart type using the toggle
button, the page will reflect the change without explicit refresh:
<figure class="tp-center">
    <img src="../chart-rebuild-3-d.png" class="visible-dark"  width="75%"/>
    <img src="../chart-rebuild-3-l.png" class="visible-light" width="75%"/>
    <figcaption>After the type was switched, with <i>rebuild</i> set to True</figcaption>
</figure>

# Styling

All the chart controls are generated with the "taipy-chart" CSS class. You can use this class
name to select the charts on your page and apply style.

## [Stylekit](../styling/stylekit.md) support

The [Stylekit](../styling/stylekit.md) provides a specific class that you can use to style charts:

* *has-background*<br/>
    When the chart control uses the *has-background* class, the rendering of the chart
    background is left to the charting library.<br/>
    The default behavior is to render the chart transparently.

# Usage

Here is a list of several sub-sections that you can check to get more details on a specific
domain covered by the chart control:

- [Basic concepts](charts/basics.md)
- [Line charts](charts/line.md)
- [Scatter charts](charts/scatter.md)
- [Bar charts](charts/bar.md)
- [Bubble charts](charts/bubble.md)
- [Filled areas](charts/filled-area.md)
- [Pie charts](charts/pie.md)
- [Histograms](charts/histogram.md)
- [Heatmaps](charts/heatmap.md)
- [Error bars](charts/error-bars.md)
- [Continuous error](charts/continuous-error.md)
- [Box plots](charts/box-plot.md)
- [Polar charts](charts/polar.md)
- [Radar charts](charts/radar.md)
- [Candlestick charts](charts/candlestick.md)
- [Funnel charts](charts/funnel.md)
- [Waterfall charts](charts/waterfall.md)
- [Treemaps](charts/treemap.md)
- [Maps](charts/map.md)
- [Gantt charts](charts/gantt.md)
- [Advanced topics](charts/advanced.md)
