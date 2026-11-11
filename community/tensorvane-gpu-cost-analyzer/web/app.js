"use strict";

const $ = id => document.getElementById(id);
const fields = { cost: "Spend", usage: "Usage", utilization: "Utilization", date: "Date" };
const operationNames = {
  sum: "Total", mean: "Average", top_n: "Top groups", bottom_n: "Bottom groups",
  week_over_week: "Week over week", nunique: "Distinct count",
};
const format = new Intl.NumberFormat(undefined, { maximumSignificantDigits: 12 });
const percentFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2, signDisplay: "exceptZero" });
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" });
const views = {
  overview: ["Overview", ""],
  quality: ["Data quality", "Inspect missing values, invalid measurements, and incomplete periods."],
  mapping: ["Detected columns", "See how each source column is used in your analysis."],
  chat: ["Ask your data", "Explore the numbers with a question."],
  calculations: ["Calculations", "The aggregate results behind your dashboard."],
};
let active = null;
let activeModel = null;
let modelEnabled = false;
let triedMapping = false;
let busy = false;
let report = null;
let selectedMetric = null;
let currentView = Object.hasOwn(views, location.hash.slice(1)) ? location.hash.slice(1) : "overview";
let chartGeometry = [];
let hoverPoint = null;
let accountPage = 0;
const ACCOUNT_PAGE_SIZE = 10;

function element(tag, value, className) {
  const node = document.createElement(tag);
  if (value != null) node.textContent = value;
  if (className) node.className = className;
  return node;
}

function fieldLabel(field) {
  const names = {
    rate: "Unit rate", gpus_allocated: "Allocated GPUs",
    jobs_failed: "Failed jobs", jobs_submitted: "Jobs submitted",
  };
  if (names[field]) return names[field];
  const source = fields[field] || active?.column_inspection?.fields?.[field]?.source || field;
  const label = source.replaceAll("_", " ")
    .replace(/\s+(USD|EUR|GBP|PKR|AED|CAD|AUD|INR|JPY|pct|percent|tonnes|tons|kg|50kg)$/i, "")
    .replace(/\bgpu\b/gi, "GPU").replace(/\bid\b/gi, "ID");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function metricInfo(field) {
  const source = active?.column_inspection?.fields?.[field]?.source || field;
  const currency = source.match(/(?:^|[_\s])(USD|EUR|GBP|PKR|AED|CAD|AUD|INR|JPY)(?:$|[_\s])/i)?.[1].toUpperCase();
  if (field === "utilization") return { unit: "0–100% scale", kind: "percent" };
  if (currency) {
    const unit = field === "rate" && /gpu.*hour/i.test(source.replaceAll("_", " "))
      ? currency + " per GPU hour" : currency;
    return { unit, kind: "currency", currency };
  }
  if (/\b(gpu.*(?:hrs|hours))\b/i.test(source.replaceAll("_", " "))) return { unit: "GPU hours", kind: "number" };
  if (/(?:hours|hrs)/i.test(source)) return { unit: "Hours", kind: "number" };
  if (/(?:tonnes|tons)/i.test(source)) return { unit: "Tonnes", kind: "number" };
  if (/50kg/i.test(source)) return { unit: "50 kg bags", kind: "number" };
  if (field === "gpus_allocated") return { unit: "GPUs", kind: "number" };
  if (field.startsWith("jobs_")) return { unit: "Jobs", kind: "number" };
  if (field === "cost" || field === "rate") return { unit: "Currency not specified", kind: "amount" };
  return { unit: "Unit not specified", kind: "number" };
}

function formatMetric(value, field, operation, precise = false) {
  if (value == null) return "—";
  if (["count", "nunique"].includes(operation)) return format.format(value);
  const info = metricInfo(field);
  if (value !== 0 && Math.abs(value) < 0.01) {
    return (info.currency ? info.currency + " " : "") + format.format(value) +
      (info.kind === "percent" ? "%" : "");
  }
  if (info.kind === "currency") {
    return new Intl.NumberFormat(undefined, {
      style: "currency", currency: info.currency, currencyDisplay: "narrowSymbol",
      minimumFractionDigits: 2, maximumFractionDigits: field === "rate" ? 4 : 2,
    }).format(value);
  }
  if (info.kind === "percent") return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value) + "%";
  if (info.kind === "amount") return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
  if (precise || (value !== 0 && Math.abs(value) < 0.01)) return format.format(value);
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

function reductionFor(result) {
  const index = report?.results.indexOf(result);
  const step = report?.plan?.calculations[index];
  return step?.reduction || result.operation;
}

function periodLabel(value) {
  return dateFormat.format(new Date(value + "T00:00:00Z"));
}

function showView(view) {
  if (!Object.hasOwn(views, view)) return;
  currentView = view;
  for (const page of document.querySelectorAll("[data-page]")) page.hidden = page.dataset.page !== view;
  for (const link of document.querySelectorAll("nav [data-view]")) {
    if (link.dataset.view === view) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  $("page-title").textContent = views[view][0];
  $("page-description").textContent = views[view][1];
  $("page-description").hidden = !views[view][1];
  $("breadcrumb-page").textContent = views[view][0];
  document.title = views[view][0] + " · Pears Analyzer";
  window.scrollTo({ top: 0 });
  if (view === "overview") requestAnimationFrame(drawChart);
}

function navigate(view) {
  if (location.hash === "#" + view) showView(view);
  else location.hash = view;
}

document.addEventListener("click", event => {
  const link = event.target.closest('a[href^="#"]');
  const view = link?.getAttribute("href").slice(1);
  if (Object.hasOwn(views, view)) {
    event.preventDefault();
    navigate(view);
  }
});
window.addEventListener("hashchange", () => showView(location.hash.slice(1)));

async function api(path, options = {}) {
  const headers = new Headers();
  if (active) headers.set("X-Dataset", active.token);
  if (path.startsWith("settings")) headers.set("X-NVA-Settings", "1");
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
    options.body = JSON.stringify(options.body);
  }
  const response = await fetch("/api/" + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "The request failed.");
  return data;
}

function notice(message, isError = false) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
  $("notice").classList.toggle("error", isError);
  $("notice").setAttribute("role", isError ? "alert" : "status");
  $("notice").setAttribute("aria-live", isError ? "assertive" : "polite");
}

