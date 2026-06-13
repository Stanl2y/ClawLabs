import readline from 'node:readline';

import {
  callTool,
  loadLab,
  parseArgs,
  writeError,
  writeResult,
} from './google-workspace-mcp-support.mjs';
import { toolSchemas } from './google-workspace-tool-schemas.mjs';

function handleInitialize(id, params) {
  writeResult(id, {
    protocolVersion: params?.protocolVersion || '2025-06-18',
    capabilities: { tools: {} },
    serverInfo: { name: 'nanoclaw-google-workspace-lab', version: '0.1.0' },
  });
}

function handleToolCall(session, id, params) {
  if (typeof params.name !== 'string') {
    writeError(id, -32602, 'tools/call requires string params.name');
    return;
  }

  try {
    const result = callTool(session, params.name, params.arguments || {});
    if (result === null) {
      writeError(id, -32602, `Unknown tool: ${params.name}`);
      return;
    }
    writeResult(id, result);
  } catch (error) {
    writeError(id, -32602, error instanceof Error ? error.message : String(error));
  }
}

function handleRequest(session, message) {
  const id = message?.id;
  if (message === null || typeof message !== 'object' || Array.isArray(message)) {
    writeError(null, -32600, 'Invalid Request');
    return;
  }

  if (typeof message.method !== 'string') {
    writeError(id ?? null, -32600, 'Invalid Request');
    return;
  }

  if (!Object.hasOwn(message, 'id')) {
    return;
  }

  if (message.method === 'initialize') {
    handleInitialize(id, message.params);
    return;
  }

  if (message.method === 'tools/list') {
    writeResult(id, { tools: toolSchemas() });
    return;
  }

  if (message.method === 'tools/call') {
    handleToolCall(session, id, message.params || {});
    return;
  }

  writeError(id, -32601, `Unknown method: ${message.method}`);
}

const config = parseArgs(process.argv.slice(2));
const session = {
  config,
  lab: loadLab(config),
  state: { readUntrustedGmail: false, readPrivateDrive: false, draftCount: 0 },
};
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

rl.on('line', (line) => {
  if (!line.trim()) return;
  try {
    handleRequest(session, JSON.parse(line));
  } catch {
    writeError(null, -32700, 'Parse error');
  }
});
