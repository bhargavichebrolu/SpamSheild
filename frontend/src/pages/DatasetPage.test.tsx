import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DATASET_RESULTS } from "../test/fixtures";
import { jsonResponse, stubApi } from "../test/helpers";
import { DatasetPage } from "./DatasetPage";

afterEach(() => vi.unstubAllGlobals());

async function renderLoaded() {
  stubApi({ "/api/results/dataset": { body: DATASET_RESULTS } });
  render(<DatasetPage />);
  await screen.findByRole("heading", { name: "Overview" });
}

describe("DatasetPage", () => {
  it("shows a loading state, then the statistics", async () => {
    stubApi({ "/api/results/dataset": { body: DATASET_RESULTS } });
    render(<DatasetPage />);
    expect(screen.getByText("Loading dataset statistics…")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Overview" })).toBeInTheDocument();
  });

  it("shows the licence as not verified, prominently and in the source details", async () => {
    await renderLoaded();
    expect(screen.getByText("Licence: Not verified")).toBeInTheDocument();
    expect(screen.getByTestId("licence")).toHaveTextContent("Not verified");
  });

  it("links to the reported source", async () => {
    await renderLoaded();
    expect(screen.getByRole("link", { name: "https://example.com/test-dataset" })).toHaveAttribute("rel", "noreferrer");
  });

  it("shows the overview, adding up missing values and empty rows", async () => {
    await renderLoaded();
    expect(screen.getByText("7,777", { selector: "dd" })).toBeInTheDocument();
    expect(screen.getByText("Missing values").nextElementSibling).toHaveTextContent("3");
    expect(screen.getByText("Empty text rows").nextElementSibling).toHaveTextContent("7");
  });

  it("shows the label balance as a labelled bar, with the numbers in text too", async () => {
    await renderLoaded();
    expect(screen.getByRole("img", { name: "Ham 62.5%, Spam 37.5%" })).toBeInTheDocument();
    expect(screen.getByText(/Ham: 5,000 rows \(62.5%\)/)).toBeInTheDocument();
    expect(screen.getByText(/Spam: 3,000 rows \(37.5%\)/)).toBeInTheDocument();
  });

  it("shows the source details as text that can wrap, not in a table", async () => {
    await renderLoaded();
    const sha = screen.getByText("test-sha");
    expect(sha.closest("table")).toBeNull();
    expect(screen.getByRole("link", { name: "https://example.com/test-dataset" }).closest("table")).toBeNull();
  });

  it("keeps long descriptions outside tables, so they can't be cut off", async () => {
    await renderLoaded();
    const description = screen.getByText(/rows in, 7,000 kept/);
    expect(description.closest("table")).toBeNull();
    expect(screen.getByText(/Stratified by label/).closest("table")).toBeNull();
  });

  it("shows duplicates and conflicting labels", async () => {
    await renderLoaded();
    const table = within(screen.getByRole("region", { name: "Duplicate checks" }));
    expect(table.getByRole("row", { name: /Exact duplicate/ })).toHaveTextContent("13 texts, 14 rows");
  });

  it("shows message lengths, with limits in numeric order", async () => {
    await renderLoaded();
    const lengths = within(screen.getByRole("region", { name: "Message length in characters" }));
    expect(lengths.getByRole("row", { name: /^Ham/ })).toHaveTextContent("25");
    const over = within(screen.getByRole("region", { name: "Rows over a length" }));
    const rows = over.getAllByRole("row").slice(1).map((row) => row.textContent);
    expect(rows).toEqual(["Over 20,000 characters44", "Over 100,000 characters43"]);
  });

  it("shows the cleaning rules and splits", async () => {
    await renderLoaded();
    const cleaning = within(screen.getByRole("region", { name: "Cleaning rules" }));
    expect(cleaning.getByRole("row", { name: /Repeat of a text/ })).toHaveTextContent("75");
    const splits = within(screen.getByRole("region", { name: "Data splits" }));
    expect(splits.getByRole("row", { name: /train/ })).toHaveTextContent("81");
  });

  it("shows text format checks and marker words", async () => {
    await renderLoaded();
    expect(within(screen.getByRole("region", { name: "How rows write numbers" })).getByRole("row", { name: /Digit style/ })).toHaveTextContent("75.0%");
    expect(within(screen.getByRole("region", { name: "Format checks" })).getByRole("row", { name: /Digits/ })).toHaveTextContent("12.50%");
    expect(within(screen.getByRole("region", { name: "Marker words" })).getByRole("row", { name: /testword/ })).toHaveTextContent("25.00%");
  });

  it("shows no statistics, only an error and a retry, when the API fails", async () => {
    let attempts = 0;
    stubApi({
      "/api/results/dataset": () => {
        attempts += 1;
        return attempts === 1
          ? jsonResponse(503, { error: { code: "results_unavailable", message: "A report is missing.", field: null } })
          : jsonResponse(200, DATASET_RESULTS);
      },
    });
    render(<DatasetPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("A report is missing.");
    expect(screen.queryByRole("heading", { name: "Overview" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Overview" })).toBeInTheDocument();
  });
});
