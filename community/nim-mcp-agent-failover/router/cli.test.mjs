// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export function run(command, args, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { env: { ...process.env, NVIDIA_API_KEY: '', ...env } });
    let stdout = '', stderr = '';
    child.stdout.on('data', (part) => { stdout += part; });
    child.stderr.on('data', (part) => { stderr += part; });
    child.on('error', reject);
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}
async function server(t, handler) {
  const s = http.createServer(async (req, res) => {
    if (req.url === '/models') return res.end(JSON.stringify({ data: [{ id: 'first' }, { id: 'second' }] }));
    let raw = ''; for await (const part of req) raw += part;
    handler(JSON.parse(raw), res);
  });
  await new Promise((r) => s.listen(0, '127.0.0.1', r));
  t.after(() => { s.closeAllConnections(); s.close(); });
  return `http://127.0.0.1:${s.address().port}`;
}
const delta = (text) => `data: ${JSON.stringify({ choices: [{ delta: { content: text } }] })}\n\n`;
for (const status of [401, 403]) test(`bench all HTTP ${status} failures reports friendly key error before table`, async (t) => {
  const base = await server(t, (_, res) => { res.writeHead(status); res.end('Authorization failed'); });
  const out = await run(process.execPath, ['router/nim-route.mjs', 'bench', '--base', base, '--models', 'first,second', '--runs', '1']);
  assert.equal(out.code, 1); assert.match(out.stderr, /key is missing or wrong.*https:\/\/build.nvidia.com/);
  assert.equal(out.stdout, '');
});
test('route marks partial output before socket failure failover', async (t) => {
  const base = await server(t, ({ model }, res) => {
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write(delta(model === 'first' ? 'partial' : 'complete'));
    if (model === 'first') setTimeout(() => res.destroy(), 40);
    else res.end('data: [DONE]\n\n');
  });
  const out = await run(process.execPath, ['router/nim-route.mjs', 'route', '--base', base, '--models', 'first,second', '--no-bench']);
  assert.equal(out.code, 0); assert.match(out.stdout, /partialcomplete/);
  assert.match(out.stderr, /\n\[first failed, failing over\]/);
  assert.match(out.stdout, /- tok\/s/);
});
test('benchmark JSON uses local label or explicit override', async (t) => {
  const base = await server(t, (_, res) => res.end(delta('hi') + 'data: [DONE]\n'));
  const dir = await mkdtemp(join(tmpdir(), 'nim-label-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  for (const label of [undefined, 'local-mlx']) {
    const path = join(dir, 'result.json');
    const out = await run(process.execPath, ['router/nim-route.mjs', 'bench', '--base', base, '--models', 'first', '--runs', '1', '--out', path, ...(label ? ['--label', label] : [])]);
    assert.equal(out.code, 0);
    const record = await readFile(path, 'utf8');
    assert.equal(JSON.parse(record).base, label ?? 'local');
    assert.doesNotMatch(record, /127\.0\.0\.1/);
  }
});
test('network error identifies base host and NIM_BASE_URL', async () => {
  const out = await run(process.execPath, ['router/nim-route.mjs', 'models', '--base', 'http://127.0.0.1:1']);
  assert.equal(out.code, 1); assert.match(out.stderr, /NIM_BASE_URL.*127\.0\.0\.1:1/);
});

for (const status of [401, 403]) test(`agent prints friendly credential guidance for HTTP ${status}`, async (t) => {
  const s = http.createServer((req, res) => { res.writeHead(status); res.end('Authorization failed'); });
  await new Promise((r) => s.listen(0, '127.0.0.1', r));
  t.after(() => { s.closeAllConnections(); s.close(); });
  const out = await run(process.execPath, ['agent/agent.mjs', '--base', `http://127.0.0.1:${s.address().port}`, 'hi']);
  assert.equal(out.code, 1);
  assert.match(out.stderr, /key is missing or wrong.*https:\/\/build.nvidia.com/);
});
