#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { writeFile } from 'node:fs/promises';
import { NimError, PREFERRED_MODELS, resolveConfig, listModels, chat, streamChat } from '../lib/nim.mjs';

export class Router {
  constructor({ ranked, parkMs = 60000, now = () => Date.now() }) {
    Object.assign(this, { ranked: [...ranked], parkMs, now });
    this.parkedUntil = new Map();
    this.gone = new Set();
    this.log = [];
  }
  async run(fn) {
    let lastError;
    for (const model of this.ranked) {
      if (this.gone.has(model)) { this.log.push({ model, skipped: 'gone' }); continue; }
      if ((this.parkedUntil.get(model) ?? -Infinity) > this.now()) {
        this.log.push({ model, skipped: 'parked' }); continue;
      }
      try {
        const out = await fn(model);
        this.log.push({ model, served: true });
        return out;
      } catch (error) {
        lastError = error;
        if (error instanceof NimError && error.gone) {
          this.gone.add(model);
          this.log.push({ model, error: error.status, gone: true });
        } else if (error instanceof NimError && error.retryable) {
          this.parkedUntil.set(model, this.now() + (error.retryAfterMs ?? this.parkMs));
          this.log.push({ model, error: error.status ?? error.message, parked: true });
        } else { throw error; }
      }
    }
    throw new Error(`No model is available: all models are parked, gone or failing.${lastError ? ` ${lastError.message}` : ''}`);
  }
}

async function limited(items, concurrency, fn) {
  if (!Number.isInteger(concurrency) || concurrency < 1) throw new Error('concurrency must be a positive integer');
  const results = new Array(items.length);
  let cursor = 0;
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (cursor < items.length) { const index = cursor++; results[index] = await fn(items[index]); }
  }));
  return results;
}

// Server error text can carry account ids and long traces. Keep it short and anonymous.
const tidy = (text) => String(text).replace(/account '[^']*'/g, "account '<redacted>'").replace(/\s+/g, ' ').slice(0, 120);

export async function probe({ base, key, models, concurrency = 6, call = chat }) {
  const catalog = models ?? (await listModels({ base, key })).map((m) => m.id);
  return limited(catalog, concurrency, async (item) => {
    const model = typeof item === 'string' ? item : item.id;
    try {
      await call({ base, key, model, messages: [{ role: 'user', content: 'Say hi.' }], maxTokens: 16, timeoutMs: 60000 });
      return { model, status: 'chat' };
    } catch (error) {
      if (!(error instanceof NimError)) throw error;
      const status = error.gone ? 'gone' : error.status === 429 ? 'rate-limited'
        : error.status >= 400 && error.status < 500 ? 'not-chat' : 'error';
      return { model, status, httpStatus: error.status, detail: tidy(error.detail ?? error.message) };
    }
  });
}

const median = (values) => {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  const n = sorted.length;
  return n ? (sorted[Math.floor((n - 1) / 2)] + sorted[Math.floor(n / 2)]) / 2 : null;
};
const min = (values) => values.length ? Math.min(...values) : null;
const max = (values) => values.length ? Math.max(...values) : null;
export async function bench({ base, key, models, prompt, runs = 5, maxTokens = 256,
  temperature = 0.2, timeoutMs = 120000, concurrency = 3, call = streamChat }) {
  if (!Number.isInteger(runs) || runs < 1) throw new Error('runs must be a positive integer');
  return limited(models, concurrency, async (model) => {
    const samples = [], errors = [], rawRuns = [];
    let gone = false;
    for (let run = 0; run < runs; run++) {
      try {
        const out = await call({ base, key, model, prompt, maxTokens, temperature, timeoutMs });
        // Keep measurements, not completion text, in benchmark records.
        const { ttftMs, totalMs, outTokens, tokensEstimated, tokPerSec } = out;
        const sample = { run: run + 1, ok: true, ttftMs, totalMs, outTokens, tokensEstimated, tokPerSec };
        samples.push(sample); rawRuns.push(sample);
      } catch (error) {
        if (!(error instanceof NimError)) throw error;
        errors.push(error.status ?? tidy(error.message));
        rawRuns.push({ run: run + 1, ok: false, status: error.status, detail: tidy(error.detail ?? error.message) });
        if (error.gone) { gone = true; break; }
      }
    }
    const ttfts = samples.map((s) => s.ttftMs).filter(Number.isFinite);
    const rates = samples.map((s) => s.tokPerSec).filter(Number.isFinite);
    return { model, runs, ok: samples.length, gone, errors, rawRuns,
      ttftMs: median(ttfts), ttftMinMs: min(ttfts), ttftMaxMs: max(ttfts),
      tokPerSec: median(rates), tokPerSecMin: min(rates), tokPerSecMax: max(rates),
      totalMs: median(samples.map((s) => s.totalMs)), outTokens: median(samples.map((s) => s.outTokens)),
      tokensEstimated: samples.some((s) => s.tokensEstimated) };
  });
}
export function rank(results) {
  return results.filter((r) => r.ok > 0)
    .sort((a, b) => (a.ttftMs ?? Infinity) - (b.ttftMs ?? Infinity)).map((r) => r.model);
}
const cell = (value) => String(value).replace(/\|/g, '\\|').replace(/[\r\n]+/g, ' ');
const number = (value, digits = 0) => Number.isFinite(value) ? value.toFixed(digits) : '-';
export function table(results) {
  return [
    '| model | ok | median TTFT ms | TTFT min to max | median tok/s | tok/s min to max | median total ms | median out tokens | errors |',
    '|---|---|---|---|---|---|---|---|---|',
    ...results.map((r) => `| ${cell(r.model)} | ${r.ok}/${r.runs} | ${number(r.ttftMs)} | ${number(r.ttftMinMs)} to ${number(r.ttftMaxMs)} | ${number(r.tokPerSec, 1)} | ${number(r.tokPerSecMin, 1)} to ${number(r.tokPerSecMax, 1)} | ${number(r.totalMs)} | ${number(r.outTokens, 1)}${r.tokensEstimated ? ' (estimated)' : ''} | ${cell(r.errors.join(', ') || '-')} |`),
  ].join('\n');
}

