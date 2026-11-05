import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DATASET_RESULTS, HEALTHY, MODELS_RESULTS } from "../test/fixtures";
import { stubApi } from "../test/helpers";
import { HomePage } from "./HomePage";

afterEach(() => vi.unstubAllGlobals());

function renderHome(routes: Parameters<typeof stubApi>[0]) {
  const fetchStub = stubApi({ "/api/health": { body: HEALTHY }, ...routes });
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );
  return fetchStub;
}

const WITH_RESULTS = {
  "/api/results/models": { body: MODELS_RESULTS },
  "/api/results/dataset": { body: DATASET_RESULTS },
};

describe("HomePage", () => {
  it("has one main heading, and the classifier", async () => {
    renderHome(WITH_RESULTS);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Is that email spam?");
    expect(screen.getByLabelText("Email text")).toBeInTheDocument();
    expect(await screen.findByText("F1 on held-out test data")).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("shows headline numbers from the API, including the lower ones", async () => {
    renderHome(WITH_RESULTS);
    const value = async (label: string) => (await screen.findByText(label)).nextElementSibling;
    expect(await value("F1 on held-out test data")).toHaveTextContent("0.6375");
    expect(await value("F1 with no close training match")).toHaveTextContent("0.5500");
    expect(await value("Lowest F1 across text styles")).toHaveTextContent("0.4500");
    expect(await value("Emails in the dataset")).toHaveTextContent("7,777");
  });

  it("says the numbers come from this dataset only", async () => {
    renderHome(WITH_RESULTS);
    expect(await screen.findByText(/Measured on this one dataset only/)).toBeInTheDocument();
  });

  it("shows charts from the API's results", async () => {
    renderHome(WITH_RESULTS);
    const errors = await screen.findByRole("list", { name: "Test errors by similarity to training data" });
    expect(within(errors).getByText("5 ham flagged, 6 spam missed")).toBeInTheDocument();
    expect(screen.getByText(/11 of 11 test errors/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Rows by label: Ham, 5,000 rows/ })).toBeInTheDocument();
  });

  it("explains how it works", () => {
    renderHome(WITH_RESULTS);
    expect(screen.getByRole("heading", { name: "How it works" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Score and explain" })).toBeInTheDocument();
  });

  it("shows no numbers or charts, and adds no extra alert, when results fail", async () => {
    renderHome({ "/api/results/models": "network-error", "/api/results/dataset": "network-error" });
    expect(await screen.findByRole("heading", { level: 1 })).toBeInTheDocument();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByText("F1 on held-out test data")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "What the results show" })).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Email text")).toBeInTheDocument();
  });

  it("still shows model results if only the dataset results fail", async () => {
    renderHome({ "/api/results/models": { body: MODELS_RESULTS }, "/api/results/dataset": "network-error" });
    expect(await screen.findByText("F1 on held-out test data")).toBeInTheDocument();
    expect(screen.queryByText("Emails in the dataset")).not.toBeInTheDocument();
  });
});
