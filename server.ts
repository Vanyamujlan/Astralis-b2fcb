import 'dotenv/config';
import {type ChildProcess, spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import express from 'express';
import {createServer as createViteServer} from 'vite';

const PORT = Number(process.env.PORT || 3000);
const TOKEN_REDACT_RE = /\b\d{6,15}:[A-Za-z0-9_-]{20,}\b/g;

function redactSecrets(text: string): string {
  let out = text.replace(TOKEN_REDACT_RE, '[REDACTED_BOT_TOKEN]');
  for (const key of ['BOT_TOKEN', 'BOT_TOCKEN', 'TELEGRAM_BOT_TOKEN', 'FIREBASE_PRIVATE_KEY', 'AI_API_KEY']) {
    const val = process.env[key];
    if (val && val.length >= 8 && out.includes(val)) {
      out = out.split(val).join('[REDACTED]');
    }
  }
  return out;
}

function resolveBotToken(): {token: string | null; sourceKey: string | null} {
  const candidates = [
    'BOT_TOKEN',
    'TELEGRAM_BOT_TOKEN',
    'BOT_TOCKEN',
    'bot_token',
    'bot_tocken',
    'bot Tocken',
    'bot tocken',
  ];
  for (const key of candidates) {
    const val = process.env[key]?.trim();
    if (val) {
      return {token: val, sourceKey: key};
    }
  }
  // Case-insensitive scan for any env key containing BOT and TOK/TOCK
  for (const [key, rawVal] of Object.entries(process.env)) {
    const upper = key.toUpperCase();
    if (upper.includes('BOT') && (upper.includes('TOKEN') || upper.includes('TOCKEN'))) {
      const val = rawVal?.trim();
      if (val) {
        return {token: val, sourceKey: key};
      }
    }
  }
  return {token: null, sourceKey: null};
}

interface BotRuntimeState {
  running: boolean;
  pid: number | null;
  hasBotToken: boolean;
  tokenSourceKey: string | null;
  hasFirebaseAdmin: boolean;
  storageMode: 'firestore' | 'local' | 'unconfigured';
  botUsername: string | null;
  startedAt: string | null;
  exitCode: number | null;
  lastError: string | null;
  firebaseWarning: string | null;
  recentLogs: string[];
}

const botState: BotRuntimeState = {
  running: false,
  pid: null,
  hasBotToken: false,
  tokenSourceKey: null,
  hasFirebaseAdmin: false,
  storageMode: 'unconfigured',
  botUsername: null,
  startedAt: null,
  exitCode: null,
  lastError: null,
  firebaseWarning: null,
  recentLogs: [],
};

let botProcess: ChildProcess | null = null;

function pushLog(line: string) {
  const clean = redactSecrets(line.trim());
  if (!clean) {
    return;
  }
  botState.recentLogs.push(clean);
  if (botState.recentLogs.length > 20) {
    botState.recentLogs.shift();
  }
  if (clean.includes('falling back to local JSON store')) {
    botState.storageMode = 'local';
    botState.firebaseWarning = clean;
  }
  if (clean.includes('Failed to initialize Firebase/Firestore')) {
    botState.firebaseWarning = clean;
  }
  const connectedMatch = clean.match(/Telegram Bot API connected successfully:\s*@([A-Za-z0-9_]+)/);
  if (connectedMatch) {
    botState.botUsername = connectedMatch[1];
    botState.lastError = null;
  }
  if (clean.includes('ERROR') || clean.includes('Traceback')) {
    if (!clean.includes('Failed to initialize Firebase/Firestore')) {
      botState.lastError = clean;
    }
  }
}

function startPythonBot() {
  const {token, sourceKey} = resolveBotToken();
  botState.hasBotToken = Boolean(token);
  botState.tokenSourceKey = sourceKey;
  botState.hasFirebaseAdmin = Boolean(
    process.env.FIREBASE_PROJECT_ID?.trim() &&
      process.env.FIREBASE_CLIENT_EMAIL?.trim() &&
      process.env.FIREBASE_PRIVATE_KEY?.trim(),
  );

  if (!token) {
    botState.running = false;
    botState.storageMode = 'unconfigured';
    botState.lastError = 'BOT_TOKEN is not set in environment secrets.';
    console.warn('[astralio-runner] BOT_TOKEN not found in process.env; Python Telegram bot not started.');
    return;
  }

  botState.storageMode = botState.hasFirebaseAdmin ? 'firestore' : 'local';

  const venvPython = path.resolve(process.cwd(), '.venv', 'bin', 'python');
  const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python3';

  const childEnv: NodeJS.ProcessEnv = {
    ...process.env,
    BOT_TOKEN: token,
    PYTHONUNBUFFERED: '1',
  };

  console.info(
    `[astralio-runner] Spawning Astralio bot (${pythonBin} -m astralio.main) | tokenKey=${sourceKey} | storage=${botState.storageMode}`,
  );

  const child = spawn(pythonBin, ['-m', 'astralio.main'], {
    cwd: process.cwd(),
    env: childEnv,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  botProcess = child;
  botState.running = true;
  botState.pid = child.pid ?? null;
  botState.startedAt = new Date().toISOString();
  botState.exitCode = null;
  botState.lastError = null;

  child.stdout?.on('data', (chunk: Buffer) => {
    for (const line of chunk.toString('utf-8').split(/\r?\n/)) {
      if (line.trim()) {
        pushLog(line);
        console.log(`[astralio-bot] ${redactSecrets(line)}`);
      }
    }
  });

  child.stderr?.on('data', (chunk: Buffer) => {
    for (const line of chunk.toString('utf-8').split(/\r?\n/)) {
      if (line.trim()) {
        pushLog(line);
        console.error(`[astralio-bot] ${redactSecrets(line)}`);
      }
    }
  });

  child.on('exit', (code, signal) => {
    botState.running = false;
    botState.pid = null;
    botState.exitCode = code;
    botProcess = null;
    console.warn(`[astralio-runner] Astralio bot exited (code=${code}, signal=${signal})`);
  });

  child.on('error', (err) => {
    botState.running = false;
    botState.pid = null;
    botState.lastError = redactSecrets(err.message);
    botProcess = null;
    console.error(`[astralio-runner] Failed to start Astralio bot: ${redactSecrets(err.message)}`);
  });
}

function stopPythonBot() {
  if (botProcess && !botProcess.killed) {
    botProcess.kill('SIGTERM');
    botProcess = null;
  }
}

process.on('SIGINT', () => {
  stopPythonBot();
  process.exit(0);
});
process.on('SIGTERM', () => {
  stopPythonBot();
  process.exit(0);
});
process.on('exit', () => {
  stopPythonBot();
});

async function startServer() {
  const app = express();

  app.get('/api/bot-status', (_req, res) => {
    res.json({
      running: botState.running,
      pid: botState.pid,
      hasBotToken: botState.hasBotToken,
      tokenSourceKey: botState.tokenSourceKey,
      hasFirebaseAdmin: botState.hasFirebaseAdmin,
      storageMode: botState.storageMode,
      botUsername: botState.botUsername,
      startedAt: botState.startedAt,
      exitCode: botState.exitCode,
      lastError: botState.lastError,
      firebaseWarning: botState.firebaseWarning,
      recentLogs: botState.recentLogs,
    });
  });

  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: {middlewareMode: true},
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.resolve(process.cwd(), 'dist');
    app.use(express.static(distDir));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distDir, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[astralio-server] Listening on http://0.0.0.0:${PORT}`);
    startPythonBot();
  });
}

void startServer();
