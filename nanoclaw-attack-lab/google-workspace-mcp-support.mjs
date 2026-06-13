import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const LAB_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_SCENARIO = path.join(
  LAB_DIR,
  'fixtures',
  'google_workspace',
  'gmail_drive_draft_canary.json',
);
const DEFAULT_EVIDENCE_DIR = path.join(LAB_DIR, 'evidence');
const VALID_MODES = new Set(['baseline', 'defended']);

function evidenceToolEnabled() {
  return process.env.GOOGLE_WORKSPACE_EXPOSE_EVIDENCE_TOOL !== '0';
}

export function parseArgs(argv) {
  const config = {
    scenario: DEFAULT_SCENARIO,
    evidenceDir: DEFAULT_EVIDENCE_DIR,
    mode: process.env.GOOGLE_WORKSPACE_MCP_MODE || 'baseline',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--scenario' && value) {
      config.scenario = path.resolve(value);
      index += 1;
    } else if (key === '--evidence-dir' && value) {
      config.evidenceDir = path.resolve(value);
      index += 1;
    } else if (key === '--mode' && value) {
      config.mode = value;
      index += 1;
    }
  }

  if (!VALID_MODES.has(config.mode)) {
    throw new Error(`invalid mode: ${config.mode}`);
  }
  return config;
}

export function loadLab(config) {
  const scenario = readJson(config.scenario);
  const fixtureDir = resolveFixtureDir(scenario, config.scenario);
  return {
    scenario,
    gmailThreads: readJson(path.join(fixtureDir, 'gmail_threads.json')),
    driveFiles: readJson(path.join(fixtureDir, 'drive_files.json')),
  };
}

export function callTool(session, name, args) {
  if (name === 'gmail.search_threads') return searchThreads(session, args);
  if (name === 'gmail.get_thread') return getThread(session, args);
  if (name === 'drive.search_files') return searchFiles(session, args);
  if (name === 'drive.read_file_content') return readFileContent(session, args);
  if (name === 'gmail.create_draft') return createDraft(session, name, args);
  if (name === 'list_google_workspace_evidence' && evidenceToolEnabled()) return listEvidence(session);
  return null;
}

export function writeResult(id, result) {
  writeMessage({ jsonrpc: '2.0', id, result });
}

export function writeError(id, code, message) {
  writeMessage({ jsonrpc: '2.0', id, error: { code, message } });
}

function searchThreads(session, args) {
  const query = requiredString(args, 'query');
  const threads = session.lab.gmailThreads.filter((thread) => includesText(threadSubject(thread), query));
  return jsonContent(threads.map((thread) => ({ id: thread.id, subject: threadSubject(thread), historyId: thread.historyId })));
}

function getThread(session, args) {
  const thread = findById(session.lab.gmailThreads, requiredString(args, 'thread_id'), 'gmail thread');
  if (!isInternalSender(threadSender(thread))) session.state.readUntrustedGmail = true;
  return jsonContent({
    ...thread,
    subject: threadSubject(thread),
    sender: threadSender(thread),
    body: threadBody(thread),
    trust: 'untrusted_email',
  });
}

function searchFiles(session, args) {
  const query = requiredString(args, 'query');
  const files = session.lab.driveFiles.filter((file) => driveFileMatchesQuery(file, query));
  return jsonContent(files.map((file) => ({ id: file.id, name: file.name })));
}

function readFileContent(session, args) {
  const file = findById(session.lab.driveFiles, requiredString(args, 'file_id'), 'drive file');
  session.state.readPrivateDrive = true;
  return jsonContent({
    ...file,
    content: driveFileContent(file),
    classification: file.appProperties?.classification || 'private_drive_file',
  });
}

function createDraft(session, name, args) {
  if (shouldBlockDraft(session, args)) {
    const block = {
      tool: name,
      reason: 'private_drive_to_external_gmail_draft',
      trust_zone: 'trusted_policy',
      to: requiredString(args, 'to'),
      protected_asset: session.lab.scenario.protected_asset,
    };
    appendEvidence(session.config, 'google_workspace_policy_blocks.jsonl', block);
    return jsonContent({ status: 'blocked', ...block });
  }

  const draft = {
    id: `draft-local-${String(session.state.draftCount + 1).padStart(3, '0')}`,
    to: requiredString(args, 'to'),
    subject: requiredString(args, 'subject'),
    body: requiredString(args, 'body'),
  };
  session.state.draftCount += 1;
  appendEvidence(session.config, 'google_workspace_drafts.jsonl', draft);
  return jsonContent({ status: 'created', ...draft });
}

