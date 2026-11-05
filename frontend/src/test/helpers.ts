import { vi } from "vitest";

type Reply = { status?: number; body: unknown } | "network-error" | (() => Promise<Response> | Response);

export const jsonResponse = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

/**
 * Replace fetch, for automated tests only, with replies chosen by path. A request to any
 * other path fails the test, so a page can't quietly call something unexpected.
 */
export function stubApi(routes: Record<string, Reply>) {
  const fetchStub = vi.fn(async (url: string | URL | Request) => {
    const path = new URL(String(url)).pathname;
    const reply = routes[path];
    if (reply === undefined) {
      throw new Error(`Unexpected request in a test: ${path}`);
    }
    if (reply === "network-error") {
      throw new TypeError("Failed to fetch");
    }
    if (typeof reply === "function") {
      return reply();
    }
    return jsonResponse(reply.status ?? 200, reply.body);
  });
  vi.stubGlobal("fetch", fetchStub);
  return fetchStub;
}
