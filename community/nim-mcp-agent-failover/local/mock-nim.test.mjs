// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import { startMock } from './mock-nim.mjs';

async function setup(t, options = {}) {
  const mock = await startMock({ port: 0, tokenDelayMs: 0, ...options });
  t.after(() => mock.close());
  const post = (path, body) => fetch(`${mock.base.replace(/\/v1$/, '')}${path}`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  const chat = (model = 'mock/fast', extra = {}) => post('/v1/chat/completions', {
    model, messages: [{ role: 'user', content: 'Hello' }], ...extra });
  return { ...mock, post, chat };
}

function events(text) {
  assert.ok(text.endsWith('data: [DONE]\n\n'));
  return text.trim().split('\n\n').slice(0, -1).map(line => {
    assert.ok(line.startsWith('data: '));
    return JSON.parse(line.slice(6));
  });
}

test('fake catalog and non-streaming fast completion', async t => {
  const m = await setup(t);
  const response = await fetch(`${m.base}/models`);
  assert.equal(response.headers.get('x-mock-nim'), '1');
  const catalog = await response.json();
  assert.deepEqual(catalog.data.map(x => x.id), ['mock/fast', 'mock/slow', 'mock/busy', 'mock/retired', 'mock/flaky']);
  assert.ok(catalog.data.every(x => x.owned_by === 'mock' && x.object === 'model'));
  const result = await m.chat();
  assert.equal(result.status, 200);
  const body = await result.json();
  assert.equal(body.object, 'chat.completion');
  assert.equal(body.choices[0].message.content, 'This is a mock response. No model is running.');
  assert.equal(body.choices[0].finish_reason, 'stop');
  assert.ok(body.usage.completion_tokens > 0);
});

test('SSE chunks, final usage and DONE; usage is opt-in', async t => {
  const m = await setup(t, { tokenDelayMs: 2 });
  for (const include_usage of [true, false]) {
    const r = await m.chat('mock/fast', { stream: true, stream_options: { include_usage } });
    assert.match(r.headers.get('content-type'), /text\/event-stream/);
    assert.equal(r.headers.get('x-mock-nim'), '1');
    const chunks = events(await r.text());
    assert.ok(chunks.every(c => c.object === 'chat.completion.chunk' && c.model === 'mock/fast' && c.id === chunks[0].id));
    assert.equal(chunks[0].choices[0].delta.role, 'assistant');
    assert.equal(chunks.flatMap(c => c.choices).map(c => c.delta.content || '').join(''), 'This is a mock response. No model is running.');
    if (include_usage) {
      assert.deepEqual(chunks.at(-1).choices, []);
      assert.equal(chunks.at(-1).usage.total_tokens, chunks.at(-1).usage.completion_tokens + 1);
      assert.equal(chunks.at(-2).choices[0].finish_reason, 'stop');
    } else {
      assert.ok(chunks.every(c => !c.usage));
      assert.equal(chunks.at(-1).choices[0].finish_reason, 'stop');
    }
  }
});

test('slow defaults to a 400 ms wait before the first token', async t => {
  const m = await setup(t);
  const start = performance.now();
  const r = await m.chat('mock/slow', { stream: true });
  const reader = r.body.getReader();
  await reader.read();
  assert.ok(performance.now() - start >= 380);
  await reader.cancel();
});

test('slow delay is configurable', async t => {
  const m = await setup(t, { slowMs: 25 });
  const start = performance.now();
  assert.equal((await m.chat('mock/slow')).status, 200);
  assert.ok(performance.now() - start >= 20);
});

test('busy retries, retired RFC 7807, and unknown model', async t => {
  const m = await setup(t);
  for (let i = 0; i < 2; i++) {
    const busy = await m.chat('mock/busy');
    assert.equal(busy.status, 429);
    assert.equal(busy.headers.get('retry-after'), '2');
    assert.equal(busy.headers.get('x-mock-nim'), '1');
  }
  const gone = await m.chat('mock/retired');
  assert.equal(gone.status, 410);
  assert.equal(gone.headers.get('content-type'), 'application/problem+json');
  assert.deepEqual(await gone.json(), { type: 'about:blank', title: 'Gone', status: 410,
    detail: "The model 'mock/retired' has reached its end of life on 2026-01-01T00:00:00Z and is no longer available." });
  assert.equal((await m.chat('mock/missing')).status, 404);
});

test('seeded flaky sequences repeat and rate extremes work', async t => {
  const a = await setup(t, { seed: 42, flakyRate: 0.5 });
  const b = await setup(t, { seed: 42, flakyRate: 0.5 });
  const sequence = async m => {
    const statuses = [];
    for (let i = 0; i < 10; i++) statuses.push((await m.chat('mock/flaky')).status);
    return statuses;
  };
  const expected = await sequence(a);
  assert.deepEqual(await sequence(b), expected);
  assert.ok(expected.includes(503) && expected.includes(200));
  await a.post('/__mock/reset', {});
  assert.deepEqual(await sequence(a), expected);
  const all = await setup(t, { flakyRate: 1 });
  const none = await setup(t, { flakyRate: 0 });
  assert.equal((await all.chat('mock/flaky')).status, 503);
  assert.equal((await none.chat('mock/flaky')).status, 200);
});

test('fault injection countdown, stats, reset and validation', async t => {
  const m = await setup(t);
  assert.equal((await m.post('/__mock/fail', { model: 'mock/fast', status: 429, count: 3 })).status, 200);
  for (let i = 0; i < 3; i++) {
    const r = await m.chat();
    assert.equal(r.status, 429);
    assert.equal(r.headers.get('retry-after'), '2');
  }
  assert.equal((await m.chat()).status, 200);
  let stats = await (await fetch(m.base.replace('/v1', '/__mock/stats'))).json();
  assert.deepEqual(stats.requests['mock/fast'], { 200: 1, 429: 3 });
  await m.post('/__mock/fail', { model: 'mock/fast', status: 503, count: 9 });
  await m.post('/__mock/reset', {});
  stats = await (await fetch(m.base.replace('/v1', '/__mock/stats'))).json();
  assert.deepEqual(stats.requests, {});
  assert.equal((await m.chat()).status, 200);
  assert.equal((await m.post('/__mock/fail', { model: 'mock/fast', status: 200, count: -1 })).status, 400);
});

test('first tool call builds required strings then quotes the tool result', async t => {
  const m = await setup(t);
  const tools = [{ type: 'function', function: { name: 'lookup', parameters: { type: 'object',
    required: ['query', 'count'], properties: { query: { type: 'string' }, count: { type: 'number' }, optional: { type: 'string' } } } } },
  { type: 'function', function: { name: 'ignored' } }];
  const call = await (await m.chat('mock/fast', { tools })).json();
  assert.equal(call.choices[0].finish_reason, 'tool_calls');
  const message = call.choices[0].message;
  const tool = message.tool_calls[0];
  assert.equal(message.content, null);
  assert.equal(tool.type, 'function');
  assert.equal(tool.function.name, 'lookup');
  assert.deepEqual(JSON.parse(tool.function.arguments), { query: 'demo' });
  const done = await (await m.chat('mock/fast', { tools, messages: [
    { role: 'user', content: 'look up' }, message, { role: 'tool', tool_call_id: tool.id, content: 'Found demo record' }] })).json();
  assert.match(done.choices[0].message.content, /Mock tool result: "Found demo record"/);
  assert.equal(done.choices[0].finish_reason, 'stop');
  const streamed = events(await (await m.chat('mock/fast', { tools, stream: true })).text());
  const delta = streamed.flatMap(c => c.choices).find(c => c.delta.tool_calls).delta.tool_calls[0];
  assert.equal(delta.index, 0);
  assert.deepEqual(JSON.parse(delta.function.arguments), { query: 'demo' });
  assert.equal(streamed.at(-1).choices[0].finish_reason, 'tool_calls');
});

test('invalid requests and missing routes retain the mock header', async t => {
  const m = await setup(t);
  const bad = await fetch(`${m.base}/chat/completions`, { method: 'POST', body: '{' });
  assert.equal(bad.status, 400);
  assert.equal(bad.headers.get('x-mock-nim'), '1');
  assert.equal((await m.chat('mock/fast', { messages: [] })).status, 400);
  assert.equal((await fetch(`${m.base}/missing`)).status, 404);
});

test('close is clean and idempotent, releasing the port', async () => {
  const m = await startMock({ port: 0 });
  const port = m.server.address().port;
  await m.close();
  await m.close();
  assert.equal(m.server.listening, false);
  const probe = net.createServer();
  await new Promise((resolve, reject) => { probe.once('error', reject); probe.listen(port, '127.0.0.1', resolve); });
  await new Promise(resolve => probe.close(resolve));
});