function controls() {
  const ready = Boolean(active?.column_inspection?.ready);
  for (const id of ["demo", "demo-inline", "empty-action", "file", "run", "send", "suggest", "daily", "model-settings"]) {
    $(id).disabled = busy || (["run", "send", "daily"].includes(id) && !ready) || (id === "suggest" && !active);
  }
  for (const button of $("mapping-body").querySelectorAll("button")) button.disabled = busy;
  $("run").textContent = busy ? "Working…" : "Run analysis ↗";
  document.body.setAttribute("aria-busy", String(busy));
}

async function runTask(message, task) {
  if (busy) return;
  busy = true;
  controls();
  notice(message);
  try {
    await task();
    notice("");
  } catch (error) {
    notice(error.message, true);
  } finally {
    busy = false;
    controls();
  }
}

function renderMapping() {
  $("mapping-body").replaceChildren();
  const inspection = active.column_inspection;
  for (const { header, profile } of active.columns) {
    const decision = inspection?.columns[header];
    const row = element("div", null, "mapping-row");
    const title = element("div");
    title.append(element("strong", header), document.createElement("br"),
      element("small", profile.type + " · " +
        new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(profile.null_rate * 100) + "% blank"));
    const resolved = decision?.status === "mapped";
    const field = element("span", decision?.key ? fieldLabel(decision.key) : "Pending detection");
    const hint = decision?.reason || "Column detection will refresh on the next analysis.";
    const action = element("div");
    if (modelEnabled && triedMapping && !resolved && (decision?.score ?? 0) < 0.95) {
      const consent = element("button", "Share samples…", "button secondary");
      consent.type = "button";
      consent.addEventListener("click", () => {
        const { destination, model } = activeModel;
        if (window.confirm("Send up to five raw sample values from “" + header +
          "” to " + destination + " (" + model + ") for this mapping request?")) {
          suggest({ column: header, consent: true, destination, model });
        }
      });
      action.append(consent);
    }
    row.append(title, field, element("small", hint), action);
    $("mapping-body").append(row);
  }
  $("suggest").hidden = false;
  $("daily-control").hidden = false;
  $("dataset-status").textContent = inspection?.ready
    ? (report ? "Analysis ready" : "Ready to analyze") : "Review column detection";
  $("dataset-status").classList.toggle("ready", Boolean(inspection?.ready));
  renderChatSuggestions();
  if (!report) renderEmptyWorkspace();
  controls();
}

function suggest(data) {
  runTask("Inspecting columns…", async () => {
    const previous = JSON.stringify(active.column_inspection?.mapping);
    active = { ...active, ...await api(data.column ? "map" : "columns", { method: "POST", body: data }) };
    triedMapping = modelEnabled;
    renderMapping();
    if (previous !== JSON.stringify(active.column_inspection?.mapping)) clearReport();
  });
}

function metricCard(label, value, trend, unit = "") {
  const card = element("article", null, "metric");
  card.append(element("p", label), element("strong", value));
  card.append(element("span", unit, "metric-unit"));
  if (trend?.change_pct != null) {
    const text = element("div", null, "metric-trend");
    text.append(element("strong", percentFormat.format(trend.change_pct) + "%"),
      element("span", "vs prior week · " + periodLabel(trend.period)));
    text.title = trend.complete === true ? "Change from the previous complete week" : "Change from the previous week";
    card.append(text);
  }
  return card;
}

