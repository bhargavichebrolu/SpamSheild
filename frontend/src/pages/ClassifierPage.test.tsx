import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HAM_RESULT, HEALTHY, SPAM_RESULT } from "../test/fixtures";
import { jsonResponse, stubApi } from "../test/helpers";
import { ClassifierPage } from "./ClassifierPage";

afterEach(() => vi.unstubAllGlobals());

const type = (text: string) => userEvent.type(screen.getByLabelText("Email text"), text);
const classify = () => userEvent.click(screen.getByRole("button", { name: "Classify" }));

describe("ClassifierPage", () => {
  it("classifies text and shows the API's result", async () => {
    const fetchStub = stubApi({ "/api/health": { body: HEALTHY }, "/api/classify": { body: SPAM_RESULT } });
    render(<ClassifierPage />);
    await type("free prize");
    await classify();

    expect(await screen.findByTestId("prediction-label")).toHaveTextContent("Spam");
    expect(screen.getByTestId("decision-score")).toHaveTextContent("+1.500");
    const call = fetchStub.mock.calls.find(([url]) => String(url).endsWith("/api/classify")) as unknown as [string, RequestInit];
    expect(JSON.parse(call[1].body as string)).toEqual({ text: "free prize" });
  });

  it("shows a loading state while waiting", async () => {
    let finish: (response: Response) => void = () => {};
    stubApi({
      "/api/health": { body: HEALTHY },
      "/api/classify": () => new Promise<Response>((resolve) => (finish = resolve)),
    });
    render(<ClassifierPage />);
    await type("free prize");
    await classify();

    expect(screen.getByText("Classifying your text…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Classifying…" })).toBeDisabled();

    finish(jsonResponse(200, SPAM_RESULT));
    expect(await screen.findByTestId("prediction-label")).toBeInTheDocument();
    expect(screen.queryByText("Classifying your text…")).not.toBeInTheDocument();
  });

  it("shows the server's message when the text can't be classified", async () => {
    stubApi({
      "/api/health": { body: HEALTHY },
      "/api/classify": {
        status: 422,
        body: { error: { code: "no_recognised_terms", message: "None of these words are known.", field: "text" } },
      },
    });
    render(<ClassifierPage />);
    await type("zzzz");
    await classify();

    expect(await screen.findByRole("alert")).toHaveTextContent("None of these words are known.");
    expect(screen.queryByTestId("prediction-label")).not.toBeInTheDocument();
  });

  it("shows no result, and how to start the API, when it can't be reached", async () => {
    stubApi({ "/api/health": "network-error", "/api/classify": "network-error" });
    render(<ClassifierPage />);

    const banner = await screen.findByRole("alert");
    expect(banner).toHaveTextContent("The API can't be reached");
    expect(banner).toHaveTextContent("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000");

    await type("free prize");
    await classify();
    await waitFor(() => expect(screen.getAllByRole("alert")).toHaveLength(2));
    expect(screen.queryByTestId("prediction-label")).not.toBeInTheDocument();
  });

  it("explains an unavailable model, and shows no made-up result", async () => {
    stubApi({
      "/api/health": () =>
        jsonResponse(503, { status: "unavailable", model_loaded: false, model_version: null, detail: "The model file was not found." }),
      "/api/classify": {
        status: 503,
        body: { error: { code: "model_unavailable", message: "The model file was not found.", field: null } },
      },
    });
    render(<ClassifierPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("The model file was not found.");

    await type("free prize");
    await classify();
    await waitFor(() => expect(screen.getAllByRole("alert")).toHaveLength(2));
    expect(screen.queryByTestId("prediction-label")).not.toBeInTheDocument();
  });

  it("can try again after a failure", async () => {
    let attempts = 0;
    stubApi({
      "/api/health": { body: HEALTHY },
      "/api/classify": () => {
        attempts += 1;
        return attempts === 1
          ? jsonResponse(500, { error: { code: "internal_error", message: "It failed.", field: null } })
          : jsonResponse(200, SPAM_RESULT);
      },
    });
    render(<ClassifierPage />);
    await type("free prize");
    await classify();
    await userEvent.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByTestId("prediction-label")).toHaveTextContent("Spam");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("marks a result as out of date when the text changes", async () => {
    stubApi({ "/api/health": { body: HEALTHY }, "/api/classify": { body: SPAM_RESULT } });
    render(<ClassifierPage />);
    await type("free prize");
    await classify();
    await screen.findByTestId("prediction-label");
    expect(screen.queryByText("The text has changed since this result")).not.toBeInTheDocument();

    await type(" more");
    expect(screen.getByText("The text has changed since this result")).toBeInTheDocument();
  });

  it("ignores a slow response from an earlier request", async () => {
    const replies: ((response: Response) => void)[] = [];
    stubApi({
      "/api/health": { body: HEALTHY },
      "/api/classify": () => new Promise<Response>((resolve) => replies.push(resolve)),
    });
    render(<ClassifierPage />);
    await type("first");
    await classify();
    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    await type("second");
    await classify();

    replies[1]!(jsonResponse(200, HAM_RESULT));
    expect(await screen.findByTestId("prediction-label")).toHaveTextContent("Ham");

    replies[0]!(jsonResponse(200, SPAM_RESULT));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.getByTestId("prediction-label")).toHaveTextContent("Ham");
  });

  it("clears the text, the result and any pending request", async () => {
    stubApi({ "/api/health": { body: HEALTHY }, "/api/classify": { body: SPAM_RESULT } });
    render(<ClassifierPage />);
    await type("free prize");
    await classify();
    await screen.findByTestId("prediction-label");

    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.getByLabelText("Email text")).toHaveValue("");
    expect(screen.queryByTestId("prediction-label")).not.toBeInTheDocument();
  });

  it("doesn't save the text in the browser", async () => {
    stubApi({ "/api/health": { body: HEALTHY }, "/api/classify": { body: SPAM_RESULT } });
    render(<ClassifierPage />);
    await type("private message text");
    await classify();
    await screen.findByTestId("prediction-label");

    expect(JSON.stringify({ ...localStorage })).not.toContain("private");
    expect(JSON.stringify({ ...sessionStorage })).not.toContain("private");
    expect(window.location.href).not.toContain("private");
  });
});
