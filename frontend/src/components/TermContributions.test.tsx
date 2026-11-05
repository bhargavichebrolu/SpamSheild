import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HAM_RESULT, SPAM_RESULT } from "../test/fixtures";
import { TermContributions } from "./TermContributions";

const renderSpam = () => render(<TermContributions explanation={SPAM_RESULT.explanation} score={SPAM_RESULT.score} />);

describe("TermContributions", () => {
  it("lists each term with its contribution, under the right direction", () => {
    renderSpam();
    const spam = within(screen.getByRole("region", { name: "Pushed towards spam" }));
    expect(spam.getByText("prize")).toBeInTheDocument();
    expect(spam.getByText("+0.750")).toBeInTheDocument();

    const ham = within(screen.getByRole("region", { name: "Pushed towards ham" }));
    expect(ham.getByText(/escapenumber/)).toBeInTheDocument();
    expect(ham.getByText("-0.500")).toBeInTheDocument();
  });

  it("explains that escapenumber means a number", () => {
    renderSpam();
    expect(screen.getByText("escapenumber (a number)")).toBeInTheDocument();
  });

  it("shows the API's caution about what the terms mean", () => {
    renderSpam();
    expect(screen.getByText("Test note: these terms do not prove why.")).toBeInTheDocument();
  });

  it("shows how the parts add up to the decision score", () => {
    renderSpam();
    const table = screen.getByRole("table", { name: "How the decision score adds up" });
    const row = (name: RegExp) => within(table).getByRole("row", { name });
    expect(row(/starting score/)).toHaveTextContent("+0.750");
    expect(row(/towards spam/)).toHaveTextContent("+1.000");
    expect(row(/towards ham/)).toHaveTextContent("-0.500");
    expect(row(/other terms/)).toHaveTextContent("+0.250");
    expect(row(/Decision score/)).toHaveTextContent("+1.500");
  });

  it("sizes bars on one shared scale, with the largest contribution at full width", () => {
    const { container } = renderSpam();
    const widths = [...container.querySelectorAll<HTMLElement>("li [title]")].map((bar) => parseFloat(bar.style.width));
    expect(widths).toHaveLength(3);
    expect(widths[0]).toBeCloseTo(100, 3);
    expect(widths[1]).toBeCloseTo((0.25 / 0.75) * 100, 3);
    expect(widths[2]).toBeCloseTo((0.5 / 0.75) * 100, 3);
  });

  it("says when no terms pushed in a direction", () => {
    render(<TermContributions explanation={HAM_RESULT.explanation} score={HAM_RESULT.score} />);
    const spam = within(screen.getByRole("region", { name: "Pushed towards spam" }));
    expect(spam.getByText("None in this message.")).toBeInTheDocument();
  });
});