function renderQuality(quality) {
  const unusual = quality ? Object.values(quality.outlier_counts || {}).reduce((sum, count) => sum + count, 0) : null;
  const values = {
    "Rows received": quality?.input_rows, "Usable rows": quality?.usable_rows,
    "Rows with missing values": quality?.rows_with_missing_values,
    "Rows with invalid values": quality?.rows_with_invalid_values,
    "Exact duplicates removed": quality?.duplicates_removed,
    "Unusual values retained": unusual,
    "Missing days": quality ? ($("daily").checked ? quality.missing_dates.length : "Not checked") : null,
  };
  $("quality-values").replaceChildren();
  for (const [label, value] of Object.entries(values)) {
    const row = element("div");
    row.append(element("dt", label), element("dd", typeof value === "number" ? format.format(value) : value ?? "—"));
    $("quality-values").append(row);
  }
  const missing = quality?.missing_dates || [];
  $("missing-days").hidden = !missing.length;
  $("missing-days").textContent = "Missing dates · " + missing.map(periodLabel).join(", ");
  $("quality-details").replaceChildren();
  if (quality) {
    for (const [key, label] of [
      ["invalid_values_by_column", "invalid values"],
      ["missing_values_by_column", "missing values"],
      ["outlier_counts", "unusual values retained"],
    ]) {
      for (const [field, count] of Object.entries(quality[key] || {})) {
        if (count) $("quality-details").append(element("p", fieldLabel(field) + " · " + count + " " + label));
      }
    }
    $("quality-snapshot").replaceChildren();
    const indicators = [
      ["Rows with missing values", quality.rows_with_missing_values],
      ["Invalid rows", quality.rows_with_invalid_values],
      ["Duplicates removed", quality.duplicates_removed],
    ];
    if ($("daily").checked) indicators.push(["Missing days", quality.missing_dates.length]);
    for (const [label, count] of indicators) {
      const item = element("div");
      item.append(element("strong", format.format(count)), element("span", label));
      $("quality-snapshot").append(item);
    }
  } else {
    $("quality-snapshot").textContent = "Quality checks appear after analysis.";
  }
}

function calculationLabel(result) {
  return fieldLabel(result.metric) + " · " + (operationNames[result.operation] || result.operation.replaceAll("_", " ")) +
    (result.groups.length ? " by " + result.groups.map(fieldLabel).join(", ") : "");
}

function resultTable(result) {
  const container = element("div", null, "result-table");
  const info = metricInfo(result.metric);
  if (!result.account_usage && !["count", "nunique"].includes(result.operation) && !info.unit.startsWith("Source")) {
    container.append(element("p", info.unit, "filter-note"));
  }
  if (result.filters.length) {
    container.append(element("p", result.filters.map(item => fieldLabel(item.field) + " = " + item.value).join(" · "), "filter-note"));
  }
  if (!result.rows.length) {
    container.append(element("p", "No rows matched this calculation.", "empty"));
    return container;
  }
  const displayGroups = result.display_columns || result.groups;
  const keys = [...displayGroups, "value"];
  if (result.operation === "week_over_week") keys.push("previous", "change_pct");
  if (result.grain) keys.push("complete", "missing_days");
  const titles = {
    value: result.account_usage ? "Total usage" +
      (info.unit === "Unit not specified" ? "" : " (" + info.unit + ")")
      : ["count", "nunique"].includes(result.operation) ? "Count" : fieldLabel(result.metric),
    period: result.grain === "week" ? "Week starting" : "Period",
    previous: "Previous period", change_pct: "Weekly change",
    complete: "Period complete", missing_days: "Missing days",
  };
  const wrap = element("div", null, "table-wrap");
  const table = element("table");
  const head = element("thead");
  const headings = element("tr");
  for (const key of keys) {
    const cell = element("th", titles[key] || fieldLabel(key));
    if (!displayGroups.includes(key) && key !== "complete") cell.className = "numeric";
    cell.scope = "col";
    headings.append(cell);
  }
  head.append(headings);
  const body = element("tbody");
  let tablePage = 0;
  const pageSize = 25;
  function renderRows() {
    body.replaceChildren();
    for (const row of result.rows.slice(tablePage * pageSize, (tablePage + 1) * pageSize)) {
      const tr = element("tr");
      for (const key of keys) {
        const value = row[key];
        const display = key === "value" || key === "previous"
          ? formatMetric(value, result.metric, reductionFor(result), true)
          : key === "change_pct" && value != null ? percentFormat.format(value) + "%"
          : key === "period" && value ? periodLabel(value)
          : typeof value === "boolean" ? (value ? "Complete" : "Incomplete")
          : typeof value === "number" ? format.format(value) : value ?? "—";
        const cell = element("td", display);
        if (typeof value === "number") {
          cell.classList.add("numeric");
          cell.title = String(value);
        }
        if (key === "complete" && value === false) cell.className = "incomplete";
        tr.append(cell);
      }
      body.append(tr);
    }
  }
  renderRows();
  table.append(head, body);
  wrap.append(table);
  container.append(wrap);
  if (result.rows.length > pageSize) {
    const pager = element("div", null, "pagination");
    const status = element("span");
    const buttons = element("div");
    const previous = element("button", "Previous", "button secondary");
    const next = element("button", "Next", "button secondary");
    previous.type = next.type = "button";
    function updatePage() {
      renderRows();
      status.textContent = "Rows " + (tablePage * pageSize + 1) + "–" +
        Math.min((tablePage + 1) * pageSize, result.rows.length) + " of " + result.rows.length;
      previous.disabled = tablePage === 0;
      next.disabled = (tablePage + 1) * pageSize >= result.rows.length;
    }
    previous.addEventListener("click", () => { tablePage--; updatePage(); });
    next.addEventListener("click", () => { tablePage++; updatePage(); });
    buttons.append(previous, next);
    pager.append(status, buttons);
    container.append(pager);
    updatePage();
  }
  if (result.deduplicated_measurements) {
    container.append(element("p", format.format(result.deduplicated_measurements) +
      " repeated measurements counted once per " + result.aggregation_grain.map(fieldLabel).join(" and ") + ".", "filter-note"));
  }
  if (result.truncated) container.append(element("p", "Showing the first 100 groups.", "filter-note"));
  return container;
}

