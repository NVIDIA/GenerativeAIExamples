// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
// Node >= 20. Run: node quickstart/node/quickstart.mjs
const base = (process.env.NIM_BASE_URL || 'https://integrate.api.nvidia.com/v1').replace(/\/+$/, '');
const key = process.env.NVIDIA_API_KEY || '';
const preferred = ['nvidia/nemotron-3.5-bolt-e4b', 'nvidia/nemotron-3.5-lightning-30b-a3b',
  'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning'];

async function request(path, body) {
  const response = await fetch(`${base}${path}`, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json', ...(key ? { Authorization: `Bearer ${key}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(Number(process.env.NIM_TIMEOUT_SECONDS || 120) * 1000),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 410) throw new Error(`410: ${error.detail || 'Model reached end of life.'} Pick another model from /v1/models.`);
    if ([401, 403].includes(response.status)) throw new Error('401: Check NVIDIA_API_KEY or your server credentials.');
    if (response.status === 429) throw new Error('429: Rate limit reached. Wait before trying again.');
    if (response.status === 404) throw new Error('404: Model not found. Pick a chat model from /v1/models.');
    throw new Error(`HTTP ${response.status}: Request failed. Check the server and model.`);
  }
  return response;
}

async function main() {
  if (new URL(base).hostname === 'integrate.api.nvidia.com' && !key) {
    throw new Error('Set NVIDIA_API_KEY first. Get a free key at https://build.nvidia.com.');
  }
  const catalog = await (await request('/models')).json();
  const ids = catalog.data.map(model => model.id);
  const model = process.env.NIM_MODEL || preferred.find(id => ids.includes(id));
  if (!model) throw new Error(`Set NIM_MODEL to a chat model from /v1/models. Catalog: ${ids.slice(0, 8).join(', ')}`);
  const start = performance.now();
  let first;
  const response = await request('/chat/completions', {
    model, messages: [{ role: 'user', content: 'Say hello in one short sentence.' }],
    max_tokens: 512, stream: true,
  });
  // SSE events can span network chunks and contain multiple data lines.
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let pending = '', data = [], done = false;
  function line(text) {
    if (text.startsWith('data:')) data.push(text.slice(5).replace(/^ /, ''));
    if (text !== '' || !data.length) return;
    const payload = data.join('\n');
    data = [];
    if (payload === '[DONE]') { done = true; return; }
    const chunk = JSON.parse(payload);
    if (chunk.error) throw new Error('Stream returned an error. Try another chat model.');
    const delta = chunk.choices?.[0]?.delta;
    const token = delta?.content || delta?.reasoning_content || '';
    if (token) { first ??= performance.now(); process.stdout.write(token); }
  }
  try {
    while (!done) {
      const chunk = await reader.read();
      if (chunk.done) break;
      pending += chunk.value;
      // Keep a trailing CR until the next chunk, in case it begins with LF.
      let match;
      while ((match = /\r\n|\n|\r(?!$)/.exec(pending))) {
        line(pending.slice(0, match.index));
        pending = pending.slice(match.index + match[0].length);
        if (done) break;
      }
    }
    if (!done) { if (pending) line(pending.replace(/\r$/, '')); line(''); }
  } finally { await reader.cancel(); }
  if (first === undefined) throw new Error('No text returned. Try another chat model or raise max_tokens for reasoning models.');
  console.log(`\nmodel=${model} ttft_ms=${Math.round(first - start)} total_ms=${Math.round(performance.now() - start)}`);
}
main().catch(error => {
  console.error(error instanceof TypeError || error.name === 'TimeoutError'
    ? 'Request failed. Check NIM_BASE_URL, connectivity and NIM_TIMEOUT_SECONDS.' : error.message);
  process.exitCode = 1;
});
