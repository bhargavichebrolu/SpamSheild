import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ClassifierForm, MAX_INPUT_CHARACTERS } from "./ClassifierForm";

function setup(text: string, loading = false) {
  const handlers = { onTextChange: vi.fn(), onSubmit: vi.fn(), onClear: vi.fn() };
  render(<ClassifierForm text={text} loading={loading} {...handlers} />);
  return handlers;
}

describe("ClassifierForm", () => {
  it("has a labelled text box", () => {
    setup("");
    expect(screen.getByLabelText("Email text")).toBeInTheDocument();
  });

  it.each(["", "   ", "\n\t"])("disables Classify for blank text %j", (text) => {
    setup(text);
    expect(screen.getByRole("button", { name: "Classify" })).toBeDisabled();
  });

  it("submits valid text", async () => {
    const { onSubmit } = setup("some text");
    await userEvent.click(screen.getByRole("button", { name: "Classify" }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("doesn't submit blank text with the Enter key or a form submission", () => {
    const { onSubmit } = setup("   ");
    fireEvent.submit(screen.getByRole("button", { name: "Classify" }).closest("form")!);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows a loading state, and can't be submitted twice", () => {
    const { onSubmit } = setup("some text", true);
    const button = screen.getByRole("button", { name: "Classifying…" });
    expect(button).toBeDisabled();
    fireEvent.submit(button.closest("form")!);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("counts characters against the limit", () => {
    setup("abc");
    expect(screen.getByText(`3 of ${MAX_INPUT_CHARACTERS.toLocaleString("en-GB")} characters`)).toBeInTheDocument();
  });

  it("warns when over the limit, and leaves the server to refuse it", () => {
    setup("a".repeat(MAX_INPUT_CHARACTERS + 5));
    expect(screen.getByText(/5 over the limit/)).toBeInTheDocument();
    expect(screen.getByLabelText("Email text")).toBeInvalid();
    expect(screen.getByRole("button", { name: "Classify" })).toBeEnabled();
  });

  it("accepts text at exactly the limit without a warning", () => {
    setup("a".repeat(MAX_INPUT_CHARACTERS));
    expect(screen.queryByText(/over the limit/)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Email text")).toBeValid();
  });

  it("clears the text", async () => {
    const { onClear } = setup("some text");
    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(onClear).toHaveBeenCalledOnce();
  });

  it("reports typing", async () => {
    const { onTextChange } = setup("");
    await userEvent.type(screen.getByLabelText("Email text"), "a");
    expect(onTextChange).toHaveBeenCalledWith("a");
  });
});
