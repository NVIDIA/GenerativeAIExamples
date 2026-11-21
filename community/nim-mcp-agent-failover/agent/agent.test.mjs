// SPDX-FileCopyrightText: Copyright (c) 2026 Jeremy Schoemaker
// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { runAgent, mcpToolsToOpenAI, splitCommand, connectMcp, mcpEnvironment, agentExitCode } from './agent.mjs';

import { Router } from '../router/nim-route.mjs';
import { NimError } from '../lib/nim.mjs';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';

const tools = mcpToolsToOpenAI([{ name: 'check', description: 'Check a model', inputSchema: {
  type: 'object', properties: { model: { type: 'string' } }, required: ['model'], additionalProperties: false,
} }]);
const call = (name = 'check', args = '{"model":"demo"}', id = 'c1') => ({ id, type: 'function', function: { name, arguments: args } });
const reply = (calls, content = null) => ({ message: { role: 'assistant', content, ...(calls ? { tool_calls: calls } : {}) } });
const fakeRouter = () => ({ log: [], async run(fn) { this.log.push({ model: 'fake', served: true }); return fn('fake'); } });
const options = (chatFn, extra = {}) => ({ question: 'test', tools, chatFn, router: fakeRouter(), callTool: async () => 'alive', ...extra });

test('two tool calls preserve ids, history, durations, trace and final answer', async () => {
  const events = [], seen = []; let turn = 0;
  const result = await runAgent(options(async ({ messages, maxTokens, model }) => {
    assert.ok(maxTokens >= 1024); assert.equal(model, 'fake');
    if (turn++ === 0) return reply([call('check', '{"model":"a"}', 'a'), call('check', '{"model":"b"}', 'b')]);
    assert.deepEqual(messages.filter((m) => m.role === 'tool').map((m) => m.tool_call_id), ['a', 'b']);
    assert.equal(messages[0].role, 'system');
    return reply(null, 'Both models are alive.');
  }, { onEvent: (event) => events.push(event), callTool: async (name, args) => { seen.push([name, args]); return 'alive'; } }));
  assert.equal(result.answer, 'Both models are alive.');
  assert.equal(result.steps, 2); assert.equal(result.toolCalls.length, 2);
  assert.ok(result.toolCalls.every((item) => item.durationMs >= 0));
  assert.equal(events.length, 4); assert.equal(seen.length, 2);
  assert.deepEqual(result.modelsUsed, ['fake']); assert.equal(result.routeLog.length, 2);
});

for (const [label, request, expected] of [
  ['unknown tool', call('missing'), /Unknown tool/],
  ['invalid JSON', call('check', '{'), /not valid JSON/],
  ['missing required field', call('check', '{}'), /missing required field: model/],
  ['null arguments', call('check', 'null'), /JSON object/],
  ['wrong field type', call('check', '{"model":3}'), /must be a string/],
  ['extra property', call('check', '{"model":"x","other":true}'), /unknown field/],
]) test(`tool floor: ${label} becomes a correctable tool result`, async () => {
  let count = 0, executed = false;
  const result = await runAgent(options(async ({ messages }) => {
    if (!count++) return reply([request]);
    assert.match(messages.at(-1).content, expected);
    return reply(null, 'Corrected.');
  }, { callTool: async () => { executed = true; } }));
  assert.equal(executed, false); assert.equal(result.answer, 'Corrected.');
});

test('tool floor: thrown errors are returned and secrets are redacted', async () => {
  let turn = 0;
  const result = await runAgent(options(async ({ messages }) => {
    if (!turn++) return reply([call()]);
    assert.match(messages.at(-1).content, /bad \[redacted\]/);
    return reply(null, 'Could not verify.');
  }, { config: { key: 'private-test-value' }, callTool: async () => { throw new Error('bad private-test-value'); } }));
  assert.doesNotMatch(JSON.stringify(result), /private-test-value/);
});

test('tool floor: oversized results are bounded before history and trace', async () => {
  let turn = 0;
  const result = await runAgent(options(async ({ messages }) => {
    if (!turn++) return reply([call()]);
    assert.ok(messages.at(-1).content.length <= 6000);
    assert.match(messages.at(-1).content, /truncated/);
    return reply(null, 'Done');
  }, { callTool: async () => 'x'.repeat(20000) }));
  assert.ok(result.toolCalls[0].result.length <= 6000);
});

test('tool floor: third consecutive identical call stops before execution', async () => {
  let executions = 0;
  const result = await runAgent(options(async () => reply([call()]), { callTool: async () => { executions++; return 'ok'; } }));
  assert.equal(executions, 2); assert.equal(result.stopped, 'repeated_tool');
  assert.match(result.answer, /three times/);
});

test('identical JSON arguments with different key order still repeat', async () => {
  const flexible = mcpToolsToOpenAI([{ name: 'check', inputSchema: { type: 'object' } }]);
  let turn = 0;
  const result = await runAgent(options(async () => reply([call('check', ++turn % 2 ? '{"a":1,"b":2}' : '{"b":2,"a":1}')]), { tools: flexible }));
  assert.equal(result.stopped, 'repeated_tool');
});

test('different intervening call resets consecutive repetition counter', async () => {
  let turn = 0;
  const result = await runAgent(options(async () => ++turn === 5 ? reply(null, 'Done') : reply([call('check', JSON.stringify({ model: turn === 3 ? 'other' : 'demo' }))])));
  assert.equal(result.answer, 'Done'); assert.equal(result.toolCalls.length, 4);
});