function positive(value, name) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1) throw new Error(`${name} must be a positive integer`);
  return n;
}
async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    base: { type: 'string' }, models: { type: 'string' }, probe: { type: 'boolean' },
    'all-chat': { type: 'boolean' }, 'no-bench': { type: 'boolean' }, prompt: { type: 'string' },
    runs: { type: 'string' }, 'max-tokens': { type: 'string', default: '256' },
    'timeout-ms': { type: 'string', default: '120000' }, concurrency: { type: 'string' }, out: { type: 'string' }, label: { type: 'string' },
  } });
  const command = positionals[0];
  if (!['models', 'bench', 'route'].includes(command) || positionals.length !== 1) {
    throw new Error('Usage: node router/nim-route.mjs models|bench|route [--base URL] [options]');
  }
  const { base, key } = resolveConfig({ ...process.env, ...(values.base ? { NIM_BASE_URL: values.base } : {}) });
  const catalog = await listModels({ base, key });
  const ids = new Set(catalog.map((m) => m.id));
  if (command === 'models') {
    if (!values.probe) { for (const model of catalog) console.log(model.id); return; }
    const results = await probe({ base, key, models: catalog, concurrency: positive(values.concurrency ?? 6, 'concurrency') });
    console.log(['| model | http | status | detail |', '|---|---|---|---|',
      ...results.map((r) => `| ${cell(r.model)} | ${r.httpStatus ?? '-'} | ${r.status} | ${cell(r.detail ?? '-')} |`)].join('\n'));
    return;
  }
  let wanted = values.models ? values.models.split(',').map((s) => s.trim()).filter(Boolean) : PREFERRED_MODELS;
  if (values['all-chat']) wanted = (await probe({ base, key, models: catalog })).filter((r) => r.status === 'chat').map((r) => r.model);
  const missing = wanted.filter((model) => !ids.has(model));
  if (missing.length) console.warn(`Skipped (not listed in catalog): ${missing.join(', ')}`);
  const models = wanted.filter((model) => ids.has(model));
  if (!models.length) throw new Error('No requested models are listed. Run models to see the current catalog.');
  const settings = { runs: positive(values.runs ?? (command === 'route' ? 2 : 5), 'runs'),
    maxTokens: positive(values['max-tokens'], 'max-tokens'), temperature: 0.2,
    prompt: values.prompt ?? 'In three sentences, explain why KV-cache size limits batch size during LLM inference.',
    concurrency: positive(values.concurrency ?? 3, 'concurrency'), timeoutMs: positive(values['timeout-ms'], 'timeout-ms') };
  let ranked;
  if (command === 'route' && values['no-bench']) {
    if (!values.models) throw new Error('--no-bench requires --models in ranked order.');
    ranked = models;
  } else {
    const results = await bench({ base, key, models, ...settings });
    if (results.every((r) => r.ok === 0 && r.rawRuns.every((run) => [401, 403].includes(run.status)))) {
      throw new NimError('NVIDIA API key is missing or wrong. Visit https://build.nvidia.com.', { status: 401 });
    }
    console.log(table(results));
    if (values.out) {
      const record = { kit: 'nim-mcp-agent-failover', date: new Date().toISOString(), base: values.label ?? (new URL(base).hostname === 'integrate.api.nvidia.com' ? new URL(base).host : 'local'),
        node: process.version, platform: process.platform, settings, results };
      await writeFile(values.out, `${JSON.stringify(record, null, 2)}\n`);
    }
    ranked = rank(results.filter((r) => !r.gone));
  }
  if (command === 'bench') return;
  if (!ranked.length) throw new Error('No model answered the benchmark. Run models --probe to check availability.');
  const router = new Router({ ranked });
  const out = await router.run(async (model) => {
    let started = false;
    try { return await streamChat({ base, key, model, ...settings, onToken: (text) => { started = true; process.stdout.write(text); } }); }
    catch (error) {
      if (started && error instanceof NimError && (error.retryable || error.gone)) console.error(`\n[${model} failed, failing over]`);
      throw error;
    }
  });
  console.log(`\nServed by ${out.model}: TTFT ${number(out.ttftMs)} ms, ${number(out.tokPerSec, 1)} tok/s${out.tokensEstimated ? ' (estimated)' : ''}`);
  console.log('Route log:', JSON.stringify(router.log));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    const message = error instanceof NimError && [401, 403].includes(error.status)
      ? 'NVIDIA API key is missing or wrong. Set NVIDIA_API_KEY with a key from https://build.nvidia.com.'
      : error instanceof NimError && error.gone
        ? `${error.model}: model is end of life. Run models to choose a current model. ${error.detail ?? ''}` : error.message;
    console.error(message);
    process.exitCode = 1;
  });
}