function showPlan(detail, plan) {
  detail.hidden = !plan;
  detail.open = false;
  detail.querySelector("pre").textContent = plan ? JSON.stringify(plan, null, 2) : "";
}

function showCalculation(index) {
  if (!report?.results[index]) return;
  $("calculation-select").value = String(index);
  $("results").replaceChildren(resultTable(report.results[index]));
}

function openCalculation(index) {
  showCalculation(index);
  navigate("calculations");
}

function selectedTrend() {
  return report?.results.find(result => result.metric === selectedMetric && result.groups.length === 1 &&
    result.groups[0] === "period" && !["top_n", "bottom_n"].includes(result.operation) &&
    result.rows.some(row => row.value != null));
}

function renderAccountUsage() {
  const result = report?.results.find(item => item.account_usage);
  $("account-usage-panel").hidden = !result;
  if (!result) return;
  const query = $("account-search").value.trim().toLocaleLowerCase();
  const columns = result.display_columns || result.groups;
  const rows = result.rows.filter(row => columns.some(field =>
    String(row[field] ?? "Unassigned").toLocaleLowerCase().includes(query)));
  const pages = Math.max(1, Math.ceil(rows.length / ACCOUNT_PAGE_SIZE));
  accountPage = Math.min(accountPage, pages - 1);
  const start = accountPage * ACCOUNT_PAGE_SIZE;
  const slice = rows.slice(start, start + ACCOUNT_PAGE_SIZE).map(row =>
    Object.fromEntries(Object.entries(row).map(([field, value]) =>
      [field, columns.includes(field) && value == null ? "Unassigned" : value])));
  const table = rows.length
    ? resultTable({ ...result, rows: slice, truncated: false })
    : element("p", "No accounts match your search.", "empty");
  $("account-usage-table").replaceChildren(table);
  $("account-usage-description").textContent = "Grouped by " +
    result.groups.map(fieldLabel).join(" and ") + " · highest usage first";
  $("account-page-status").textContent = rows.length
    ? "Showing " + (start + 1) + "–" + (start + slice.length) + " of " + rows.length +
      " account groups" + (query ? " matching your search" : "")
    : "No accounts match your search.";
  $("account-previous").disabled = accountPage === 0;
  $("account-next").disabled = accountPage + 1 >= pages;
}

$("account-search").addEventListener("input", () => { accountPage = 0; renderAccountUsage(); });
$("account-previous").addEventListener("click", () => { accountPage--; renderAccountUsage(); });
$("account-next").addEventListener("click", () => { accountPage++; renderAccountUsage(); });

function renderRankings() {
  $("rankings").replaceChildren();
  if (!report) return;
  const results = report.results.filter(result => result.metric === selectedMetric && result.groups.length === 1 &&
    result.groups[0] !== "period" && result.rows.some(row => row.value != null));
  const preferred = ["region", "entity"];
  results.sort((a, b) => {
    const rank = item => preferred.includes(item.groups[0]) ? preferred.indexOf(item.groups[0]) : preferred.length;
    return rank(a) - rank(b);
  });
  const seen = new Set();
  for (const result of results) {
    const group = result.groups[0];
    if (seen.has(group)) continue;
    seen.add(group);
    const panel = element("section", null, "panel ranking-panel");
    const header = element("div", null, "panel-head");
    const title = element("div");
    const info = metricInfo(selectedMetric);
    title.append(element("h2", "By " + fieldLabel(group).toLowerCase()),
      element("p", (reductionFor(result) === "mean" ? "Average " : "Total ") +
        fieldLabel(selectedMetric).toLowerCase() + (info.kind === "amount" ? "" : " · " + info.unit)));
    const button = element("button", "View data ↗", "text-button");
    button.addEventListener("click", () => openCalculation(report.results.indexOf(result)));
    header.append(title, button);
    panel.append(header);
    const rows = result.rows.filter(row => row.value != null).slice(0, 5);
    const maximum = Math.max(...rows.map(row => Math.abs(row.value)), 1);
    for (const row of rows) {
      const item = element("div", null, "rank-row");
      const top = element("div", null, "rank-labels");
      const label = element("span", row[group] ?? "Unassigned");
      label.title = row[group] ?? "Unassigned";
      top.append(label, element("strong", formatMetric(row.value, selectedMetric, reductionFor(result))));
      const bar = element("meter");
      bar.min = 0;
      bar.max = maximum;
      bar.value = Math.abs(row.value);
      bar.setAttribute("aria-label", (row[group] ?? "Unassigned") + ": " + format.format(row.value));
      if (row.value < 0) bar.classList.add("negative");
      item.append(top, bar);
      panel.append(item);
    }
    if (rows.some(row => row.value < 0)) panel.append(element("p", "Bars show magnitude; values retain their sign.", "filter-note"));
    $("rankings").append(panel);
    if (seen.size === 2) break;
  }
}

