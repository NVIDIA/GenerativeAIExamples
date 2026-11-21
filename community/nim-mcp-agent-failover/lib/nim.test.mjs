// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { DEFAULT_BASE, resolveConfig, NimError, listModels, pickModel, chat, streamChat } from './nim.mjs';

async function mock(t, handler) {
  const server = http.createServer(handler);
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => { server.closeAllConnections(); server.close(); });
  return `http://127.0.0.1:${server.address().port}`;
}
const input = { model: 'test', prompt: 'hi', key: '' };
const event = (delta) => `data: ${JSON.stringify({ choices: [{ delta }] })}\r\n\r\n`;

test('resolveConfig validates NVIDIA key and supports local bases', () => {
  assert.throws(() => resolveConfig({}), /key.*missing.*build.nvidia.com/i);
  assert.deepEqual(resolveConfig({ NVIDIA_API_KEY: 'test' }), { base: DEFAULT_BASE, key: 'test', model: null });
  assert.deepEqual(resolveConfig({ NIM_BASE_URL: 'http://localhost:8000/v1///', NIM_MODEL: 'local' }),
    { base: 'http://localhost:8000/v1', key: '', model: 'local' });
});

test('listModels sends no authorization when key is empty; pickModel intersects in preference order', async (t) => {
  const base = await mock(t, (req, res) => {
    assert.equal(req.headers.authorization, undefined);
    res.end(JSON.stringify({ data: [{ id: 'a' }, { id: 'c' }] }));
  });
  assert.deepEqual(await listModels({ base, key: '' }), [{ id: 'a' }, { id: 'c' }]);
  assert.equal(await pickModel({ base, key: '', preferred: ['gone', 'c', 'a'] }), 'c');
  await assert.rejects(pickModel({ base, preferred: ['gone'] }), /No preferred model/);
});

test('chat preserves tool_calls and sends the documented request fields', async (t) => {
  const message = { role: 'assistant', content: null, tool_calls: [{ id: '1', type: 'function', function: { name: 'lookup', arguments: '{}' } }] };
  const base = await mock(t, async (req, res) => {
    let raw = ''; for await (const part of req) raw += part;
    const body = JSON.parse(raw);
    assert.equal(req.headers.authorization, 'Bearer test');
    assert.equal(body.tool_choice, 'auto'); assert.equal(body.max_tokens, 1024);
    res.end(JSON.stringify({ model: 'test', choices: [{ message, finish_reason: 'tool_calls' }], usage: { completion_tokens: 4 } }));
  });
  const result = await chat({ base, key: 'test', model: 'test', messages: [], tools: [], toolChoice: 'auto' });
  assert.deepEqual(result.message, message); assert.equal(result.finishReason, 'tool_calls');
  assert.equal(result.usage.completion_tokens, 4); assert.ok(result.totalMs >= 0);
});

test('HTTP errors parse RFC 7807 detail and Retry-After seconds', async (t) => {
  const base = await mock(t, (req, res) => {
    const gone = req.url === '/models';
    res.writeHead(gone ? 410 : 429, { 'retry-after': '2.5' });
    res.end(JSON.stringify({ detail: gone ? 'Model is end of life.' : 'Busy.' }));
  });
  await assert.rejects(listModels({ base }), (e) => e instanceof NimError && e.gone && !e.retryable && e.detail === 'Model is end of life.');
  await assert.rejects(chat({ base, ...input }), (e) => e.status === 429 && e.retryAfterMs === 2500 && e.retryable);
});

test('streamChat parses split SSE, reasoning, keepalives, usage and final DONE without newline', async (t) => {
  const base = await mock(t, async (req, res) => {
    let raw = ''; for await (const part of req) raw += part;
    assert.equal(JSON.parse(raw).stream_options.include_usage, true);
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    const data = '\n: keepalive\n\ndata:\n' + event({ reasoning_content: 'thinking' }) + event({ content: 'hello ' }) + event({ content: 'world' })
      + 'data: {"usage":{"completion_tokens":9},"choices":[]}\n\ndata: [DONE]';
    for (let i = 0; i < data.length; i += 7) { res.write(data.slice(i, i + 7)); await new Promise((r) => setTimeout(r, 1)); }
    await new Promise((r) => setTimeout(r, 60));
    res.end();
  });
  const tokens = [];
  const out = await streamChat({ base, ...input, onToken: (token) => tokens.push(token) });
  assert.equal(out.text, 'hello world'); assert.equal(out.reasoning, 'thinking');
  assert.deepEqual(tokens, ['hello ', 'world']); assert.equal(out.outTokens, 9);
  assert.equal(out.tokensEstimated, false); assert.ok(out.ttftMs > 0 && out.ttftMs <= out.totalMs);
  assert.ok(out.tokPerSec > 0);
});

test('streamChat estimates tokens when usage is missing', async (t) => {
  const base = await mock(t, (req, res) => res.end(event({ reasoning_content: 'think' }) + event({ content: 'hi' }) + 'data: [DONE]\n'));
  const out = await streamChat({ base, ...input });
  assert.equal(out.outTokens, 2); assert.equal(out.tokensEstimated, true);
});

test('network failures and timeouts are retryable NimErrors for every request type', async (t) => {
  const base = await mock(t, () => {});
  for (const call of [listModels, chat, streamChat]) {
    await assert.rejects(call({ base, ...input, timeoutMs: 15 }), (e) => e instanceof NimError && e.status === null && e.retryable);
    await assert.rejects(call({ base: 'http://127.0.0.1:1', ...input }), (e) => e instanceof NimError && e.status === null && e.retryable);
  }
});

test('streaming body timeouts are retryable', async (t) => {
  const base = await mock(t, (req, res) => { res.writeHead(200); res.write(event({ content: 'hi' })); });
  await assert.rejects(streamChat({ base, ...input, timeoutMs: 30 }), (e) => e instanceof NimError && e.status === null && e.retryable);
});

test('streamChat preserves callback errors as caller errors', async (t) => {
  const base = await mock(t, (req, res) => res.end(event({ content: 'hi' }) + 'data: [DONE]\n'));
  const error = new TypeError('caller bug');
  await assert.rejects(streamChat({ base, ...input, onToken() { throw error; } }), (e) => e === error);
});

test('malformed stream JSON is a retryable model error', async (t) => {
  const base = await mock(t, (req, res) => res.end('data: {bad}\n'));
  await assert.rejects(streamChat({ base, ...input }), (e) =>
    e instanceof NimError && e.status === null && e.retryable && e.model === 'test' && /stream parse error/.test(e.message));
});

for (const code of [403, '403', undefined]) test(`in-stream errors retain message and numeric status: ${code}`, async (t) => {
  const base = await mock(t, (req, res) => res.end(`data: ${JSON.stringify({ error: { message: 'stream refused', code } })}\n`));
  await assert.rejects(streamChat({ base, ...input }), (e) =>
    e instanceof NimError && e.message === 'stream refused' && e.model === 'test' &&
    e.status === (typeof code === 'number' ? code : null));
});

test('single-chunk generation has no meaningful token rate', async (t) => {
  const base = await mock(t, (req, res) => res.end(event({ content: 'hi' }) + 'data: [DONE]\n'));
  assert.equal((await streamChat({ base, ...input })).tokPerSec, null);
});
