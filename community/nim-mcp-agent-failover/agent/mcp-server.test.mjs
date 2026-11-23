// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createToolServer } from './mcp-server.mjs';

async function roundTrip(t, overrides = {}) {
  const invocations = [];
  const client = {
    listModels: async () => Array.from({ length: 70 }, (_, i) => ({ id: `test/model-${i}` })),
    chat: async (options) => { invocations.push(options); return { message: { tool_calls: [
      { id: 'ping1', type: 'function', function: { name: 'ping', arguments: '{"value":"OK"}' } },
    ] } }; },
    streamChat: async (options) => { invocations.push(options); return { ttftMs: invocations.length * 10, tokPerSec: invocations.length * 2, tokensEstimated: true }; },
    ...overrides,
  };
  const server = await createToolServer({ client, config: { key: 'private-test-value', base: 'http://offline/v1' } });
  const connection = new Client({ name: 'test', version: '1' });
  const [left, right] = InMemoryTransport.createLinkedPair();
  await server.connect(left); await connection.connect(right);
  t.after(async () => { await connection.close(); await server.close(); });
  return { connection, invocations, call: async (name, args) => {
    const result = await connection.callTool({ name, arguments: args });
    return JSON.parse(result.content[0].text);
  } };
}

test('in-memory MCP registers all tools with required model schema', async (t) => {
  const { connection } = await roundTrip(t);
  const { tools } = await connection.listTools();
  assert.deepEqual(tools.map((tool) => tool.name), ['list_models', 'check_model', 'measure_model', 'supports_tools']);
  assert.deepEqual(tools.find((tool) => tool.name === 'check_model').inputSchema.required, ['model']);
});

test('list models caps 60 and reports total plus filtered matches', async (t) => {
  const { call } = await roundTrip(t);
  const all = await call('list_models', {});
  assert.equal(all.ids.length, 60); assert.equal(all.total, 70);
  const filtered = await call('list_models', { filter: 'MODEL-69' });
  assert.deepEqual(filtered.ids, ['test/model-69']); assert.equal(filtered.matched, 1);
});

test('check model tiny chat returns alive and latency', async (t) => {
  const { call, invocations } = await roundTrip(t);
  const result = await call('check_model', { model: 'demo' });
  assert.equal(result.status, 'alive'); assert.equal(result.httpStatus, 200); assert.ok(result.latencyMs >= 0);
  assert.equal(invocations[0].maxTokens, 16);
});

for (const [status, expected] of [[410, 'end_of_life'], [429, 'rate_limited'], [400, 'not_chat'], [500, 'error']]) {
  test(`check model classifies HTTP ${status}, retaining safe detail`, async (t) => {
    const { call } = await roundTrip(t, { chat: async () => { throw Object.assign(new Error('fallback'), { status, detail: 'End of life private-test-value' }); } });
    const result = await call('check_model', { model: 'demo' });
    assert.equal(result.status, expected); assert.equal(result.httpStatus, status);
    assert.equal(result.detail, 'End of life [redacted]');
  });
}

test('measure clamps runs to three and computes medians', async (t) => {
  const { call, invocations } = await roundTrip(t);
  const result = await call('measure_model', { model: 'demo', runs: 20 });
  assert.equal(invocations.length, 3); assert.equal(result.okCount, 3);
  assert.equal(result.medianTtftMs, 20); assert.equal(result.medianTokensPerSecond, 4);
  assert.equal(result.tokensEstimated, true); assert.ok(invocations.every((item) => item.maxTokens === 96));
});

test('measure default two, minimum one and partial failure', async (t) => {
  let count = 0;
  const { call } = await roundTrip(t, { streamChat: async () => {
    if (!count++) throw Object.assign(new Error('Busy'), { status: 429 });
    return { ttftMs: 12, tokPerSec: 34, tokensEstimated: false };
  } });
  const result = await call('measure_model', { model: 'demo' });
  assert.equal(count, 2); assert.equal(result.okCount, 1); assert.equal(result.errors[0].status, 'rate_limited');
  assert.equal(result.medianTtftMs, 12); assert.equal(result.tokensEstimated, false);
  await call('measure_model', { model: 'demo', runs: 0 }); assert.equal(count, 3);
});

test('measure all failures has null medians rather than invented numbers', async (t) => {
  const { call } = await roundTrip(t, { streamChat: async () => { throw new Error('offline'); } });
  const result = await call('measure_model', { model: 'demo' });
  assert.equal(result.okCount, 0); assert.equal(result.medianTtftMs, null); assert.equal(result.medianTokensPerSecond, null);
});

test('tool probe requires an actual well formed function call', async (t) => {
  const { call, invocations } = await roundTrip(t);
  assert.equal((await call('supports_tools', { model: 'demo' })).supportsTools, true);
  assert.equal(invocations[0].toolChoice.function.name, 'ping');
  assert.ok(invocations[0].maxTokens >= 1024);
});

for (const argumentsText of ['{', '{}', '{"value":1}']) test(`invalid tool probe args ${argumentsText} returns false`, async (t) => {
  const { call } = await roundTrip(t, { chat: async () => ({ message: { tool_calls: [
    { id: 'x', type: 'function', function: { name: 'ping', arguments: argumentsText } },
  ] } }) });
  assert.equal((await call('supports_tools', { model: 'demo' })).supportsTools, false);
});

test('SDK rejects missing required fields over actual transport', async (t) => {
  const { connection } = await roundTrip(t);
  const result = await connection.callTool({ name: 'check_model', arguments: {} });
  assert.equal(result.isError, true); assert.match(result.content[0].text, /model/);
});

test('measure stops permanently on 410 instead of retrying a retired model', async (t) => {
  let requests = 0;
  const { call } = await roundTrip(t, { streamChat: async () => {
    requests++; throw Object.assign(new Error('retired'), { status: 410 });
  } });
  const result = await call('measure_model', { model: 'retired', runs: 3 });
  assert.equal(requests, 1); assert.equal(result.errors[0].status, 'end_of_life');
});

test('measure preserves unavailable rates for short streams', async (t) => {
  const { call } = await roundTrip(t, { streamChat: async () => ({ ttftMs: 10, tokPerSec: null }) });
  const result = await call('measure_model', { model: 'short' });
  assert.equal(result.okCount, 2);
  assert.equal(result.medianTokensPerSecond, null);
});
