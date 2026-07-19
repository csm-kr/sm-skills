'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { spawn, spawnSync } = require('child_process');

const HOST = '127.0.0.1';
const PORT = Number(process.env.CODEX_UI_PORT || 43119);
const ROOT = __dirname;
const WORKSPACE = process.env.CODEX_UI_WORKSPACE ? path.resolve(process.env.CODEX_UI_WORKSPACE) : path.resolve(ROOT, '..');
const RUNS_DIR = path.join(ROOT, 'runs');
const SCHEMA_PATH = path.join(ROOT, 'result-schema.json');
const EXAMPLE_SCHEMA_PATH = path.join(ROOT, 'example-schema.json');
const CRITERIA_SCHEMA_PATH = path.join(ROOT, 'criteria-schema.json');
function resolveCodexBin() {
  if (process.env.CODEX_BIN) return process.env.CODEX_BIN;
  if (process.platform !== 'win32') return 'codex';
  const candidates = [
    process.env.APPDATA && path.join(process.env.APPDATA, 'npm', 'node_modules', '@openai', 'codex', 'node_modules', '@openai', 'codex-win32-x64', 'vendor', 'x86_64-pc-windows-msvc', 'bin', 'codex.exe'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'OpenAI', 'Codex', 'bin', 'codex.exe')
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate)) || 'codex.cmd';
}
const CODEX_BIN = resolveCodexBin();
const CODEX_NEEDS_SHELL = process.platform === 'win32' && /\.cmd$/i.test(CODEX_BIN);
const CODEX_SANDBOX = process.env.CODEX_UI_SANDBOX || 'workspace-write';
const BROWSER_HARNESS_HOME = process.env.BH_HOME || process.env.BROWSER_HARNESS_HOME || path.join(os.homedir(), '.config', 'browser-harness');
const MAX_BODY_BYTES = 32 * 1024;
const runs = new Map();

fs.mkdirSync(RUNS_DIR, { recursive: true });

