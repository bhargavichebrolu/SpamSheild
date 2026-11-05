import type { FormEvent } from "react";

import { count } from "../utils/format";

/** The API's limit, repeated here only to guide the user. The server still enforces it. */
export const MAX_INPUT_CHARACTERS = 20_000;

interface ClassifierFormProps {
  text: string;
  loading: boolean;
  onTextChange: (text: string) => void;
  onSubmit: () => void;
  onClear: () => void;
}

export function ClassifierForm({ text, loading, onTextChange, onSubmit, onClear }: ClassifierFormProps) {
  const overLimit = text.length > MAX_INPUT_CHARACTERS;
  const empty = text.trim().length === 0;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!empty && !loading) {
      onSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label htmlFor="email-text" className="mb-1 block font-semibold">
          Email text
        </label>
        <textarea
          id="email-text"
          value={text}
          onChange={(event) => onTextChange(event.target.value)}
          rows={9}
          aria-describedby="email-text-help"
          aria-invalid={overLimit}
          placeholder="Paste the text of an email here"
          className="block w-full rounded-xl border-2 border-axis bg-surface p-3 text-base text-ink placeholder:text-ink-secondary focus:border-link"
        />
        <div id="email-text-help" className="mt-1 flex flex-wrap justify-between gap-x-4 gap-y-1 text-sm text-ink-secondary">
          <span>Your text isn't stored or logged.</span>
          <span className={overLimit ? "font-semibold text-ink" : undefined}>
            {count(text.length)} of {count(MAX_INPUT_CHARACTERS)} characters
            {overLimit ? `: ${count(text.length - MAX_INPUT_CHARACTERS)} over the limit` : ""}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={empty || loading} className="btn-primary">
          {loading ? "Classifying…" : "Classify"}
        </button>
        <button type="button" onClick={onClear} disabled={text.length === 0 && !loading} className="btn-secondary">
          Clear
        </button>
      </div>
    </form>
  );
}