function renderReport(data) {
  report = data;
  $("workspace-empty").hidden = true;
  $("analysis-dashboard").hidden = false;
  $("dataset-status").textContent = "Analysis ready";
  renderQuality(data.quality);
  $("summary").textContent = data.summary
    .replaceAll("Sum of cost was", "Total spend was")
    .replaceAll("Sum of usage was", "Total usage was")
    .replaceAll("Mean of utilization was", "Average utilization was")
    .replaceAll("Highest ranked cost:", "The leading spend group was")
    .replaceAll("mapped measurements", "measurements");
  $("analysis-time").textContent = new Intl.DateTimeFormat(undefined, { timeStyle: "short" }).format(new Date());
  const totals = data.results.filter(item => !item.groups.length && ["sum", "mean"].includes(item.operation));
  const cards = [metricCard("Usable rows", format.format(data.quality.usable_rows), null,
    "of " + format.format(data.quality.input_rows) + " rows uploaded")];
  for (const result of totals.slice(0, 3)) {
    const value = result.rows[0]?.value;
    const trend = data.results.find(item => item.metric === result.metric && item.operation === "week_over_week" &&
      item.groups.length === 1 && item.groups[0] === "period");
    const change = trend?.rows.findLast(row => row.change_pct != null);
    const label = { cost: "Total spend", usage: "Total usage", utilization: "Average utilization" }[result.metric] ||
      (result.operation === "mean" ? "Average " : "Total ") + fieldLabel(result.metric).toLowerCase();
    cards.push(metricCard(label, formatMetric(value, result.metric, result.operation), change, metricInfo(result.metric).unit));
  }
  $("metrics").replaceChildren(...cards);
  $("extra-metrics").replaceChildren();
  for (const result of totals.slice(3)) {
    const item = element("div");
    const value = result.rows[0]?.value;
    const label = element("span", fieldLabel(result.metric));
    label.append(element("small", metricInfo(result.metric).unit));
    item.append(label, element("strong", formatMetric(value, result.metric, result.operation)));
    $("extra-metrics").append(item);
  }
  $("extra-metrics-panel").hidden = totals.length <= 3;
  const metrics = [...new Set(data.results.map(result => result.metric).filter(metric => metric !== "rows"))];
  if (!metrics.includes(selectedMetric)) selectedMetric = metrics.includes("cost") ? "cost" : metrics[0] ?? null;
  $("chart-metric").replaceChildren(...metrics.map(metric => new Option(fieldLabel(metric), metric)));
  $("chart-metric").value = selectedMetric || "";
  $("metric-control").hidden = !metrics.length;
  $("calculation-select").replaceChildren(...data.results.map((result, index) => new Option(calculationLabel(result), index)));
  $("calculation-select").disabled = !data.results.length;
  if (data.results.length) showCalculation(0);
  else $("results").replaceChildren(element("p", "No usable rows remained for calculation.", "empty"));
  showPlan($("report-plan"), data.plan);
  hoverPoint = null;
  accountPage = 0;
  $("account-search").value = "";
  renderAccountUsage();
  renderRankings();
  drawChart();
}

function clearReport() {
  report = null;
  selectedMetric = null;
  hoverPoint = null;
  if (active?.column_inspection?.ready) $("dataset-status").textContent = "Ready to analyze";
  $("metrics").replaceChildren(...["Usable rows", "Total spend", "Total usage", "Average utilization"].map(label => metricCard(label, "—")));
  $("summary").textContent = "Run an analysis to generate a summary.";
  $("analysis-time").textContent = "";
  $("rankings").replaceChildren();
  $("account-usage-panel").hidden = true;
  $("metric-control").hidden = true;
  $("calculation-select").replaceChildren(new Option("No calculations available", ""));
  $("calculation-select").disabled = true;
  $("results").replaceChildren(element("p", "Run an analysis to inspect its results.", "empty"));
  $("extra-metrics-panel").hidden = true;
  showPlan($("report-plan"), null);
  renderQuality(null);
  renderEmptyWorkspace();
  drawChart();
}

function renderEmptyWorkspace() {
  $("workspace-empty").hidden = false;
  $("analysis-dashboard").hidden = true;
  const ready = active?.column_inspection?.ready;
  $("empty-title").textContent = active ? (ready ? "Your dataset is ready" : "Review the detected fields") : "Start with your data";
  $("empty-description").textContent = active
    ? ready ? "Run an analysis to generate totals, trends, and the summary."
      : (active.column_inspection?.blocking_issues?.join(" ") || "No numeric metrics are ready for analysis.")
    : "Upload a CSV to see totals, trends, and data quality in one place.";
  $("empty-action").textContent = active ? (ready ? "Run analysis" : "Review columns") : "Choose CSV";
  $("demo-inline").hidden = Boolean(active);
  $("demo").hidden = !active || active.name === "demo.csv";
  $("upload-help").hidden = Boolean(active);
}

