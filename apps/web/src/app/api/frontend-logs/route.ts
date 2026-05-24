import { headers } from "next/headers";
import { NextResponse } from "next/server";

import { appendFrontendLogs } from "@/server/frontend-log-store";

export const runtime = "nodejs";

type IncomingLogEvent = {
  timestamp?: string;
  type?: string;
  level?: "info" | "error";
  sessionId?: string;
  route?: string;
  details?: Record<string, boolean | number | string | string[] | null>;
};

export async function POST(request: Request) {
  const requestHeaders = await headers();
  const requestId = requestHeaders.get("x-request-id") ?? crypto.randomUUID();
  const remoteIp = requestHeaders.get("x-forwarded-for") ?? requestHeaders.get("x-real-ip") ?? "unknown";
  const userAgent = requestHeaders.get("user-agent") ?? "unknown";

  let payload: { events?: IncomingLogEvent[] };
  try {
    payload = (await request.json()) as { events?: IncomingLogEvent[] };
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  const rawEvents = Array.isArray(payload.events) ? payload.events : [];
  if (rawEvents.length === 0) {
    return NextResponse.json({ accepted: 0 });
  }

  const now = new Date().toISOString();
  const events = rawEvents
    .filter((event) => typeof event.type === "string" && typeof event.sessionId === "string" && typeof event.route === "string")
    .slice(0, 100)
    .map((event) => ({
      timestamp: event.timestamp ?? now,
      type: event.type ?? "unknown",
      level: event.level === "error" ? "error" : "info",
      sessionId: event.sessionId ?? "unknown",
      route: event.route ?? "/",
      details: event.details ?? {},
      receivedAt: now,
      requestId,
      remoteIp,
      userAgent,
    }));

  const result = await appendFrontendLogs(events as any);
  return NextResponse.json({ accepted: events.length, keptEntries: result.keptEntries });
}