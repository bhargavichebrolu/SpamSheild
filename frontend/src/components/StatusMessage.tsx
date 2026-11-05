import type { ReactNode } from "react";

import { ApiError } from "../services/api";

type Tone = "loading" | "error" | "caution" | "info";

const TONES: Record<Tone, { label: string | null; border: string; icon: string | null }> = {
  loading: { label: null, border: "border-l-axis", icon: null },
  error: { label: "Error", border: "border-l-critical", icon: "!" },
  caution: { label: "Caution", border: "border-l-warning", icon: "!" },
  info: { label: null, border: "border-l-axis", icon: "i" },
};

interface StatusMessageProps {
  tone: Tone;
  title?: string;
  children?: ReactNode;
}

/** A message in one consistent style. Colour is never its only signal: it has a label too. */
export function StatusMessage({ tone, title, children }: StatusMessageProps) {
  const { label, border, icon } = TONES[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-xl border border-line border-l-4 ${border} bg-surface p-4 text-sm`}
    >
      <p className="flex items-start gap-2 font-semibold">
        {icon && (
          <span
            aria-hidden="true"
            className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-current text-[0.65rem] leading-none"
          >
            {icon}
          </span>
        )}
        <span>
          {label && <span className="sr-only">{label}: </span>}
          {title}
        </span>
      </p>
      {children && <div className="mt-2 space-y-2 text-ink-secondary">{children}</div>}
    </div>
  );
}

export function LoadingMessage({ children }: { children: ReactNode }) {
  return (
    <StatusMessage tone="loading" title={String(children)} />
  );
}

export function RetryButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="btn-secondary !px-4 !py-1.5 text-sm"
    >
      Try again
    </button>
  );
}

export function StartBackendHelp() {
  return (
    <>
      <p>Start it from the repository root, with your Python environment active:</p>
      <pre className="overflow-x-auto rounded bg-page p-2 text-xs text-ink">
        <code>cd backend{"\n"}python -m uvicorn app.main:app --host 127.0.0.1 --port 8000</code>
      </pre>
    </>
  );
}

interface ApiErrorMessageProps {
  error: unknown;
  onRetry?: () => void;
}

/** Explain a failed request, using the server's own message when it gave one. */
export function ApiErrorMessage({ error, onRetry }: ApiErrorMessageProps) {
  const retry = onRetry && <RetryButton onClick={onRetry} />;

  if (error instanceof ApiError) {
    if (error.kind === "network") {
      return (
        <StatusMessage tone="error" title="The API can't be reached">
          <StartBackendHelp />
          {retry}
        </StatusMessage>
      );
    }
    if (error.kind === "timeout") {
      return (
        <StatusMessage tone="error" title="The API took too long to respond">
          <p>Your text wasn't classified. It may be busy, so please try again.</p>
          {retry}
        </StatusMessage>
      );
    }
    if (error.kind === "invalid_response") {
      return (
        <StatusMessage tone="error" title="The API sent a response that couldn't be read">
          {retry}
        </StatusMessage>
      );
    }
    if (error.status === 422 || error.status === 413) {
      return <StatusMessage tone="error" title={error.message} />;
    }
    return (
      <StatusMessage tone="error" title={error.message}>
        {retry}
      </StatusMessage>
    );
  }

  return (
    <StatusMessage tone="error" title="Something went wrong">
      {retry}
    </StatusMessage>
  );
}
