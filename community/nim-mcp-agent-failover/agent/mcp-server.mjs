// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import { pathToFileURL } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod/v4';

export function redact(value, key = '') {
  let text = String(value);
  if (key) text = text.split(key).join('[redacted]');
  return text.replace(/nvapi-[A-Za-z0-9_-]+/g, '[redacted]');
}
const median = (values) => {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};

// Inject the three NIM operations to exercise the actual MCP registrations offline.
export async function createToolServer({ client, config } = {}) {
  if (!client) {
    const { chat, streamChat, listModels, resolveConfig } = await import('../lib/nim.mjs');
    client = { chat, streamChat, listModels };
    config ??= resolveConfig();
  }
  config ??= {};
  const server = new McpServer({ name: 'nim-tools', version: '1.0.0' });
  const result = (value) => ({ content: [{ type: 'text', text: redact(JSON.stringify(value), config.key) }] });
  const failure = (error) => ({
    status: error.status === 410 ? 'end_of_life' : error.status === 429 ? 'rate_limited'
      : [400, 404, 422].includes(error.status) ? 'not_chat' : 'error',
    httpStatus: error.status ?? null, detail: redact(error.detail || error.message, config.key),
  });
  const register = (name, description, inputSchema, handler) => server.registerTool(name,
    { description, inputSchema }, async (args) => {
      try { return result(await handler(args)); }
      catch (error) { return { ...result(failure(error)), isError: true }; }
    });
  register('list_models', 'List the live NIM catalog. Optional id substring filter, e.g. nemotron (not NVIDIA Nemotron); at most 60 ids returned.',
    { filter: z.string().optional() }, async ({ filter = '' }) => {
      const catalog = await client.listModels(config);
      const matches = catalog.map((entry) => entry.id).filter((id) => id.toLowerCase().includes(filter.toLowerCase()));
      return { ids: matches.slice(0, 60), total: catalog.length, matched: matches.length };
    });
  register('check_model', 'Probe a model with a tiny chat. Reports alive, HTTP 410 end of life, rate limit, or failure.',
    { model: z.string().min(1) }, async ({ model }) => {
      const start = performance.now();
      try {
        await client.chat({ ...config, model, messages: [{ role: 'user', content: 'Say OK.' }], maxTokens: 16 });
        return { model, status: 'alive', httpStatus: 200, detail: 'Chat completion succeeded.', latencyMs: performance.now() - start };
      } catch (error) { return { model, ...failure(error), latencyMs: performance.now() - start }; }
    });
  register('measure_model', 'Measure 1 to 3 short streams. Compare median TTFT and tokens per second; this is a small sample, not a universal ranking.',
    { model: z.string().min(1), runs: z.number().int().optional() }, async ({ model, runs = 2 }) => {
      const samples = [], errors = [];
      for (let i = 0; i < Math.max(1, Math.min(3, runs)); i++) {
        try { samples.push(await client.streamChat({ ...config, model, prompt: 'Explain what an API is in two short sentences.', maxTokens: 96 })); }
        catch (error) { errors.push(failure(error)); if (error.status === 410) break; }
      }
      return { model, medianTtftMs: median(samples.map((s) => s.ttftMs)),
        medianTokensPerSecond: median(samples.map((s) => s.tokPerSec)), okCount: samples.length,
        tokensEstimated: samples.some((s) => s.tokensEstimated), errors };
    });
  register('supports_tools', 'Probe actual function calling with a required ping tool. True means a well formed ping call was returned.',
    { model: z.string().min(1) }, async ({ model }) => {
      const tool = { type: 'function', function: { name: 'ping', description: 'Return the supplied value.',
        parameters: { type: 'object', properties: { value: { type: 'string' } }, required: ['value'], additionalProperties: false } } };
      try {
        const response = await client.chat({ ...config, model, maxTokens: 1024,
          messages: [{ role: 'user', content: 'Call ping with value OK.' }], tools: [tool],
          toolChoice: { type: 'function', function: { name: 'ping' } } });
        const supported = response.message?.tool_calls?.some((call) => {
          try {
            const args = JSON.parse(call.function.arguments);
            return call.id && call.type === 'function' && call.function.name === 'ping' && args &&
              typeof args.value === 'string' && Object.keys(args).length === 1;
          } catch { return false; }
        }) ?? false;
        return { model, supportsTools: Boolean(supported), detail: supported ? 'Well formed ping call returned.' : 'No valid ping call returned by this probe.' };
      } catch (error) { return { model, supportsTools: false, ...failure(error) }; }
    });
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const server = await createToolServer();
    await server.connect(new StdioServerTransport());
    for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, async () => { await server.close(); process.exit(0); });
  } catch (error) {
    console.error(`NIM tools: ${redact(error.message, process.env.NVIDIA_API_KEY)}`);
    process.exitCode = 1;
  }
}