function drawChart() {
  const series = selectedTrend();
  const palette = getComputedStyle(document.documentElement);
  const lineColor = palette.getPropertyValue("--chart-line").trim();
  const warningColor = palette.getPropertyValue("--chart-warning").trim();
  const canvas = $("chart");
  canvas.hidden = !series;
  $("chart-empty").hidden = Boolean(series);
  $("trend-data").disabled = !series;
  $("chart-tooltip").hidden = true;
  $("trend-caption").replaceChildren();
  $("chart-title").textContent = series ? fieldLabel(selectedMetric) + " over time" : "Time trend";
  chartGeometry = [];
  if (!series) {
    $("chart-subtitle").textContent = report ? "No time series was calculated for this metric." : "Run an analysis to explore the timeline.";
    return;
  }
  const rows = series.rows.filter(row => row.value != null);
  const incomplete = rows.some(row => row.complete === false);
  const info = metricInfo(selectedMetric);
  $("chart-subtitle").textContent = { week: "Weekly", month: "Monthly", day: "Daily" }[series.grain] + " " +
    (reductionFor(series) === "mean" ? "average" : "total") +
    (info.kind === "amount" ? " · Amount" : " · " + info.unit);
  const legend = element("span", null, "legend-item");
  legend.append(element("i", null, "legend-dot"), document.createTextNode(fieldLabel(selectedMetric)));
  $("trend-caption").append(legend);
  if (incomplete) {
    const note = element("span", null, "legend-item");
    note.append(element("i", null, "legend-dot amber"), document.createTextNode("Incomplete period"));
    $("trend-caption").append(note);
  }
  const { width, height } = canvas.getBoundingClientRect();
  if (!width || !height) return;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  const left = width < 340 ? 48 : 62;
  const top = 20, bottom = height - 35, right = width - 18;
  const dates = rows.map(row => Date.parse(row.period));
  const low = Math.min(0, ...rows.map(row => row.value));
  const high = Math.max(0, ...rows.map(row => row.value));
  const span = high - low || 1;
  const x = time => dates[0] === dates.at(-1) ? (left + right) / 2
    : left + (right - left) * (time - dates[0]) / (dates.at(-1) - dates[0]);
  const y = value => bottom - (bottom - top) * (value - low) / (span * 1.08);
  ctx.font = "11px Segoe UI, sans-serif";
  const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumSignificantDigits: 3 });
  for (let index = 0; index <= 4; index++) {
    const value = low + span * index / 4;
    ctx.strokeStyle = palette.getPropertyValue("--chart-grid").trim();
    ctx.beginPath();
    ctx.moveTo(left, y(value));
    ctx.lineTo(right, y(value));
    ctx.stroke();
    ctx.fillStyle = palette.getPropertyValue("--chart-label").trim();
    ctx.textBaseline = "middle";
    ctx.fillText(compact.format(value), 1, y(value));
  }
  chartGeometry = rows.map(row => ({ ...row, x: x(Date.parse(row.period)), y: y(row.value) }));
  const segments = [[]];
  chartGeometry.forEach((point, index) => {
    if (series.grain === "week" && index && dates[index] - dates[index - 1] > 604800000) segments.push([]);
    segments.at(-1).push(point);
  });
  const gradient = ctx.createLinearGradient(0, top, 0, bottom);
  gradient.addColorStop(0, lineColor + "24");
  gradient.addColorStop(1, lineColor + "00");
  for (const segment of segments) {
    ctx.beginPath();
    ctx.moveTo(segment[0].x, y(0));
    for (const point of segment) ctx.lineTo(point.x, point.y);
    ctx.lineTo(segment.at(-1).x, y(0));
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.beginPath();
    segment.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  chartGeometry.forEach(point => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, 3.3, 0, Math.PI * 2);
    ctx.fillStyle = point.complete === false ? warningColor : lineColor;
    ctx.fill();
  });
  const labelCount = width < 400 ? 2 : 4;
  const indices = new Set(Array.from({ length: labelCount }, (_, index) => Math.round(index * (rows.length - 1) / (labelCount - 1))));
  const shortDate = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
  ctx.fillStyle = palette.getPropertyValue("--chart-label").trim();
  for (const index of indices) {
    ctx.textAlign = index === 0 ? "left" : index === rows.length - 1 ? "right" : "center";
    ctx.fillText(shortDate.format(new Date(dates[index])), chartGeometry[index].x, bottom + 23);
  }
  if (hoverPoint != null && chartGeometry[hoverPoint]) {
    const point = chartGeometry[hoverPoint];
    ctx.strokeStyle = "#a4b48c";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(point.x, top);
    ctx.lineTo(point.x, bottom);
    ctx.stroke();
    $("chart-tooltip").textContent = periodLabel(point.period) + " · " +
      formatMetric(point.value, selectedMetric, reductionFor(series)) +
      (point.complete === false ? " · incomplete period" : "");
    $("chart-tooltip").hidden = false;
  }
  canvas.setAttribute("aria-label", fieldLabel(selectedMetric) + " over time. Use arrow keys to inspect points, or View data for the table.");
}

