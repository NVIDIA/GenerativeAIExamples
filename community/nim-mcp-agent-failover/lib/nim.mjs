// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
export const DEFAULT_BASE = 'https://integrate.api.nvidia.com/v1';
export const PREFERRED_MODELS = [
  'nvidia/nemotron-3.5-bolt-e4b',
  'nvidia/nemotron-3.5-lightning-30b-a3b',
  'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning',
];

export function resolveConfig(env = process.env) {
  const base = (env.NIM_BASE_URL || DEFAULT_BASE).replace(/\/+$/, '');
  const key = env.NVIDIA_API_KEY || '';
  if (new URL(base).hostname === 'integrate.api.nvidia.com' && !key) {
    throw new NimError('NVIDIA API key is missing or wrong. Set NVIDIA_API_KEY with a key from https://build.nvidia.com.', { status: 401 });
  }
  return { base, key, model: env.NIM_MODEL || null };
}

export class NimError extends Error {
  constructor(message, { status = null, model = null, detail = null, retryAfterMs, cause } = {}) {
    super(message, { cause });
    this.name = 'NimError';
    Object.assign(this, { status, model, detail, gone: status === 410,
      retryable: status === null || status === 429 || (status >= 500 && status < 600) });
    if (retryAfterMs !== undefined) this.retryAfterMs = retryAfterMs;
  }
}

const headers = (key) => ({ ...(key ? { authorization: `Bearer ${key}` } : {}), 'content-type': 'application/json' });
async function request({ base, key, model = null, timeoutMs }, path, body) {
  try {
    const res = await fetch(`${base.replace(/\/+$/, '')}${path}`, {
      method: body ? 'POST' : 'GET', headers: headers(key),
      signal: AbortSignal.timeout(timeoutMs), ...(body ? { body: JSON.stringify(body) } : {}),
    });
    if (!res.ok) {
      const raw = await res.text();
      let detail = null;
      try { const parsed = JSON.parse(raw); detail = parsed.detail ?? parsed.error?.message ?? null; } catch { /* Plain text errors are also allowed. */ }
      const seconds = res.headers.get('retry-after');
      const retryAfterMs = res.status === 429 && seconds !== null && Number.isFinite(Number(seconds))
        ? Math.max(0, Number(seconds) * 1000) : undefined;
      throw new NimError(`${model || path}: HTTP ${res.status}${detail || raw ? `: ${detail || raw.slice(0, 300)}` : ''}`,
        { status: res.status, model, detail, retryAfterMs });
    }
    return res;
  } catch (error) {
    if (error instanceof NimError) throw error;
    throw transportError(error, model, base);
  }
}
function transportError(error, model, base) {
  const timeout = error.name === 'TimeoutError' || error.name === 'AbortError';
  return new NimError(`${model || 'NIM'}: ${timeout ? 'request timed out' : `network request failed; check NIM_BASE_URL (${new URL(base).host})`}`, { model, cause: error });
}

export async function listModels({ base, key, timeoutMs = 15000 }) {
  const res = await request({ base, key, timeoutMs }, '/models');
  try { return (await res.json()).data; } catch (error) { throw transportError(error, null, base); }
}
export async function pickModel({ base, key, preferred = PREFERRED_MODELS }) {
  const ids = new Set((await listModels({ base, key })).map((m) => m.id));
  const model = preferred.find((id) => ids.has(id));
  if (!model) throw new Error('No preferred model is listed. Run models and choose a current model.');
  return model;
}
export async function chat({ base, key, model, messages, tools, toolChoice, maxTokens = 1024, temperature = 0.2, timeoutMs = 120000 }) {
  const start = performance.now();
  const res = await request({ base, key, model, timeoutMs }, '/chat/completions', {
    model, messages, ...(tools ? { tools } : {}), ...(toolChoice ? { tool_choice: toolChoice } : {}),
    max_tokens: maxTokens, temperature, stream: false,
  });
  let data;
  try { data = await res.json(); } catch (error) { throw transportError(error, model, base); }
  return { model: data.model || model, message: data.choices?.[0]?.message,
    finishReason: data.choices?.[0]?.finish_reason, usage: data.usage, totalMs: performance.now() - start };
}

export async function streamChat({ base, key, model, messages, prompt, maxTokens = 256, temperature = 0.2, timeoutMs = 120000, onToken }) {
  const start = performance.now();
  const res = await request({ base, key, model, timeoutMs }, '/chat/completions', {
    model, messages: messages ?? [{ role: 'user', content: prompt }], max_tokens: maxTokens, temperature,
    stream: true, stream_options: { include_usage: true },
  });
  let text = '', reasoning = '', ttftMs = null, usage = null, chunks = 0, buffer = '', done = false;
  let callbackError;
  const decoder = new TextDecoder();
  function line(raw) {
    const trimmed = raw.trim();
    if (!trimmed.startsWith('data:')) return;
    const data = trimmed.slice(5).trim();
    if (!data) return;
    if (data === '[DONE]') { done = true; return; }
    let event;
    try { event = JSON.parse(data); }
    catch (cause) { throw new NimError('stream parse error', { model, cause }); }
    if (event.error) throw new NimError(event.error.message || 'stream error', {
      model, status: typeof event.error.code === 'number' && Number.isFinite(event.error.code) ? event.error.code : null,
    });
    if (event.usage) usage = event.usage;
    const delta = event.choices?.[0]?.delta;
    if (delta?.content || delta?.reasoning_content) {
      ttftMs ??= performance.now() - start;
      chunks++;
      if (delta.reasoning_content) reasoning += delta.reasoning_content;
      if (delta.content) {
        text += delta.content;
        try { onToken?.(delta.content); } catch (error) { callbackError = error; throw error; }
      }
    }
  }
  try {
    for await (const part of res.body) {
      buffer += decoder.decode(part, { stream: true });
      let pos;
      while (!done && (pos = buffer.indexOf('\n')) >= 0) {
        line(buffer.slice(0, pos)); buffer = buffer.slice(pos + 1);
      }
      if (done) break;
    }
    if (!done) line(buffer + decoder.decode());
  } catch (error) {
    if (error === callbackError) throw error;
    if (error.name === 'TimeoutError' || error.name === 'AbortError' || error instanceof TypeError) throw transportError(error, model, base);
    throw error;
  }
  const totalMs = performance.now() - start;
  const outTokens = usage?.completion_tokens ?? chunks;
  return { model, text, reasoning, ttftMs, totalMs, outTokens,
    tokensEstimated: usage?.completion_tokens == null,
    tokPerSec: ttftMs === null || totalMs - ttftMs < 50 ? null : outTokens / ((totalMs - ttftMs) / 1000) };
}
