import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HAM_RESULT, SPAM_RESULT } from "../test/fixtures";
import { PredictionResult, SHORT_MESSAGE_RECOGNISED_WORDS } from "./PredictionResult";

describe("PredictionResult", () => {
  it("shows Spam, with the score labelled as a decision score", () => {
    render(<PredictionResult result={SPAM_RESULT} outOfDate={false} />);
    expect(screen.getByTestId("prediction-label")).toHaveTextContent("Spam");
    const score = screen.getByTestId("decision-score");
    expect(score).toHaveTextContent("+1.500");
    expect(score.parentElement).toHaveTextContent("Decision score");
  });

  it("shows Ham, with a negative score", () => {
    render(<PredictionResult result={HAM_RESULT} outOfDate={false} />);
    expect(screen.getByTestId("prediction-label")).toHaveTextContent("Ham");
    expect(screen.getByTestId("decision-score")).toHaveTextContent("-2.250");
  });

  it("never shows a percentage, and never calls the score a probability or confidence value", () => {
    const { container } = render(<PredictionResult result={SPAM_RESULT} outOfDate={false} />);
    const text = container.textContent ?? "";
    expect(text).not.toContain("%");
    expect(text).not.toMatch(/\bconfidence\b/i);
    expect(text).toContain("It isn't a probability");
    expect(text).not.toMatch(/probability (of|that)/i);
  });

  it(`shows a caution below ${SHORT_MESSAGE_RECOGNISED_WORDS} recognised words`, () => {
    render(<PredictionResult result={{ ...SPAM_RESULT, terms_recognised: 4 }} outOfDate={false} />);
    const caution = screen.getByRole("status");
    expect(caution).toHaveTextContent("Only 4 recognised words");
    expect(caution).toHaveTextContent("a display warning, not a measured reliability boundary");
    expect(caution).toHaveTextContent("It doesn't change the model's prediction");
  });

  it("uses the singular for one recognised word", () => {
    render(<PredictionResult result={{ ...SPAM_RESULT, terms_recognised: 1 }} outOfDate={false} />);
    expect(screen.getByRole("status")).toHaveTextContent("Only 1 recognised word");
  });

  it(`shows no caution at exactly ${SHORT_MESSAGE_RECOGNISED_WORDS} recognised words`, () => {
    render(<PredictionResult result={{ ...SPAM_RESULT, terms_recognised: 5 }} outOfDate={false} />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("doesn't change the label or score when it shows the caution", () => {
    render(<PredictionResult result={{ ...SPAM_RESULT, terms_recognised: 1 }} outOfDate={false} />);
    expect(screen.getByTestId("prediction-label")).toHaveTextContent("Spam");
    expect(screen.getByTestId("decision-score")).toHaveTextContent("+1.500");
  });

  it("says when the text has changed since the result", () => {
    render(<PredictionResult result={SPAM_RESULT} outOfDate />);
    expect(within(screen.getByRole("status")).getByText("The text has changed since this result")).toBeInTheDocument();
  });

  it("shows the recognised words, characters and model version", () => {
    render(<PredictionResult result={SPAM_RESULT} outOfDate={false} />);
    expect(screen.getByTestId("terms-recognised")).toHaveTextContent("8");
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("test-version")).toBeInTheDocument();
  });
});