$("chart").addEventListener("pointermove", event => {
  if (!chartGeometry.length) return;
  const position = event.clientX - $("chart").getBoundingClientRect().left;
  hoverPoint = chartGeometry.reduce((nearest, point, index) =>
    Math.abs(point.x - position) < Math.abs(chartGeometry[nearest].x - position) ? index : nearest, 0);
  drawChart();
});
$("chart").addEventListener("pointerleave", () => {
  if (document.activeElement !== $("chart")) {
    hoverPoint = null;
    drawChart();
  }
});
$("chart").addEventListener("keydown", event => {
  if (!["ArrowLeft", "ArrowRight"].includes(event.key) || !chartGeometry.length) return;
  event.preventDefault();
  hoverPoint = Math.max(0, Math.min(chartGeometry.length - 1, (hoverPoint ?? 0) + (event.key === "ArrowRight" ? 1 : -1)));
  drawChart();
});
$("chart-metric").addEventListener("change", () => {
  selectedMetric = $("chart-metric").value;
  hoverPoint = null;
  renderRankings();
  drawChart();
});
$("trend-data").addEventListener("click", () => {
  const result = selectedTrend();
  if (result) openCalculation(report.results.indexOf(result));
});
$("calculation-select").addEventListener("change", () => showCalculation(Number($("calculation-select").value)));
window.addEventListener("resize", () => { if (currentView === "overview") drawChart(); });

function renderChatSuggestions() {
  $("chat-suggestions").replaceChildren();
  const registry = active?.column_inspection?.fields || {};
  const questions = [];
  if (registry.cost && registry.region) questions.push("Which region has the highest spend?");
  if (registry.usage && registry.date) questions.push("What was weekly usage?");
  const metric = active?.column_inspection?.metrics?.find(field => !["cost", "usage", "utilization"].includes(field));
  if (metric) questions.push("What was total " + registry[metric].source + "?");
  for (const question of questions.slice(0, 3)) {
    const button = element("button", question, "button secondary");
    button.type = "button";
    button.addEventListener("click", () => { $("question").value = question; $("question").focus(); });
    $("chat-suggestions").append(button);
  }
}

async function analyze(question) {
  const result = await api("analyze", { method: "POST", body: { daily: $("daily").checked, question } });
  if (result.column_inspection) {
    active.column_inspection = result.column_inspection;
    triedMapping = modelEnabled;
    renderMapping();
  }
  return result;
}

async function loadDataset(kind, file) {
  const initial = !active;
  const options = { method: "POST" };
  if (file) {
    options.body = new FormData();
    options.body.set("file", file);
  }
  active = await api(kind, options);
  $("dataset-strip").hidden = false;
  triedMapping = modelEnabled;
  $("dataset-name").textContent = active.name;
  const dateColumn = active.columns.find(item => item.header === active.column_inspection?.mapping.date);
  const range = dateColumn?.profile.date_range;
  $("dataset-meta").textContent = format.format(active.rows) + " rows · " + active.columns.length + " columns" +
    (range ? " · " + range.map(periodLabel).join(" – ") : "");
  $("daily").checked = active.column_inspection?.expected_frequency === "day" || kind === "demo";
  renderMapping();
  clearReport();
  $("conversation").replaceChildren();
  if (!initial) navigate(active.column_inspection?.ready ? "overview" : "mapping");
  if (kind === "demo" && !modelEnabled) renderReport(await analyze());
}

$("file").addEventListener("change", event => {
  const file = event.target.files[0];
  if (file) runTask("Reading CSV…", () => loadDataset("upload", file));
  event.target.value = "";
});
$("demo").addEventListener("click", () => runTask("Loading demo dataset…", () => loadDataset("demo")));
$("demo-inline").addEventListener("click", () => runTask("Loading demo dataset…", () => loadDataset("demo")));
$("empty-action").addEventListener("click", () => {
  if (!active) $("file").click();
  else if (active.column_inspection?.ready) $("run").click();
  else navigate("mapping");
});
for (const eventName of ["dragenter", "dragover"]) {
  $("workspace-empty").addEventListener(eventName, event => {
    if (event.dataTransfer?.types.includes("Files") && !busy) {
      event.preventDefault();
      $("workspace-empty").classList.add("drag-active");
    }
  });
}
$("workspace-empty").addEventListener("dragleave", event => {
  if (!$("workspace-empty").contains(event.relatedTarget)) $("workspace-empty").classList.remove("drag-active");
});
$("workspace-empty").addEventListener("drop", event => {
  event.preventDefault();
  $("workspace-empty").classList.remove("drag-active");
  const file = event.dataTransfer?.files[0];
  if (file && !busy) runTask("Reading CSV…", () => loadDataset("upload", file));
});
$("suggest").addEventListener("click", () => suggest({}));
$("run").addEventListener("click", () => runTask("Validating the plan and calculating results…", async () => {
  const data = await analyze();
  if (data.clarification) throw new Error(data.clarification);
  renderReport(data);
  navigate("overview");
}));
$("daily").addEventListener("change", clearReport);
$("chat-form").addEventListener("submit", event => {
  event.preventDefault();
  const input = $("question");
  const question = input.value.trim();
  if (!question || busy) return;
  runTask("Calculating the answer…", async () => {
    const data = await analyze(question);
    $("conversation").append(element("div", question, "message user"));
    const answer = element("div", null, "message");
    answer.append(element("p", data.clarification || data.summary));
    for (const result of data.results || []) {
      answer.append(element("h3", calculationLabel(result)), resultTable(result));
    }
    if (data.plan) {
      const detail = element("details");
      detail.append(element("summary", "View validated plan"), element("pre"));
      showPlan(detail, data.plan);
      answer.append(detail);
    }
    $("conversation").append(answer);
    $("conversation").scrollTop = $("conversation").scrollHeight;
    input.value = "";
  });
});

