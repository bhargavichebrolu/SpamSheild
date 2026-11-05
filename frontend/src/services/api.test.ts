import { afterEach, describe, expect, it, vi } from "vitest";

import { HEALTHY, SPAM_RESULT } from "../test/fixtures";
import { jsonResponse, stubApi } from "../test/helpers";
import { API_BASE_URL, ApiError, classifyEmail, getDatasetResults, getHealth, getModelsResults, REQUEST_TIMEOUT_MS } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("classifyEmail", () => {
  it("sends the text to the real endpoint as JSON", async () => {
    const fetchStub = stubApi({ "/api/classify": { body: SPAM_RESULT } });
    await expect(classifyEmail("some text")).resolves.toEqual(SPAM_RESULT);

    const [url, init] = fetchStub.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/api/classify`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ text: "some text" });
  });

  it("reports the server's code and message for a refused request", async () => {
    stubApi({
      "/api/classify": { status: 422, body: { error: { code: "text_too_long", message: "Too long.", field: "text" } } },
    });
    await expect(classifyEmail("x")).rejects.toMatchObject({
      name: "ApiError",
      kind: "server",
      status: 422,
      code: "text_too_long",
      message: "Too long.",
    });
  });

  it("reports a network failure separately from a server response", async () => {
    stubApi({ "/api/classify": "network-error" });
    await expect(classifyEmail("x")).rejects.toMatchObject({ kind: "network", status: null });
  });

  it("reports a response that isn't JSON", async () => {
    stubApi({ "/api/classify": () => new Response("<html>", { status: 200 }) });
    await expect(classifyEmail("x")).rejects.toMatchObject({ kind: "invalid_response" });
  });

  it("gives a generic message when an error response has no details", async () => {
    stubApi({ "/api/classify": { status: 500, body: {} } });
    await expect(classifyEmail("x")).rejects.toMatchObject({
      kind: "server",
      status: 500,
      message: "The API couldn't complete this request.",
    });
  });

  it("reports a timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
          }),
      ),
    );
    const request = classifyEmail("x");
    const outcome = expect(request).rejects.toMatchObject({ kind: "timeout" });
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
    await outcome;
  });

  it("passes on a cancellation without turning it into an error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
          }),
      ),
    );
    const controller = new AbortController();
    const request = classifyEmail("x", controller.signal);
    controller.abort();
    const error = await request.catch((reason: unknown) => reason);
    expect(error).not.toBeInstanceOf(ApiError);
  });
});

describe("getHealth", () => {
  it("returns a healthy response", async () => {
    stubApi({ "/api/health": { body: HEALTHY } });
    await expect(getHealth()).resolves.toEqual(HEALTHY);
  });

  it("treats a 503 as a normal answer explaining the problem", async () => {
    const body = { status: "unavailable", model_loaded: false, model_version: null, detail: "No model." };
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(503, body)));
    await expect(getHealth()).resolves.toEqual(body);
  });
});

describe("saved results", () => {
  it("calls the real endpoints", async () => {
    const fetchStub = stubApi({
      "/api/results/models": { body: { models: true } },
      "/api/results/dataset": { body: { dataset: true } },
    });
    await expect(getModelsResults()).resolves.toEqual({ models: true });
    await expect(getDatasetResults()).resolves.toEqual({ dataset: true });
    expect(fetchStub).toHaveBeenCalledTimes(2);
  });

  it("reports unavailable results", async () => {
    stubApi({
      "/api/results/models": {
        status: 503,
        body: { error: { code: "results_unavailable", message: "Report missing.", field: null } },
      },
    });
    await expect(getModelsResults()).rejects.toMatchObject({ status: 503, code: "results_unavailable" });
  });
});
