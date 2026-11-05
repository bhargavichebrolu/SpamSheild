import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MODELS_RESULTS } from "../test/fixtures";
import { jsonResponse, stubApi } from "../test/helpers";
import { ModelsPage } from "./ModelsPage";

afterEach(() => vi.unstubAllGlobals());

async function renderLoaded(results = MODELS_RESULTS) {
  stubApi({ "/api/results/models": { body: results } });
  render(<ModelsPage />);
  await screen.findByRole("heading", { name: "Final test results" });
}

describe("ModelsPage", () => {
  it("shows a loading state, then the results", async () => {
    stubApi({ "/api/results/models": { body: MODELS_RESULTS } });
    render(<ModelsPage />);
    expect(screen.getByText("Loading saved results…")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Final test results" })).toBeInTheDocument();
    expect(screen.queryByText("Loading saved results…")).not.toBeInTheDocument();
  });

  it("shows test results exactly as the API gave them, with sample counts", async () => {
    await renderLoaded();
    expect(screen.getByText("0.6375")).toBeInTheDocument();
    const bands = screen.getByRole("region", { name: "Test results by similarity to training data" });
    expect(within(bands).getByRole("row", { name: /Under 0.80/ })).toHaveTextContent("111");
    expect(within(bands).getByRole("row", { name: /Under 0.80/ })).toHaveTextContent("0.5500");
  });

  it("handles a similarity band with no messages", async () => {
    await renderLoaded();
    const bands = screen.getByRole("region", { name: "Test results by similarity to training data" });
    expect(within(bands).getByRole("row", { name: /0.95 and above/ })).toHaveTextContent("No messages");
  });

  it("shows every comparison run, and marks the selected one", async () => {
    await renderLoaded();
    const table = within(screen.getByRole("region", { name: "All model comparison runs" }));
    expect(table.getAllByRole("row")).toHaveLength(MODELS_RESULTS.comparison_runs.length + 1);
    const selected = table.getByRole("row", { name: /\(selected\)/ });
    expect(selected).toHaveTextContent("Single words");
    expect(selected).toHaveAttribute("data-highlight", "true");
  });

  it("shows the selection rule and that it used validation results", async () => {
    await renderLoaded();
    expect(screen.getByText("Test step one")).toBeInTheDocument();
    expect(screen.getByText(/The rule used validation results only/)).toBeInTheDocument();
  });

  it("says when the selected model isn't the highest F1, from the data", async () => {
    await renderLoaded();
    expect(screen.getByText(/The selected model isn't the highest F1/)).toHaveTextContent(
      "words and bigrams scored 0.6125, against 0.6000",
    );
  });

  it("doesn't say that when the selected model is the highest F1", async () => {
    await renderLoaded({ ...MODELS_RESULTS, comparison_runs: [MODELS_RESULTS.comparison_runs[0]!] });
    expect(screen.queryByText(/isn't the highest F1/)).not.toBeInTheDocument();
  });

  it("warns if the results don't describe the saved model", async () => {
    await renderLoaded({
      ...MODELS_RESULTS,
      test_evaluation: { ...MODELS_RESULTS.test_evaluation, report_matches_saved_model: false },
    });
    expect(screen.getByText("These results don't describe the saved model file")).toBeInTheDocument();
  });

  it("shows the source-leakage results with their interpretation note", async () => {
    await renderLoaded();
    expect(screen.getByText("Test note: not proof of generalisation.")).toBeInTheDocument();
    const cross = within(screen.getByRole("region", { name: "Cross-style results" }));
    expect(cross.getByRole("row", { name: /^Digit style/ })).toHaveTextContent("0.4500");
    expect(cross.getByRole("row", { name: /matched size/ })).toHaveTextContent("0.4600");
    const markers = within(screen.getByRole("region", { name: "Marker removal results" }));
    expect(markers.getByRole("row", { name: /\(used\)/ })).toHaveTextContent("0.5900");
  });

  it("shows the limitations", async () => {
    await renderLoaded();
    expect(screen.getByText("Test limitation one")).toBeInTheDocument();
  });

  it("shows no results, only an error and a retry, when the API fails", async () => {
    let attempts = 0;
    stubApi({
      "/api/results/models": () => {
        attempts += 1;
        return attempts === 1
          ? jsonResponse(503, { error: { code: "results_unavailable", message: "A report is missing.", field: null } })
          : jsonResponse(200, MODELS_RESULTS);
      },
    });
    render(<ModelsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("A report is missing.");
    expect(screen.queryByRole("heading", { name: "Final test results" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Final test results" })).toBeInTheDocument();
  });

  it("explains when the API can't be reached", async () => {
    stubApi({ "/api/results/models": "network-error" });
    render(<ModelsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("The API can't be reached");
  });
});
