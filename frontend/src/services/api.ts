/**
 * Every call to the backend goes through this file. It tells apart the ways a request can
 * fail, so that pages can show the right message. There are no sample or fallback results:
 * if the backend can't answer, the page shows an error rather than made-up data.
 */

import type { ClassifyResponse, DatasetResults, HealthResponse, ModelsResults } from "../types/api";

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const REQUEST_TIMEOUT_MS = 30_000;

export type ApiErrorKind = "network" | "timeout" | "server" | "invalid_response";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | null;
  readonly code: string | null;

  constructor(kind: ApiErrorKind, message: string, status: number | null = null, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

async function send(path: string, init: RequestInit, signal?: AbortSignal): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  const forwardAbort = () => controller.abort();
  signal?.addEventListener("abort", forwardAbort);

  try {
    return await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch (error) {
    // A cancelled request isn't a failure, so the caller decides what to do with it.
    if (signal?.aborted) {
      throw error;
    }
    if (timedOut) {
      throw new ApiError("timeout", "The API took too long to respond.");
    }
    throw new ApiError("network", "The API can't be reached.");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forwardAbort);
  }
}

async function readJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("invalid_response", "The API sent a response that couldn't be read.", response.status);
  }
}

async function readResult<T>(response: Response): Promise<T> {
  if (response.ok) {
    return readJson<T>(response);
  }
  const body = await readJson<{ error?: { code?: string; message?: string } }>(response);
  throw new ApiError(
    "server",
    body.error?.message ?? "The API couldn't complete this request.",
    response.status,
    body.error?.code ?? null,
  );
}

export async function classifyEmail(text: string, signal?: AbortSignal): Promise<ClassifyResponse> {
  const response = await send(
    "/api/classify",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    },
    signal,
  );
  return readResult<ClassifyResponse>(response);
}

/** A 503 from this endpoint is a normal answer: it explains why the model isn't loaded. */
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await send("/api/health", { method: "GET" }, signal);
  if (response.status === 503) {
    return readJson<HealthResponse>(response);
  }
  return readResult<HealthResponse>(response);
}

export async function getModelsResults(signal?: AbortSignal): Promise<ModelsResults> {
  return readResult<ModelsResults>(await send("/api/results/models", { method: "GET" }, signal));
}

export async function getDatasetResults(signal?: AbortSignal): Promise<DatasetResults> {
  return readResult<DatasetResults>(await send("/api/results/dataset", { method: "GET" }, signal));
}
