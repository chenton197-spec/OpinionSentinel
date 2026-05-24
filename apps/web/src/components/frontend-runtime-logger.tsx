"use client";

import { useEffect, useEffectEvent, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";

type FrontendLogEvent = {
  timestamp: string;
  type: string;
  level: "info" | "error";
  sessionId: string;
  route: string;
  details: Record<string, boolean | number | string | string[] | null>;
};

const SESSION_STORAGE_KEY = "brand-ops-frontend-log-session";
const FLUSH_INTERVAL_MS = 10000;
const HEARTBEAT_INTERVAL_MS = 60000;
const MAX_BATCH_SIZE = 12;

function getSessionId(): string {
  if (typeof window === "undefined") {
    return "server";
  }

  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const sessionId = window.crypto.randomUUID();
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
}

function truncate(value: string, maxLength = 120): string {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength)}...`;
}

function currentRoute(pathname: string | null, search: string): string {
  return search ? `${pathname ?? ""}?${search}` : pathname ?? "/";
}

function describeElement(target: EventTarget | null): Record<string, boolean | number | string | string[] | null> {
  if (!(target instanceof Element)) {
    return { tag: "unknown" };
  }

  const element = target.closest("button, a, input, select, textarea, form, [role]") ?? target;
  const inputElement = element instanceof HTMLInputElement ? element : null;
  const text = truncate((element.textContent ?? "").replace(/\s+/g, " ").trim(), 80);
  const className = typeof element.className === "string" ? truncate(element.className, 120) : "";

  return {
    tag: element.tagName.toLowerCase(),
    id: element.id || null,
    name: element.getAttribute("name"),
    type: inputElement?.type ?? element.getAttribute("type"),
    role: element.getAttribute("role"),
    href: element.getAttribute("href"),
    action: element.getAttribute("action"),
    text,
    className,
    checked: inputElement?.checked ?? false,
    valueLength: inputElement?.type === "password" ? 0 : (inputElement?.value.length ?? 0),
  };
}

function stringifyError(error: unknown): string {
  if (error instanceof Error) {
    return `${error.name}: ${error.message}`;
  }
  if (typeof error === "string") {
    return error;
  }
  return "unknown error";
}

export function FrontendRuntimeLogger() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const sessionIdRef = useRef<string>("pending");
  const queueRef = useRef<FrontendLogEvent[]>([]);
  const previousRouteRef = useRef<string>("");

  const enqueue = useEffectEvent((type: string, details: Record<string, boolean | number | string | string[] | null>, level: "info" | "error" = "info") => {
    const route = currentRoute(pathname, searchParams.toString());
    queueRef.current.push({
      timestamp: new Date().toISOString(),
      type,
      level,
      sessionId: sessionIdRef.current,
      route,
      details,
    });
  });

  const flush = useEffectEvent(async (reason: string) => {
    if (queueRef.current.length === 0) {
      return;
    }

    const batch = queueRef.current.splice(0, queueRef.current.length);

    try {
      await fetch("/api/frontend-logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason, events: batch }),
        keepalive: true,
      });
    } catch {
      queueRef.current.unshift(...batch);
    }
  });

  useEffect(() => {
    sessionIdRef.current = getSessionId();
    enqueue("app_boot", {
      language: navigator.language,
      online: navigator.onLine,
      platform: navigator.platform,
      referrer: document.referrer || null,
      title: document.title,
      userAgent: truncate(navigator.userAgent, 180),
      viewport: `${window.innerWidth}x${window.innerHeight}`,
    });
    void flush("boot");
  }, []);

  useEffect(() => {
    const route = currentRoute(pathname, searchParams.toString());
    const previousRoute = previousRouteRef.current || null;
    previousRouteRef.current = route;
    enqueue("route_view", {
      previousRoute,
      title: document.title,
      visibilityState: document.visibilityState,
    });
    void flush("route_view");
  }, [pathname, searchParams]);

  useEffect(() => {
    const originalFetch = window.fetch.bind(window);
    const originalConsoleError = window.console.error.bind(window.console);

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const startedAt = performance.now();
      const method = init?.method ?? (input instanceof Request ? input.method : "GET");
      const url = typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;

      if (url.includes("/api/frontend-logs")) {
        return originalFetch(input, init);
      }

      try {
        const response = await originalFetch(input, init);
        enqueue("network_response", {
          durationMs: Math.round(performance.now() - startedAt),
          method,
          ok: response.ok,
          status: response.status,
          url: truncate(url, 200),
        });

        if (queueRef.current.length >= MAX_BATCH_SIZE) {
          void flush("network_batch");
        }

        return response;
      } catch (error) {
        enqueue("network_error", {
          durationMs: Math.round(performance.now() - startedAt),
          error: stringifyError(error),
          method,
          url: truncate(url, 200),
        }, "error");

        if (queueRef.current.length >= MAX_BATCH_SIZE) {
          void flush("network_error_batch");
        }

        throw error;
      }
    };

    window.console.error = (...args: unknown[]) => {
      enqueue("console_error", {
        args: args.map((item) => truncate(String(item), 160)),
      }, "error");
      originalConsoleError(...args);
    };

    const handleClick = (event: MouseEvent) => {
      enqueue("ui_click", describeElement(event.target));
      if (queueRef.current.length >= MAX_BATCH_SIZE) {
        void flush("click_batch");
      }
    };

    const handleChange = (event: Event) => {
      enqueue("ui_change", describeElement(event.target));
    };

    const handleSubmit = (event: SubmitEvent) => {
      enqueue("ui_submit", describeElement(event.target));
      void flush("submit");
    };

    const handleVisibilityChange = () => {
      enqueue("visibility_change", {
        online: navigator.onLine,
        visibilityState: document.visibilityState,
      });
      if (document.visibilityState === "hidden") {
        void flush("hidden");
      }
    };

    const handleOnline = () => enqueue("network_status", { online: true });
    const handleOffline = () => enqueue("network_status", { online: false }, "error");

    const handleError = (event: ErrorEvent) => {
      enqueue("runtime_error", {
        colno: event.colno,
        filename: event.filename || null,
        lineno: event.lineno,
        message: event.message,
      }, "error");
      void flush("runtime_error");
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      enqueue("unhandled_rejection", {
        reason: stringifyError(event.reason),
      }, "error");
      void flush("unhandled_rejection");
    };

    window.addEventListener("click", handleClick, true);
    window.addEventListener("change", handleChange, true);
    window.addEventListener("submit", handleSubmit, true);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleUnhandledRejection);

    const heartbeatTimer = window.setInterval(() => {
      enqueue("runtime_heartbeat", {
        online: navigator.onLine,
        queueSize: queueRef.current.length,
        visibilityState: document.visibilityState,
      });
      void flush("heartbeat");
    }, HEARTBEAT_INTERVAL_MS);

    const flushTimer = window.setInterval(() => {
      void flush("interval");
    }, FLUSH_INTERVAL_MS);

    return () => {
      window.fetch = originalFetch;
      window.console.error = originalConsoleError;
      window.removeEventListener("click", handleClick, true);
      window.removeEventListener("change", handleChange, true);
      window.removeEventListener("submit", handleSubmit, true);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleUnhandledRejection);
      window.clearInterval(heartbeatTimer);
      window.clearInterval(flushTimer);
      void flush("unmount");
    };
  }, []);

  return null;
}