test('step limit returns structured result and reasoning-only content is tolerated', async () => {
  let turns = 0;
  const result = await runAgent(options(async ({ messages }) => {
    if (turns++) assert.match(messages.at(-1).content, /final visible answer/);
    return { message: { content: null, reasoning_content: 'thinking' } };
  }, { maxSteps: 2 }));
  assert.equal(turns, 2);
  assert.equal(result.steps, 2); assert.equal(result.stopped, 'step_limit'); assert.match(result.answer, /Step limit reached/);
});

test('each turn uses the injected router and fails over mid-conversation', async () => {
  const log = []; let turns = 0;
  const router = { log, async run(fn) {
    try { return await fn('first'); }
    catch (error) { if (!error.retryable) throw error; log.push({ model: 'first', parked: true }); return fn('second'); }
  } };
  const result = await runAgent(options(async ({ model }) => {
    if (turns++ === 0) return reply([call()]);
    if (model === 'first') throw Object.assign(new Error('429'), { retryable: true });
    return reply(null, 'Recovered with tool history.');
  }, { router }));
  assert.deepEqual(result.modelsUsed, ['first', 'second']); assert.equal(result.routeLog[0].parked, true);
});

test('MCP schema conversion preserves description and JSON schema', () => {
  assert.equal(tools[0].function.name, 'check'); assert.equal(tools[0].function.description, 'Check a model');
  assert.deepEqual(tools[0].function.parameters.required, ['model']);
});

test('command parser supports spaces, quoted arguments and no shell expansion', () => {
  assert.deepEqual(splitCommand('node "a b.mjs" --value \'$(echo nope)\''), ['node', 'a b.mjs', '--value', '$(echo nope)']);
  assert.throws(() => splitCommand('node "bad'), /Unclosed/);
  assert.throws(() => splitCommand(''), /Empty/);
});

test('stdio wiring namespaces only collisions and flattens text', async () => {
  const script = `import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
    import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
    const s = new McpServer({name:'test',version:'1'});
    s.registerTool('shared', {inputSchema:{}}, async()=>({content:[{type:'text',text:'one'},{type:'text',text:'two'}]}));
    s.registerTool(process.argv[1], {inputSchema:{}}, async()=>({content:[{type:'text',text:'unique'}]}));
    await s.connect(new StdioServerTransport());`;
  const mcp = await connectMcp(['unique1', 'unique2'].map((name) => [process.execPath, '--input-type=module', '-e', script, name]));
  try {
    assert.deepEqual(mcp.tools.map((tool) => tool.function.name), ['server1__shared', 'unique1', 'server2__shared', 'unique2']);
    assert.equal(await mcp.callTool('server1__shared', {}), 'one\ntwo');
    assert.equal(await mcp.callTool('unique2', {}), 'unique');
  } finally { await mcp.close(); }
});

test('failed MCP startup is friendly and closes transports', async (t) => {
  let closed = 0;
  const original = Client.prototype.close;
  t.mock.method(Client.prototype, 'close', async function () { closed++; return original.call(this); });
  await assert.rejects(connectMcp([['/no-such-mcp-command']]), /MCP server 1 failed to start/);
  assert.equal(closed, 1);
});

test('real Router drops 410 and parks 429 while retaining tool history', async () => {
  const router = new Router({ ranked: ['gone', 'busy', 'alive'] });
  const attempted = []; let turns = 0;
  const result = await runAgent(options(async ({ model, messages }) => {
    attempted.push(model);
    if (model === 'gone') throw new NimError('gone', { status: 410 });
    if (model === 'busy') throw new NimError('busy', { status: 429 });
    if (!turns++) return reply([call()]);
    assert.equal(messages.at(-1).role, 'tool');
    return reply(null, 'Alive after failover.');
  }, { router }));
  assert.equal(result.answer, 'Alive after failover.');
  assert.deepEqual(attempted, ['gone', 'busy', 'alive', 'alive']);
  assert.ok(result.routeLog.some((item) => item.gone));
  assert.ok(result.routeLog.some((item) => item.parked));
});

test('custom MCP environment omits key unless sharing is explicit', () => {
  const env = { PATH: '/bin', NVIDIA_API_KEY: 'test-value', OTHER: 'yes', UNSET: undefined };
  assert.deepEqual(mcpEnvironment(env), { PATH: '/bin', OTHER: 'yes' });
  assert.deepEqual(mcpEnvironment(env, true), { PATH: '/bin', NVIDIA_API_KEY: 'test-value', OTHER: 'yes' });
  assert.equal(env.NVIDIA_API_KEY, 'test-value');
});

test('agent exit codes distinguish completion from both stops', () => {
  assert.equal(agentExitCode({ answer: 'Done' }), 0);
  assert.equal(agentExitCode({ stopped: 'step_limit' }), 2);
  assert.equal(agentExitCode({ stopped: 'repeated_tool' }), 2);
});

test('MCP startup includes bounded redacted stderr', async () => {
  const script = "process.stderr.write('x'.repeat(3000) + ' failure private-test-value'); process.exit(1)";
  await assert.rejects(connectMcp([[process.execPath, '-e', script]], { ...process.env, NVIDIA_API_KEY: 'private-test-value' }), (e) => {
    assert.match(e.message, /failure \[redacted\]/);
    assert.doesNotMatch(e.message, /private-test-value/);
    assert.ok(e.message.length < 2200);
    return true;
  });
});
