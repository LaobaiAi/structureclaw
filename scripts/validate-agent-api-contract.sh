#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

npm run build --prefix backend >/dev/null

node - <<'JS'
const assert = (cond, msg) => {
  if (!cond) {
    throw new Error(msg);
  }
};

const run = async () => {
  const { createRequire } = await import('node:module');
  const require = createRequire(process.cwd() + '/backend/package.json');
  const Fastify = require('fastify');
  const { AgentService } = await import('./backend/dist/services/agent.js');

  const captured = [];
  AgentService.prototype.run = async function mockRun(params) {
    captured.push(params);
    return {
      traceId: 'trace-api-contract',
      startedAt: '2026-03-09T00:00:00.000Z',
      completedAt: '2026-03-09T00:00:00.012Z',
      durationMs: 12,
      success: true,
      mode: 'rule-based',
      needsModelInput: false,
      plan: ['validate', 'analyze', 'report'],
      toolCalls: [
        { tool: 'validate', input: {}, status: 'success', startedAt: new Date().toISOString() },
        { tool: 'analyze', input: {}, status: 'success', startedAt: new Date().toISOString() },
        { tool: 'report', input: {}, status: 'success', startedAt: new Date().toISOString() },
      ],
      response: 'ok',
      report: {
        summary: 'ok',
        json: { k: 'v' },
      },
      artifacts: [{ type: 'report', format: 'json', path: '/tmp/report.json' }],
      metrics: {
        toolCount: 3,
        failedToolCount: 0,
        totalToolDurationMs: 10,
        averageToolDurationMs: 3.3,
        maxToolDurationMs: 5,
        toolDurationMsByName: { validate: 2, analyze: 3, report: 5 },
      },
    };
  };

  const { agentRoutes } = await import('./backend/dist/api/agent.js');
  const { chatRoutes } = await import('./backend/dist/api/chat.js');

  const app = Fastify();
  await app.register(agentRoutes, { prefix: '/api/v1/agent' });
  await app.register(chatRoutes, { prefix: '/api/v1/chat' });

  const requestBody = {
    message: '请分析并导出报告',
    conversationId: 'conv-api-1',
    traceId: 'trace-request-001',
    context: {
      autoAnalyze: true,
      autoCodeCheck: true,
      includeReport: true,
      reportFormat: 'both',
      reportOutput: 'file',
    },
  };

  const runResp = await app.inject({
    method: 'POST',
    url: '/api/v1/agent/run',
    payload: requestBody,
  });
  assert(runResp.statusCode === 200, 'agent/run should return 200');
  const runPayload = runResp.json();
  assert(runPayload.traceId === 'trace-api-contract', 'agent/run should return traceId');
  assert(typeof runPayload.startedAt === 'string', 'agent/run should return startedAt');
  assert(typeof runPayload.completedAt === 'string', 'agent/run should return completedAt');
  assert(Array.isArray(runPayload.toolCalls), 'agent/run should include toolCalls');
  assert(runPayload.metrics?.toolCount === 3, 'agent/run should include metrics');
  assert(runPayload.metrics?.maxToolDurationMs === 5, 'agent/run should include expanded metrics');

  const execResp = await app.inject({
    method: 'POST',
    url: '/api/v1/chat/execute',
    payload: requestBody,
  });
  assert(execResp.statusCode === 200, 'chat/execute should return 200');
  const execPayload = execResp.json();
  assert(execPayload.traceId === 'trace-api-contract', 'chat/execute should proxy agent result');
  assert(execPayload.artifacts?.[0]?.path === '/tmp/report.json', 'chat/execute should return artifacts');

  assert(captured.length >= 2, 'agent run should be called for both endpoints');
  assert(captured[0]?.traceId === 'trace-request-001', 'agent/run should pass traceId');
  assert(captured[1]?.traceId === 'trace-request-001', 'chat/execute should pass traceId');
  assert(captured[0]?.context?.reportOutput === 'file', 'agent/run should pass reportOutput context');
  assert(captured[1]?.context?.reportFormat === 'both', 'chat/execute should pass reportFormat context');

  await app.close();
  console.log('[ok] agent api contract regression');
};

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
JS
