import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

type FrontendLogEntry = {
  timestamp: string;
  type: string;
  level: "info" | "error";
  sessionId: string;
  route: string;
  details: Record<string, boolean | number | string | string[] | null>;
  receivedAt: string;
  requestId: string;
  remoteIp: string;
  userAgent: string;
};

const RETENTION_WINDOW_MS = 30 * 60 * 1000;

function hasProjectMarkers(root: string): boolean {
  return root.endsWith("demo") || root.endsWith(path.join("projects", "demo"));
}

function resolveProjectRoot(): string {
  let current = process.cwd();

  for (let depth = 0; depth < 5; depth += 1) {
    if (hasProjectMarkers(current)) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }

  return process.cwd();
}

function parseEntries(raw: string): FrontendLogEntry[] {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .flatMap((line) => {
      try {
        return [JSON.parse(line) as FrontendLogEntry];
      } catch {
        return [];
      }
    });
}

export async function appendFrontendLogs(events: FrontendLogEntry[]) {
  const projectRoot = resolveProjectRoot();
  const logDir = path.join(projectRoot, "logs", "frontend");
  const operationsFile = path.join(logDir, "operations.ndjson");
  const summaryFile = path.join(logDir, "summary.json");
  const cutoff = Date.now() - RETENTION_WINDOW_MS;

  await mkdir(logDir, { recursive: true });

  let existingEntries: FrontendLogEntry[] = [];
  try {
    existingEntries = parseEntries(await readFile(operationsFile, "utf8"));
  } catch {
    existingEntries = [];
  }

  const retainedEntries = [...existingEntries, ...events].filter((entry) => {
    const timestamp = Date.parse(entry.timestamp);
    return Number.isFinite(timestamp) && timestamp >= cutoff;
  });

  const eventTypeCounts = retainedEntries.reduce<Record<string, number>>((accumulator, entry) => {
    accumulator[entry.type] = (accumulator[entry.type] ?? 0) + 1;
    return accumulator;
  }, {});

  const summary = {
    generatedAt: new Date().toISOString(),
    logDir,
    logFile: operationsFile,
    retainedMinutes: 30,
    totalEntries: retainedEntries.length,
    activeSessions: [...new Set(retainedEntries.map((entry) => entry.sessionId))].length,
    lastEventAt: retainedEntries.at(-1)?.timestamp ?? null,
    lastRoute: retainedEntries.at(-1)?.route ?? null,
    eventTypeCounts,
  };

  const serializedEntries = retainedEntries.map((entry) => JSON.stringify(entry)).join("\n");
  await writeFile(operationsFile, serializedEntries ? `${serializedEntries}\n` : "", "utf8");
  await writeFile(summaryFile, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

  return {
    keptEntries: retainedEntries.length,
    logDir,
    operationsFile,
    summaryFile,
  };
}