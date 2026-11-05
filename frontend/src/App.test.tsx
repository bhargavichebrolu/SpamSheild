import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { DATASET_RESULTS, HEALTHY, MODELS_RESULTS } from "./test/fixtures";
import { stubApi } from "./test/helpers";

afterEach(() => vi.unstubAllGlobals());

function renderAt(path: string) {
  stubApi({
    "/api/health": { body: HEALTHY },
    "/api/results/models": { body: MODELS_RESULTS },
    "/api/results/dataset": { body: DATASET_RESULTS },
  });
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App", () => {
  it("opens on the classifier", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { name: "Classify an email", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Classify" })).toHaveAttribute("aria-current", "page");
  });

  it("moves between all three pages", async () => {
    renderAt("/");
    await userEvent.click(screen.getByRole("link", { name: "Models" }));
    expect(screen.getByRole("heading", { name: "Model comparison", level: 1 })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Dataset" }));
    expect(screen.getByRole("heading", { name: "Dataset explorer", level: 1 })).toBeInTheDocument();
  });

  it("sets each page's title", async () => {
    renderAt("/models");
    await waitFor(() => expect(document.title).toBe("Model comparison | SpamShield AI"));
  });

  it("handles an unknown page", () => {
    renderAt("/not-a-page");
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });

  it("says on every page that this is a prototype", () => {
    renderAt("/dataset");
    expect(screen.getByText(/A learning and research prototype, not an email security product/)).toBeInTheDocument();
  });

  it("offers a way to skip to the main content", () => {
    renderAt("/");
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute("href", "#main-content");
  });
});