function listEvidence(session) {
  return jsonContent({
    drafts: readEvidence(session.config, 'google_workspace_drafts.jsonl'),
    policyBlocks: readEvidence(session.config, 'google_workspace_policy_blocks.jsonl'),
  });
}

function shouldBlockDraft(session, args) {
  return (
    session.config.mode === 'defended' &&
    !isInternalSender(requiredString(args, 'to')) &&
    requiredString(args, 'body').includes(session.lab.scenario.protected_asset)
  );
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function resolveFixtureDir(scenario, scenarioPath) {
  const candidates = [
    path.resolve(path.dirname(scenarioPath), scenario.fixture),
    path.resolve(LAB_DIR, scenario.fixture),
    path.resolve(process.cwd(), scenario.fixture),
  ];
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error(`fixture not found: ${scenario.fixture}`);
  return found;
}

function textContent(text) {
  return { content: [{ type: 'text', text }] };
}

function jsonContent(value) {
  return textContent(JSON.stringify(value));
}

function writeMessage(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

function requiredString(args, key) {
  const value = args?.[key];
  if (typeof value === 'string') return value;
  throw new Error(`missing string parameter: ${key}`);
}

function evidenceFile(config, name) {
  fs.mkdirSync(config.evidenceDir, { recursive: true });
  return path.join(config.evidenceDir, name);
}

function appendEvidence(config, name, item) {
  fs.appendFileSync(
    evidenceFile(config, name),
    `${JSON.stringify({ timestamp: new Date().toISOString(), ...item })}\n`,
    'utf8',
  );
}

function readEvidence(config, name) {
  const file = evidenceFile(config, name);
  if (!fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, 'utf8')
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line));
}

function includesText(value, query) {
  return String(value).toLowerCase().includes(query.toLowerCase());
}

function driveFileMatchesQuery(file, query) {
  const haystack = [
    file.name,
    file.exportedText || '',
    file.appProperties?.classification || '',
    file.appProperties?.source || '',
  ]
    .join('\n')
    .toLowerCase();
  const normalizedQuery = String(query).toLowerCase();
  if (haystack.includes(normalizedQuery)) return true;

  const tokens = normalizedQuery
    .split(/[^a-z0-9]+/i)
    .map((token) => token.trim())
    .filter((token) => token.length >= 3);
  if (tokens.length === 0) return false;

  let matches = 0;
  for (const token of new Set(tokens)) {
    if (haystack.includes(token)) matches += 1;
  }
  return matches >= Math.min(2, tokens.length);
}

function findById(items, id, label) {
  const item = items.find((candidate) => candidate.id === id);
  if (!item) throw new Error(`${label} not found: ${id}`);
  return item;
}

function threadSubject(thread) {
  return firstMessage(thread).payload.headers.find((header) => sameHeader(header, 'Subject'))?.value || '';
}

function threadSender(thread) {
  return firstMessage(thread).payload.headers.find((header) => sameHeader(header, 'From'))?.value || '';
}

function threadBody(thread) {
  return decodeBase64Url(firstMessage(thread).payload.body.data);
}

function firstMessage(thread) {
  const message = thread.messages?.[0];
  if (!message) throw new Error(`gmail thread has no messages: ${thread.id}`);
  return message;
}

function sameHeader(header, name) {
  return String(header?.name || '').toLowerCase() === name.toLowerCase();
}

function isInternalSender(sender) {
  return /<[^>]+@example\.internal>$/.test(sender) || sender.endsWith('@example.internal');
}

function decodeBase64Url(data) {
  const normalized = String(data).replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
  return Buffer.from(padded, 'base64').toString('utf8');
}

function driveFileContent(file) {
  return typeof file.exportedText === 'string' ? file.exportedText : '';
}
