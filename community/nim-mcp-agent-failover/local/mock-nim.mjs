// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import http from 'node:http';
import { pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const ids = ['fast', 'slow', 'busy', 'retired', 'flaky'].map(name => `mock/${name}`);

// Synthetic usage counts describe mock chunks, not tokens from a real tokenizer.
export async function startMock({ port = 8089, host = '127.0.0.1', slowMs = 400,
  tokenDelayMs = 10, flakyRate = 0.5, seed = 1 } = {}) {
  if (![slowMs, tokenDelayMs].every(n => Number.isFinite(n) && n >= 0) ||
      !Number.isFinite(flakyRate) || flakyRate < 0 || flakyRate > 1 || !Number.isInteger(seed)) {
    throw new Error('Use non-negative delays, flakyRate between 0 and 1, and an integer seed.');
  }
  const faults = new Map();
  let counts = Object.create(null), state = seed >>> 0, serial = 0;
  const server = http.createServer(async (req, res) => {
    res.setHeader('x-mock-nim', '1');
    const json = (status, body, type = 'application/json') => {
      res.writeHead(status, { 'content-type': type });
      res.end(JSON.stringify(body));
    };
    const record = (model, status) => {
      counts[model] ??= {};
      counts[model][status] = (counts[model][status] || 0) + 1;
    };
    const fail = (model, status) => {
      record(model, status);
      if (status === 429) res.setHeader('retry-after', '2');
      if (status === 410) return json(410, { type: 'about:blank', title: 'Gone', status: 410,
        detail: `The model '${model}' has reached its end of life on 2026-01-01T00:00:00Z and is no longer available.` }, 'application/problem+json');
      json(status, { error: { message: `Mock failure (${status}); no model is running.`, type: 'mock_error', code: status } });
    };
    try {
      const path = new URL(req.url, 'http://mock').pathname;
      if (req.method === 'GET' && path === '/v1/models') return json(200, {
        object: 'list', data: ids.map(id => ({ id, object: 'model', created: 0, owned_by: 'mock' })) });
      if (req.method === 'GET' && path === '/__mock/stats') return json(200, { requests: counts });
      if (req.method !== 'POST') return json(404, { error: { message: 'Unknown mock endpoint' } });
      let raw = '';
      for await (const chunk of req) {
        raw += chunk;
        if (raw.length > 1_000_000) return json(413, { error: { message: 'Request too large' } });
      }
      let body;
      try { body = JSON.parse(raw || '{}'); } catch { return json(400, { error: { message: 'Invalid JSON' } }); }
      if (!body || typeof body !== 'object' || Array.isArray(body)) return json(400, { error: { message: 'Expected an object' } });
      if (path === '/__mock/reset') {
        faults.clear(); counts = Object.create(null); state = seed >>> 0; serial = 0;
        return json(200, { reset: true });
      }
      if (path === '/__mock/fail') {
        if (!ids.includes(body.model) || !Number.isInteger(body.status) || body.status < 400 || body.status > 599 ||
            !Number.isInteger(body.count) || body.count < 0) return json(400, { error: { message: 'Use a known model, status 400..599, and non-negative integer count' } });
        faults.set(body.model, { status: body.status, count: body.count });
        return json(200, { model: body.model, status: body.status, count: body.count });
      }
      if (path !== '/v1/chat/completions') return json(404, { error: { message: 'Unknown mock endpoint' } });
      const model = body.model;
      if (!ids.includes(model)) return fail(String(model), 404);
      if (!Array.isArray(body.messages) || !body.messages.length || body.messages.some(m => !m || typeof m.role !== 'string')) {
        return fail(model, 400);
      }
      const fault = faults.get(model);
      if (fault?.count > 0) { fault.count--; return fail(model, fault.status); }
      if (model === 'mock/busy') return fail(model, 429);
      if (model === 'mock/retired') return fail(model, 410);
      if (model === 'mock/flaky') {
        state = (Math.imul(1664525, state) + 1013904223) >>> 0;
        if (state / 4294967296 < flakyRate) return fail(model, 503);
      }
      const last = body.messages.at(-1);
      let message = { role: 'assistant', content: 'This is a mock response. No model is running.' };
      let finish = 'stop';
      if (last.role === 'tool') message.content = `Mock tool result: ${JSON.stringify(String(last.content).slice(0, 160))}. No model is running.`;
      else if (last.role === 'user' && Array.isArray(body.tools) && body.tools.length) {
        const fn = body.tools[0]?.function;
        if (!fn || typeof fn.name !== 'string') return fail(model, 400);
        const args = {};
        for (const key of fn.parameters?.required || []) {
          if (fn.parameters?.properties?.[key]?.type === 'string') Object.defineProperty(args, key, { value: 'demo', enumerable: true });
        }
        message = { role: 'assistant', content: null, tool_calls: [{ id: 'call_mock_1', type: 'function',
          function: { name: fn.name, arguments: JSON.stringify(args) } }] };
        finish = 'tool_calls';
      }
      if (model === 'mock/slow') await delay(slowMs);
      if (res.destroyed) return;
      record(model, 200);
      const envelope = { id: `chatcmpl-mock-${++serial}`, created: 0, model };
      const pieces = message.content?.match(/\S+\s*/g) || [];
      const usage = { prompt_tokens: 1, completion_tokens: pieces.length || 1, total_tokens: (pieces.length || 1) + 1 };
      if (!body.stream) return json(200, { ...envelope, object: 'chat.completion',
        choices: [{ index: 0, message, finish_reason: finish }], usage });
      res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' });
      const send = data => res.write(`data: ${JSON.stringify({ ...envelope, object: 'chat.completion.chunk', ...data })}\n\n`);
      const choice = (delta, finish_reason = null) => ({ choices: [{ index: 0, delta, finish_reason }] });
      send(choice({ role: 'assistant', content: '' }));
      if (message.tool_calls) send(choice({ tool_calls: message.tool_calls.map((call, index) => ({ index, ...call })) }));
      for (const piece of pieces) {
        if (res.destroyed) return;
        send(choice({ content: piece }));
        if (tokenDelayMs) await delay(tokenDelayMs);
      }
      if (res.destroyed) return;
      send(choice({}, finish));
      if (body.stream_options?.include_usage) send({ choices: [], usage });
      res.end('data: [DONE]\n\n');
    } catch {
      if (!res.headersSent) json(500, { error: { message: 'Mock request failed' } });
      else res.end();
    }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, host, resolve); });
  let closing;
  return { server, base: `http://${host}:${server.address().port}/v1`, close() {
    closing ??= new Promise((resolve, reject) => {
      server.close(error => error ? reject(error) : resolve());
      server.closeAllConnections();
    });
    return closing;
  } };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const options = {};
    const flags = { '--port': 'port', '--slow-ms': 'slowMs', '--token-delay-ms': 'tokenDelayMs' };
    for (let i = 2; i < process.argv.length; i += 2) {
      const key = flags[process.argv[i]], value = Number(process.argv[i + 1]);
      if (!key || !Number.isInteger(value) || value < 0 || (key === 'port' && value > 65535)) throw new Error('Usage: node local/mock-nim.mjs [--port 8089] [--slow-ms 400] [--token-delay-ms 10]');
      options[key] = value;
    }
    const mock = await startMock(options);
    console.log(`MOCK NIM at ${mock.base}. No model is running. Offline canned responses only.`);
    for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, () => mock.close());
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