const providerLabels = {
  openai: "OpenAI", anthropic: "Claude", gemini: "Gemini", compatible: "Compatible endpoint",
};
let modelSettings = { providers: {}, environment: null, active: null };
let settingsBusy = false;

function applyModel(selection) {
  const changed = JSON.stringify(activeModel) !== JSON.stringify(selection);
  activeModel = selection;
  modelEnabled = Boolean(selection);
  $("mode").textContent = selection ? selection.model : "Local analysis";
  $("mode").title = selection ? selection.destination + " · " + selection.model : "";
  if (changed && active) {
    triedMapping = false;
    active.column_inspection = null;
    renderMapping();
    clearReport();
  }
}

function settingsMessage(message, error = false) {
  const status = $("settings-notice");
  status.hidden = !message;
  status.textContent = message;
  status.classList.toggle("error", error);
}

function showProvider() {
  const id = $("provider").value;
  const provider = modelSettings.providers[id];
  $("endpoint-field").hidden = id !== "compatible";
  $("endpoint").required = id === "compatible";
  $("endpoint").value = provider?.endpoint || "";
  $("provider-key").value = "";
  $("manual-model").value = "";
  $("remove-provider").hidden = !provider;
  $("key-help").textContent = provider?.has_key
    ? "API key saved. Leave blank to reuse it."
    : id === "compatible" ? "Leave blank if the endpoint does not require a key."
      : "Saved in your system credential store.";
}

function modelValue(provider, model) {
  return JSON.stringify([provider, model]);
}

function showSettings(state, highlightProvider) {
  modelSettings = state;
  applyModel(state.active);
  const select = $("saved-model");
  select.replaceChildren(new Option("Local analysis", ""));
  if (state.environment) {
    select.append(new Option("OpenAI · " + state.environment.model + " (environment)",
      modelValue("environment", state.environment.model)));
  }
  for (const [provider, entry] of Object.entries(state.providers)) {
    const group = element("optgroup");
    group.label = providerLabels[provider];
    for (const model of entry.models) group.append(new Option(model, modelValue(provider, model)));
    select.append(group);
  }
  const active = state.active;
  const current = active ? modelValue(active.provider, active.model) : "";
  const highlighted = state.providers[highlightProvider]?.models[0];
  select.value = highlighted && active?.provider !== highlightProvider
    ? modelValue(highlightProvider, highlighted) : current;
  showProvider();
}

async function settingsTask(message, task) {
  if (settingsBusy) return;
  settingsBusy = true;
  const controls = [...$("settings-dialog").querySelectorAll("button, input, select")];
  for (const control of controls) control.disabled = true;
  settingsMessage(message);
  try {
    await task();
  } catch (error) {
    settingsMessage(error.message, true);
  } finally {
    settingsBusy = false;
    for (const control of controls) control.disabled = false;
  }
}

$("model-settings").addEventListener("click", () => {
  $("settings-dialog").showModal();
  settingsTask("Loading saved models…", async () => {
    const state = await api("settings");
    if (state.active?.provider in providerLabels) $("provider").value = state.active.provider;
    showSettings(state);
    settingsMessage("");
  });
});
$("settings-dialog").addEventListener("cancel", event => {
  if (settingsBusy) event.preventDefault();
});
$("settings-dialog").addEventListener("close", () => {
  $("provider-key").value = "";
  settingsMessage("");
});
$("provider").addEventListener("change", showProvider);
$("provider-form").addEventListener("submit", event => {
  event.preventDefault();
  const provider = $("provider").value;
  const body = {
    provider, endpoint: $("endpoint").value, key: $("provider-key").value, model: $("manual-model").value,
  };
  settingsTask("Checking the provider and finding models…", async () => {
    const state = await api("settings/providers", { method: "POST", body });
    showSettings(state, provider);
    settingsMessage("Provider saved. Choose a model and select Use model.");
  });
});
$("model-selection").addEventListener("submit", event => {
  event.preventDefault();
  const [provider, model] = $("saved-model").value ? JSON.parse($("saved-model").value) : [null, null];
  settingsTask("Saving selection…", async () => {
    showSettings(await api("settings/selection", { method: "POST", body: { provider, model } }));
    if (active) {
      const updated = await api("columns", { method: "POST" });
      active = { ...active, ...updated };
      triedMapping = modelEnabled;
      renderMapping();
    }
    settingsMessage(activeModel ? activeModel.model + " is active." : "Local analysis is active.");
  });
});
$("remove-provider").addEventListener("click", () => {
  const provider = $("provider").value;
  if (!window.confirm("Remove " + providerLabels[provider] + " and its saved key?")) return;
  settingsTask("Removing provider…", async () => {
    showSettings(await api("settings/providers/" + provider, { method: "DELETE" }));
    settingsMessage("Provider removed.");
  });
});

showView(currentView);
clearReport();
runTask("Connecting to the workspace…", async () => {
  applyModel((await api("status")).active);
});