function json(res, status, value) {
  const body = JSON.stringify(value);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store'
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new Error('요청 본문이 너무 큽니다.'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function publicRun(job) {
  return {
    runId: job.id,
    status: job.status,
    startedAt: job.startedAt,
    finishedAt: job.finishedAt || null,
    exitCode: job.exitCode,
    error: job.error || null,
    result: job.result || null
  };
}

function emit(job, event) {
  const payload = Object.assign({ emitted_at: new Date().toISOString() }, event);
  job.events.push(payload);
  if (job.events.length > 1000) job.events.shift();
  const line = `data: ${JSON.stringify(payload)}\n\n`;
  for (const res of job.listeners) {
    try { res.write(line); } catch (_) { job.listeners.delete(res); }
  }
}

function finishStreams(job) {
  for (const res of job.listeners) {
    try { res.end(); } catch (_) {}
  }
  job.listeners.clear();
}

function buildPrompt(query, criteria, runDir, options = {}) {
  const safeCriteria = JSON.stringify(criteria, null, 2);
  const excludeChannels = Array.isArray(options.excludeChannels) ? options.excludeChannels : [];
  const expansionInstructions = options.isExpansion ? [
    '',
    '[Additional batch]',
    `This is sequential batch ${Math.max(2, Number(options.batchNumber || 2))}. Return up to 5 NEW candidates that are not in the exclusion list below.`,
    'Treat matching channel URLs as duplicates. Also avoid the same channel when only the channel name matches.',
    'Do a fresh discovery pass for new candidates and run the full verification, scoring, and report pipeline again. Do not merely re-rank or repeat the previous candidates.',
    '[Already shown channels — exclude]',
    JSON.stringify(excludeChannels, null, 2)
  ] : [];
  return [
    'Use $find-youtube-influencers and follow it faithfully.',
    'The user already confirmed the request below. Do not ask a follow-up question; apply the provided structured criteria.',
    'Use public web discovery and the official Browser Use skill for direct YouTube verification.',
    'The default Browser Use daemon is already running and healthy. The server copied its authenticated runtime endpoint into this writable run directory.',
    'BH_HOME, BH_RUNTIME_DIR, BH_TMP_DIR, and BH_AGENT_WORKSPACE are all preconfigured inside this run directory while still pointing to the existing default daemon endpoint.',
    'Invoke browser-use with the preconfigured default daemon exactly as documented. Do not set or change BH_HOME, BROWSER_HARNESS_HOME, BH_RUNTIME_DIR, BH_RUNTIME_DIR_SHARED, BH_TMP_DIR, BH_AGENT_WORKSPACE, BU_NAME, BU_CDP_URL, or BU_CDP_WS. Do not start an isolated or remote daemon and do not substitute Computer Use.',
    'Do not mix longform and Shorts in one sample. If both are requested, evaluate them as separate cohorts.',
    'Do not relax required gates. Unknown public values must remain null. Use the skill scripts for scoring and HTML rendering.',
    'Each execution is capped at 5 candidates to reduce YouTube automation and bot-detection risk.',
    'Execute the research in this exact order: (1) broad public-web candidate discovery, (2) direct YouTube verification with Browser Use, (3) score_candidates.py, (4) render_report.py and Browser Use report QA, (5) final schema result.',
    'Do not create scored-candidates.json before candidates.json, and do not create the HTML report before scored-candidates.json.',
    `Write intermediate JSON and the self-contained HTML report only inside: ${runDir}`,
    'Return a final JSON object that exactly matches the supplied output schema. Candidate URLs and video URLs must be URLs you actually verified.',
    'Map NEAR MATCH to the schema status value NEAR. Use evidence_completeness values such as 완전, 부분, or 부족.',
    'If no candidate passes, return verified NEAR/FAIL/UNVERIFIED candidates up to 5 and explain this in summary. Never fabricate candidates or metrics.',
    '',
    '[Confirmed user request]',
    query,
    '',
    '[Structured criteria]',
    safeCriteria,
    ...expansionInstructions
  ].join('\n');
}

function observePipelineEvent(job, event) {
  if (!job || !event || !job.pipelineStages) return;
  const type = String(event.type || '');
  const hay = `${type} ${JSON.stringify(event.item || {})} ${event.text || ''}`.toLowerCase();
  const found = [];
  if (type === 'thread.started' || type === 'turn.started') found.push(['criteria', '확정된 조사 기준을 Codex 실행에 전달했습니다.']);
  if (/web_search|search_query|검색 결과|google\.com\/search|bing\.com\/search/.test(hay)) found.push(['discovery', '공개 웹 후보 발견 이벤트를 확인했습니다.']);
  if ((/browser-use|browser_use/.test(hay) && /youtube\.com|youtu\.be/.test(hay)) || /youtube 직접 검증|채널 페이지.*확인/.test(hay)) {
    found.push(['verification', 'Browser Use의 YouTube 직접 검증 이벤트를 확인했습니다.']);
  }
  if (/score_candidates\.py/.test(hay)) found.push(['scoring', 'score_candidates.py 실행 이벤트를 확인했습니다.']);
  if (/render_report\.py/.test(hay)) found.push(['report', 'render_report.py 실행 이벤트를 확인했습니다.']);
  for (const [phase, message] of found) {
    if (job.pipelineStages.has(phase)) continue;
    job.pipelineStages.add(phase);
    emit(job, { type: 'server.stage', source: 'server', phase, message });
  }
}

function inspectPipelineArtifacts(job) {
  const files = {
    candidates: path.join(job.runDir, 'candidates.json'),
    scored: path.join(job.runDir, 'scored-candidates.json'),
    report: path.join(job.runDir, 'influencer-report.html')
  };
  const artifacts = {};
  for (const [name, filePath] of Object.entries(files)) {
    if (!fs.existsSync(filePath)) {
      artifacts[name] = { exists: false, modified_at: null };
      continue;
    }
    const stat = fs.statSync(filePath);
    artifacts[name] = { exists: true, modified_at: stat.mtime.toISOString() };
  }
  const complete = Object.values(artifacts).every(item => item.exists);
  const ordered = complete &&
    new Date(artifacts.candidates.modified_at) <= new Date(artifacts.scored.modified_at) &&
    new Date(artifacts.scored.modified_at) <= new Date(artifacts.report.modified_at);
  return { complete, ordered, artifacts };
}

function buildExamplePrompt(seedQuery) {
  return [
    'Create one Korean natural-language request for finding YouTube influencers for a product sponsorship campaign.',
    'This is only a request-writing task. Do not browse the web, inspect files, call tools, or perform influencer research.',
    'Return a final JSON object that exactly matches the supplied output schema.',
    'The query must ask for Korean YouTubers and must request exactly 5 results because the UI caps results at 5 to reduce YouTube automation and bot-detection risk.',
    'Choose one concrete consumer product. Vary the product category and the condition structure instead of copying the seed request.',
    'Include 2 to 4 useful conditions selected from subscriber range, recent longform or Shorts sample size, average views, average or total comments, upload recency, preferred content context, or advertising experience.',
    'Keep longform and Shorts as separate cohorts when both are mentioned. Do not invent channel names or research results.',
    'Write the query in friendly, specific Korean that a non-technical user can edit.',
    'Write note as one short Korean sentence explaining how this example differs from the seed request.',
    '',
    '[Seed request to differ from]',
    seedQuery || '(none)'
  ].join('\n');
}

function buildCriteriaPrompt(query) {
  const evaluationDate = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(new Date());
  return [
    'Interpret the Korean YouTube influencer discovery request below.',
    'This is only a request-understanding task. Do not browse the web, inspect files, call tools, or perform influencer research.',
    'Return a final JSON object that exactly matches the supplied output schema.',
    'Write confirmation_message as natural, friendly Korean addressed to the user. Do not assemble a mechanical keyword sentence and do not use awkward wording such as "한국어 상품을 정확히 채널 중".',
    'Preserve every explicit condition. Put only genuinely omitted defaults in assumptions.',
    'Defaults when omitted: market 한국, language 한국어, subscriber_max 100000, recent_video_count 3, recent_content_type longform, upload_recency_days 90, sponsored_content_required false, strictness strict, near_match_tolerance 0.1, require_complete_evidence true.',
    'If no comment rule is requested, use comment_rule total while leaving both comment thresholds null.',
    'If both longform and Shorts are requested, include both in content_cohorts and keep their samples separate. Otherwise include one cohort.',
    'The UI can return at most 5 candidates to reduce YouTube automation and bot-detection risk. Preserve the user number in requested_result_count, cap result_count at 5, and set bot_limit_applied correctly.',
    `Set evaluation_date to ${evaluationDate}.`,
    'Do not invent channel names, metrics, or research findings.',
    '',
    '[User request]',
    query
  ].join('\n');
}

function parseJsonLines(job, chunk, streamName) {
  job[streamName] += chunk.toString('utf8');
  const lines = job[streamName].split(/\r?\n/);
  job[streamName] = lines.pop() || '';
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (streamName === 'stdoutBuffer') {
      try {
        const event = JSON.parse(line);
        const normalized = Object.assign({ source: 'codex' }, event);
        emit(job, normalized);
        observePipelineEvent(job, normalized);
      } catch (_) {
        emit(job, { type: 'codex.stdout', source: 'codex', text: line.slice(0, 2000) });
      }
    } else {
      emit(job, { type: 'codex.stderr', source: 'codex', text: line.slice(0, 2000) });
    }
  }
}

function startCodexRun(query, criteria, options = {}) {
  const active = [...runs.values()].find(job => job.status === 'running' || job.status === 'starting');
  if (active) {
    const err = new Error('봇 탐지 위험 완화를 위해 한 번에 하나의 조사만 실행할 수 있습니다.');
    err.statusCode = 409;
    err.activeRunId = active.id;
    throw err;
  }

  const idPrefix = options.isExpansion ? 'more-' : '';
  const id = `${idPrefix}${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(3).toString('hex')}`;
  const runDir = path.join(RUNS_DIR, id);
  fs.mkdirSync(runDir, { recursive: true });
  const browserRunHome = path.join(runDir, '.browser-harness');
  const browserRuntimeDir = path.join(browserRunHome, 'runtime');
  const browserTmpDir = path.join(browserRunHome, 'tmp');
  const browserWorkspaceDir = path.join(browserRunHome, 'agent-workspace');
  fs.mkdirSync(browserRuntimeDir, { recursive: true });
  fs.mkdirSync(browserTmpDir, { recursive: true });
  fs.mkdirSync(browserWorkspaceDir, { recursive: true });
  const sourceRuntimeDir = path.join(BROWSER_HARNESS_HOME, 'runtime');
  for (const fileName of ['bu-default.port', 'bu-default.pid']) {
    const source = path.join(sourceRuntimeDir, fileName);
    if (fs.existsSync(source)) fs.copyFileSync(source, path.join(browserRuntimeDir, fileName));
  }
  const outputPath = path.join(runDir, 'final-result.json');
  const prompt = buildPrompt(query, criteria, runDir, options);
  const job = {
    id,
    status: 'starting',
    startedAt: new Date().toISOString(),
    finishedAt: null,
    exitCode: null,
    error: null,
    result: null,
    events: [],
    listeners: new Set(),
    stdoutBuffer: '',
    stderrBuffer: '',
    child: null,
    outputPath,
    runDir,
    isExpansion: Boolean(options.isExpansion),
    batchNumber: Math.max(1, Number(options.batchNumber || 1)),
    pipelineStages: new Set()
  };
  runs.set(id, job);

  const args = [
    'exec', '--json', '--ephemeral', '--color', 'never',
    '--sandbox', CODEX_SANDBOX,
    '-c', 'sandbox_workspace_write.network_access=true',
    '--skip-git-repo-check',
    '-C', WORKSPACE,
    '--output-schema', SCHEMA_PATH,
    '--output-last-message', outputPath,
    '-'
  ];

  emit(job, {
    type: 'server.started',
    source: 'server',
    run_id: id,
    command: `codex exec --json --ephemeral --sandbox ${CODEX_SANDBOX} -c sandbox_workspace_write.network_access=true --output-schema result-schema.json -`
  });

  const child = spawn(CODEX_BIN, args, {
    cwd: WORKSPACE,
    env: Object.assign({}, process.env, {
      NO_COLOR: '1',
      BH_HOME: browserRunHome,
      BROWSER_HARNESS_HOME: browserRunHome,
      BH_RUNTIME_DIR: browserRuntimeDir,
      BH_RUNTIME_DIR_SHARED: '1',
      BH_TMP_DIR: browserTmpDir,
      BH_AGENT_WORKSPACE: browserWorkspaceDir
    }),
    windowsHide: true,
    shell: CODEX_NEEDS_SHELL
  });
  job.child = child;
  job.status = 'running';
  child.stdout.on('data', chunk => parseJsonLines(job, chunk, 'stdoutBuffer'));
  child.stderr.on('data', chunk => parseJsonLines(job, chunk, 'stderrBuffer'));
  child.on('error', error => {
    job.status = 'failed';
    job.error = error.message;
    job.finishedAt = new Date().toISOString();
    emit(job, { type: 'server.failed', source: 'server', message: error.message });
    finishStreams(job);
  });
  child.on('close', code => {
    if (job.status === 'cancelled' || job.status === 'failed') return;
    job.exitCode = code;
    job.finishedAt = new Date().toISOString();
    if (job.stdoutBuffer.trim()) parseJsonLines(job, '\n', 'stdoutBuffer');
    if (job.stderrBuffer.trim()) parseJsonLines(job, '\n', 'stderrBuffer');
    try {
      const raw = fs.readFileSync(outputPath, 'utf8').trim();
      job.result = JSON.parse(raw);
      const pipeline = inspectPipelineArtifacts(job);
      emit(job, { type: 'server.pipeline', source: 'server', pipeline });
      emit(job, { type: 'server.result', source: 'server', result: job.result });
      if (job.result.status === 'failed') {
        job.status = 'failed';
        job.error = job.result.summary || 'Codex가 검증을 완료하지 못했습니다.';
        emit(job, { type: 'server.failed', source: 'server', exit_code: code, message: job.error });
      } else {
        job.status = code === 0 ? 'completed' : 'partial';
        emit(job, { type: 'server.completed', source: 'server', exit_code: code, status: job.status });
      }
    } catch (error) {
      job.status = 'failed';
      job.error = code === 0 ? `최종 구조화 결과를 읽지 못했습니다: ${error.message}` : `Codex CLI가 종료 코드 ${code}로 끝났습니다.`;
      emit(job, { type: 'server.failed', source: 'server', exit_code: code, message: job.error });
    }
    setTimeout(() => finishStreams(job), 100);
  });
  child.stdin.end(prompt, 'utf8');
  return job;
}

function startExampleRun(seedQuery) {
  const active = [...runs.values()].find(job => job.status === 'running' || job.status === 'starting');
  if (active) {
    const err = new Error('현재 Codex 작업이 끝난 뒤 다른 예를 만들어 주세요.');
    err.statusCode = 409;
    err.activeRunId = active.id;
    throw err;
  }

  const id = `example-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(3).toString('hex')}`;
  const runDir = path.join(RUNS_DIR, id);
  fs.mkdirSync(runDir, { recursive: true });
  const outputPath = path.join(runDir, 'example-result.json');
  const prompt = buildExamplePrompt(seedQuery);
  const job = {
    id,
    kind: 'example',
    status: 'starting',
    startedAt: new Date().toISOString(),
    finishedAt: null,
    exitCode: null,
    error: null,
    result: null,
    events: [],
    listeners: new Set(),
    stdoutBuffer: '',
    stderrBuffer: '',
    child: null,
    outputPath
  };
  runs.set(id, job);

  const args = [
    'exec', '--json', '--ephemeral', '--color', 'never',
    '--sandbox', 'read-only',
    '--skip-git-repo-check',
    '-C', WORKSPACE,
    '--output-schema', EXAMPLE_SCHEMA_PATH,
    '--output-last-message', outputPath,
    '-'
  ];

  emit(job, {
    type: 'server.started',
    source: 'server',
    job_kind: 'example',
    run_id: id,
    command: 'codex exec --json --ephemeral --sandbox read-only --output-schema example-schema.json -'
  });

  const child = spawn(CODEX_BIN, args, {
    cwd: WORKSPACE,
    env: Object.assign({}, process.env, { NO_COLOR: '1' }),
    windowsHide: true,
    shell: CODEX_NEEDS_SHELL
  });
  job.child = child;
  job.status = 'running';
  child.stdout.on('data', chunk => parseJsonLines(job, chunk, 'stdoutBuffer'));
  child.stderr.on('data', chunk => parseJsonLines(job, chunk, 'stderrBuffer'));
  child.on('error', error => {
    job.status = 'failed';
    job.error = error.message;
    job.finishedAt = new Date().toISOString();
    emit(job, { type: 'server.failed', source: 'server', job_kind: 'example', message: error.message });
    finishStreams(job);
  });
  child.on('close', code => {
    if (job.status === 'cancelled' || job.status === 'failed') return;
    job.exitCode = code;
    job.finishedAt = new Date().toISOString();
    if (job.stdoutBuffer.trim()) parseJsonLines(job, '\n', 'stdoutBuffer');
    if (job.stderrBuffer.trim()) parseJsonLines(job, '\n', 'stderrBuffer');
    try {
      const raw = fs.readFileSync(outputPath, 'utf8').trim();
      const result = JSON.parse(raw);
      if (typeof result.query !== 'string' || result.query.trim().length < 20) throw new Error('생성된 요청문이 너무 짧습니다.');
      job.result = { query: result.query.trim(), note: String(result.note || '').trim() };
      emit(job, { type: 'server.result', source: 'server', job_kind: 'example', result: job.result });
      job.status = code === 0 ? 'completed' : 'partial';
      emit(job, { type: 'server.completed', source: 'server', job_kind: 'example', exit_code: code, status: job.status });
    } catch (error) {
      job.status = 'failed';
      job.error = code === 0 ? `새 요청 예시를 읽지 못했습니다: ${error.message}` : `Codex CLI가 종료 코드 ${code}로 끝났습니다.`;
      emit(job, { type: 'server.failed', source: 'server', job_kind: 'example', exit_code: code, message: job.error });
    }
    setTimeout(() => finishStreams(job), 100);
  });
  child.stdin.end(prompt, 'utf8');
  return job;
}

function startCriteriaRun(query) {
  const active = [...runs.values()].find(job => job.status === 'running' || job.status === 'starting');
  if (active) {
    const err = new Error('현재 Codex 작업이 끝난 뒤 조건을 확인해 주세요.');
    err.statusCode = 409;
    err.activeRunId = active.id;
    throw err;
  }

  const id = `criteria-${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomBytes(3).toString('hex')}`;
  const runDir = path.join(RUNS_DIR, id);
  fs.mkdirSync(runDir, { recursive: true });
  const outputPath = path.join(runDir, 'criteria-result.json');
  const prompt = buildCriteriaPrompt(query);
  const job = {
    id,
    kind: 'criteria',
    status: 'starting',
    startedAt: new Date().toISOString(),
    finishedAt: null,
    exitCode: null,
    error: null,
    result: null,
    events: [],
    listeners: new Set(),
    stdoutBuffer: '',
    stderrBuffer: '',
    child: null,
    outputPath
  };
  runs.set(id, job);

  const args = [
    'exec', '--json', '--ephemeral', '--color', 'never',
    '--sandbox', 'read-only',
    '--skip-git-repo-check',
    '-C', WORKSPACE,
    '--output-schema', CRITERIA_SCHEMA_PATH,
    '--output-last-message', outputPath,
    '-'
  ];

  emit(job, {
    type: 'server.started',
    source: 'server',
    job_kind: 'criteria',
    run_id: id,
    command: 'codex exec --json --ephemeral --sandbox read-only --output-schema criteria-schema.json -'
  });

  const child = spawn(CODEX_BIN, args, {
    cwd: WORKSPACE,
    env: Object.assign({}, process.env, { NO_COLOR: '1' }),
    windowsHide: true,
    shell: CODEX_NEEDS_SHELL
  });
  job.child = child;
  job.status = 'running';
  child.stdout.on('data', chunk => parseJsonLines(job, chunk, 'stdoutBuffer'));
  child.stderr.on('data', chunk => parseJsonLines(job, chunk, 'stderrBuffer'));
  child.on('error', error => {
    job.status = 'failed';
    job.error = error.message;
    job.finishedAt = new Date().toISOString();
    emit(job, { type: 'server.failed', source: 'server', job_kind: 'criteria', message: error.message });
    finishStreams(job);
  });
  child.on('close', code => {
    if (job.status === 'cancelled' || job.status === 'failed') return;
    job.exitCode = code;
    job.finishedAt = new Date().toISOString();
    if (job.stdoutBuffer.trim()) parseJsonLines(job, '\n', 'stdoutBuffer');
    if (job.stderrBuffer.trim()) parseJsonLines(job, '\n', 'stderrBuffer');
    try {
      const raw = fs.readFileSync(outputPath, 'utf8').trim();
      const result = JSON.parse(raw);
      if (typeof result.confirmation_message !== 'string' || !result.criteria || typeof result.criteria !== 'object') {
        throw new Error('필수 조건 해석 필드가 없습니다.');
      }
      const requested = Math.min(100, Math.max(1, Number(result.criteria.requested_result_count || result.criteria.result_count || 5)));
      result.criteria.requested_result_count = requested;
      result.criteria.result_count = Math.min(5, Math.max(1, Number(result.criteria.result_count || requested)));
      result.criteria.bot_limit_applied = requested > 5;
      job.result = {
        confirmation_message: result.confirmation_message.trim(),
        assumptions: Array.isArray(result.assumptions) ? result.assumptions.map(value => String(value).trim()).filter(Boolean) : [],
        criteria: result.criteria
      };
      emit(job, { type: 'server.result', source: 'server', job_kind: 'criteria', result: job.result });
      job.status = code === 0 ? 'completed' : 'partial';
      emit(job, { type: 'server.completed', source: 'server', job_kind: 'criteria', exit_code: code, status: job.status });
    } catch (error) {
      job.status = 'failed';
      job.error = code === 0 ? `조건 해석 결과를 읽지 못했습니다: ${error.message}` : `Codex CLI가 종료 코드 ${code}로 끝났습니다.`;
      emit(job, { type: 'server.failed', source: 'server', job_kind: 'criteria', exit_code: code, message: job.error });
    }
    setTimeout(() => finishStreams(job), 100);
  });
  child.stdin.end(prompt, 'utf8');
  return job;
}

function cancelJob(job) {
  if (!job || !['starting', 'running'].includes(job.status)) return false;
  job.status = 'cancelled';
  job.finishedAt = new Date().toISOString();
  if (job.child && !job.child.killed) job.child.kill();
  emit(job, { type: 'server.cancelled', source: 'server', message: '사용자가 조사를 중지했습니다.' });
  setTimeout(() => finishStreams(job), 100);
  return true;
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const types = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.png': 'image/png'
  };
  fs.readFile(filePath, (error, data) => {
    if (error) return json(res, error.code === 'ENOENT' ? 404 : 500, { error: '파일을 열 수 없습니다.' });
    res.writeHead(200, { 'Content-Type': types[ext] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(data);
  });
}

const versionProbe = spawnSync(CODEX_BIN, ['--version'], {
  cwd: WORKSPACE,
  encoding: 'utf8',
  windowsHide: true,
  shell: CODEX_NEEDS_SHELL
});
const codexVersion = String(versionProbe.stdout || versionProbe.stderr || '').trim();

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${HOST}:${PORT}`);
  if (req.method === 'GET' && url.pathname === '/api/health') {
    return json(res, 200, {
      ok: versionProbe.status === 0,
      codex_version: codexVersion || null,
      workspace: WORKSPACE,
      sandbox: CODEX_SANDBOX,
      network_access: CODEX_SANDBOX === 'workspace-write',
      active_run_id: ([...runs.values()].find(job => ['starting', 'running'].includes(job.status)) || {}).id || null
    });
  }

  if (req.method === 'POST' && url.pathname === '/api/runs') {
    try {
      const raw = await readBody(req);
      const body = JSON.parse(raw || '{}');
      const query = String(body.query || '').trim();
      if (query.length < 2 || query.length > 8000) return json(res, 400, { error: '조사 요청은 2~8,000자로 입력해 주세요.' });
      const criteria = body.criteria && typeof body.criteria === 'object' ? body.criteria : {};
      criteria.result_count = Math.min(5, Math.max(1, Number(criteria.result_count || 5)));
      const excludeChannels = (Array.isArray(body.exclude_channels) ? body.exclude_channels : []).slice(0, 100).map(channel => ({
        name: String((channel && channel.name) || '').trim().slice(0, 200),
        url: String((channel && channel.url) || '').trim().slice(0, 1000)
      })).filter(channel => channel.name || channel.url);
      const isExpansion = Boolean(body.is_expansion) && excludeChannels.length > 0;
      const batchNumber = Math.max(1, Math.min(20, Number(body.batch_number || (isExpansion ? 2 : 1))));
      const job = startCodexRun(query, criteria, { isExpansion, batchNumber, excludeChannels });
      return json(res, 202, { runId: job.id, eventsUrl: `/api/runs/${job.id}/events`, isExpansion, batchNumber });
    } catch (error) {
      return json(res, error.statusCode || 400, { error: error.message, activeRunId: error.activeRunId || null });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/examples') {
    try {
      const raw = await readBody(req);
      const body = JSON.parse(raw || '{}');
      const seedQuery = String(body.seed_query || '').trim();
      if (seedQuery.length > 8000) return json(res, 400, { error: '기존 요청은 8,000자 이하로 입력해 주세요.' });
      const job = startExampleRun(seedQuery);
      return json(res, 202, { runId: job.id, eventsUrl: `/api/runs/${job.id}/events` });
    } catch (error) {
      return json(res, error.statusCode || 400, { error: error.message, activeRunId: error.activeRunId || null });
    }
  }

  if (req.method === 'POST' && url.pathname === '/api/criteria') {
    try {
      const raw = await readBody(req);
      const body = JSON.parse(raw || '{}');
      const query = String(body.query || '').trim();
      if (query.length < 2 || query.length > 8000) return json(res, 400, { error: '조건 확인 요청은 2~8,000자로 입력해 주세요.' });
      const job = startCriteriaRun(query);
      return json(res, 202, { runId: job.id, eventsUrl: `/api/runs/${job.id}/events` });
    } catch (error) {
      return json(res, error.statusCode || 400, { error: error.message, activeRunId: error.activeRunId || null });
    }
  }

  const runMatch = url.pathname.match(/^\/api\/runs\/([^/]+)(?:\/(events))?$/);
  if (runMatch) {
    const job = runs.get(runMatch[1]);
    if (!job) return json(res, 404, { error: '실행 기록을 찾을 수 없습니다.' });
    if (req.method === 'GET' && runMatch[2] === 'events') {
      res.writeHead(200, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
      });
      res.write(': connected\n\n');
      for (const event of job.events) res.write(`data: ${JSON.stringify(event)}\n\n`);
      if (['completed', 'partial', 'failed', 'cancelled'].includes(job.status)) return res.end();
      job.listeners.add(res);
      req.on('close', () => job.listeners.delete(res));
      return;
    }
    if (req.method === 'GET') return json(res, 200, publicRun(job));
    if (req.method === 'DELETE') return json(res, cancelJob(job) ? 202 : 409, publicRun(job));
  }

  if (req.method !== 'GET') return json(res, 405, { error: '지원하지 않는 요청입니다.' });
  const relative = url.pathname === '/' ? 'Influencer Finder.dc.html' : decodeURIComponent(url.pathname.slice(1));
  const filePath = path.resolve(ROOT, relative);
  if (filePath !== ROOT && !filePath.startsWith(ROOT + path.sep)) return json(res, 403, { error: '허용되지 않은 경로입니다.' });
  return serveFile(res, filePath);
});

server.listen(PORT, HOST, () => {
  console.log(`YouTube Influencer Finder: http://${HOST}:${PORT}`);
  console.log(`Codex CLI: ${codexVersion || 'not detected'}`);
});

function shutdown() {
  for (const job of runs.values()) cancelJob(job);
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 3000).unref();
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
