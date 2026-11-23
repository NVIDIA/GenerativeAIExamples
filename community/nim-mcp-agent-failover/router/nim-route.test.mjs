// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { NimError, streamChat } from '../lib/nim.mjs';
import { Router, probe, bench, rank, table } from './nim-route.mjs';

async function mock(t) {
  const seen = [];
  const server = http.createServer(async (req, res) => {
    let raw = ''; for await (const part of req) raw += part;
    const body = JSON.parse(raw); const { model } = body; seen.push(body);
    const status = { busy: 429, bad: 400, gone: 410, fail: 503 }[model];
    if (status) { res.writeHead(status); res.end(JSON.stringify({ detail: model === 'gone' ? 'End of life.' : model })); return; }
    if (model === 'slow') await new Promise((r) => setTimeout(r, 60));
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    if (!body.stream) { res.end(JSON.stringify({ choices: [{ message: { content: 'hi' } }] })); return; }
    for (const word of ['hello ', 'from ', model]) res.write(`data: ${JSON.stringify({ choices: [{ delta: { content: word } }] })}\n\n`);
    res.end('data: {"usage":{"completion_tokens":3},"choices":[]}\n\ndata: [DONE]\n\n');
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  t.after(() => { server.closeAllConnections(); server.close(); });
  return { base: `http://127.0.0.1:${server.address().port}`, seen };
}

test('bench + rank order by TTFT and retain raw successes and errors', async (t) => {
  const { base } = await mock(t);
  const results = await bench({ base, models: ['slow', 'busy', 'fast'], prompt: 'hi', runs: 2 });
  assert.deepEqual(rank(results), ['fast', 'slow']);
  assert.deepEqual(results[1].errors, [429, 429]);
  assert.equal(results[0].rawRuns.length, 2);
  assert.equal(results[0].outTokens, 3); assert.equal(results[0].tokensEstimated, false);
  assert.ok(results[0].ttftMinMs <= results[0].ttftMs && results[0].ttftMs <= results[0].ttftMaxMs);
  assert.match(table(results), /median TTFT ms/);
});

test('Router parks 429 then retries after expiry', async (t) => {
  const { base } = await mock(t);
  let now = 0;
  const router = new Router({ ranked: ['busy', 'fast'], parkMs: 1000, now: () => now });
  const fn = (model) => streamChat({ base, model, prompt: 'hi' });
  assert.equal((await router.run(fn)).model, 'fast');
  await router.run(fn);
  assert.deepEqual(router.log.map((l) => l.skipped ?? l.error ?? 'served'), [429, 'served', 'parked', 'served']);
  now = 2000; await router.run(fn); assert.equal(router.log.at(-2).error, 429);
});

test('410 drops a model permanently and stops its benchmark runs', async (t) => {
  const { base, seen } = await mock(t);
  let now = 0;
  const router = new Router({ ranked: ['gone', 'fast'], parkMs: 1, now: () => now });
  const fn = (model) => streamChat({ base, model, prompt: 'hi' });
  await router.run(fn); now = 100000; await router.run(fn);
  assert.equal(seen.filter((r) => r.model === 'gone').length, 1);
  assert.equal(router.log.at(-2).skipped, 'gone');
  const result = (await bench({ base, models: ['gone'], runs: 5, prompt: 'hi' }))[0];
  assert.equal(result.gone, true); assert.deepEqual(result.errors, [410]); assert.equal(result.rawRuns.length, 1);
  assert.equal(seen.filter((r) => r.model === 'gone').length, 2);
});

test('Retry-After controls parking instead of parkMs', async () => {
  let now = 0, attempts = 0;
  const router = new Router({ ranked: ['busy', 'fast'], parkMs: 10, now: () => now });
  const fn = async (model) => { if (model === 'busy') { attempts++; throw new NimError('busy', { status: 429, retryAfterMs: 2000 }); } return model; };
  await router.run(fn); now = 100; await router.run(fn); assert.equal(attempts, 1);
  now = 2000; await router.run(fn); assert.equal(attempts, 2);
});

test('400 and non-NimError rethrow without failover', async (t) => {
  const { base, seen } = await mock(t);
  const router = new Router({ ranked: ['bad', 'fast'] });
  await assert.rejects(router.run((model) => streamChat({ base, model, prompt: 'hi' })), (e) => e.status === 400);
  assert.deepEqual(seen.map((r) => r.model), ['bad']);
  const bug = new Error('bug'); let calls = 0;
  await assert.rejects(router.run(async () => { calls++; throw bug; }), (e) => e === bug);
  assert.equal(calls, 1);
});

test('probe classifies chat, gone, rate limit, other 4xx and 5xx', async (t) => {
  const { base, seen } = await mock(t);
  const results = await probe({ base, models: ['fast', 'gone', 'busy', 'bad', 'fail'], concurrency: 2 });
  assert.deepEqual(results.map((r) => r.status), ['chat', 'gone', 'rate-limited', 'not-chat', 'error']);
  assert.equal(results[1].detail, 'End of life.'); assert.ok(seen.every((r) => r.max_tokens === 16));
  const timeout = await probe({ models: ['timeout'], call: async () => { throw new NimError('timeout'); } });
  assert.equal(timeout[0].status, 'error');
});

test('bench bounds concurrency and runs each model sequentially', async () => {
  let active = 0, peak = 0;
  const perModel = new Set();
  const results = await bench({ models: ['a', 'b', 'c'], runs: 3, concurrency: 2, call: async ({ model }) => {
    assert.equal(perModel.has(model), false); perModel.add(model); active++; peak = Math.max(peak, active);
    await new Promise((r) => setTimeout(r, 5)); active--; perModel.delete(model);
    return { ttftMs: 2, totalMs: 8, outTokens: 3, tokPerSec: 500, tokensEstimated: true };
  } });
  assert.equal(peak, 2); assert.ok(results.every((r) => r.ok === 3 && r.tokensEstimated));
});

test('Router fails over retryable network and server errors and reports exhaustion', async () => {
  const router = new Router({ ranked: ['network', 'server', 'ok'] });
  assert.equal(await router.run(async (model) => {
    if (model !== 'ok') throw new NimError('failure', { status: model === 'network' ? null : 503 });
    return model;
  }), 'ok');
  await assert.rejects(new Router({ ranked: [] }).run(() => {}), /No model is available/);
});

test('bench redacts and bounds raw error details and tolerates null rates', async () => {
  const results = await bench({ models: ['error', 'short'], runs: 1, call: async ({ model }) => {
    if (model === 'error') throw new NimError('failure', { status: 500, detail: "account 'private-id' " + 'x'.repeat(500) });
    return { ttftMs: 1, totalMs: 2, tokPerSec: null };
  } });
  assert.doesNotMatch(JSON.stringify(results), /private-id/);
  assert.ok(results[0].rawRuns[0].detail.length <= 120);
  assert.equal(results[1].tokPerSec, null);
  assert.match(table(results), /\| - \| - to - \|/);
});

test('bench also redacts transport error messages stored in errors', async () => {
  const results = await bench({ models: ['offline'], runs: 1, call: async () => { throw new NimError("account 'private-id' refused"); } });
  assert.doesNotMatch(JSON.stringify(results), /private-id/);
});
