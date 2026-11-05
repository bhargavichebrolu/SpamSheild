import { useEffect, useRef, useState } from "react";

import { ClassifierForm } from "../components/ClassifierForm";
import { PredictionResult } from "../components/PredictionResult";
import { ApiErrorMessage, LoadingMessage, RetryButton, StartBackendHelp, StatusMessage } from "../components/StatusMessage";
import { useApiResource } from "../hooks/useApiResource";
import { classifyEmail, getHealth } from "../services/api";
import type { ClassifyResponse } from "../types/api";

function BackendStatus() {
  const { data, error, retry } = useApiResource(getHealth);

  if (error) {
    return (
      <StatusMessage tone="error" title="The API can't be reached">
        <StartBackendHelp />
        <RetryButton onClick={retry} />
      </StatusMessage>
    );
  }
  if (data?.status === "unavailable") {
    return (
      <StatusMessage tone="error" title="The model isn't available">
        <p>{data.detail}</p>
        <RetryButton onClick={retry} />
      </StatusMessage>
    );
  }
  return null;
}

export function ClassifierPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [resultText, setResultText] = useState("");
  const [error, setError] = useState<unknown>(null);

  // Only the newest request may update the page, so a late response can't replace a newer one.
  const currentRequest = useRef<AbortController | null>(null);

  useEffect(() => () => currentRequest.current?.abort(), []);

  const handleSubmit = async () => {
    currentRequest.current?.abort();
    const controller = new AbortController();
    currentRequest.current = controller;
    const submitted = text;

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await classifyEmail(submitted, controller.signal);
      if (!controller.signal.aborted) {
        setResult(response);
        setResultText(submitted);
      }
    } catch (requestError) {
      if (!controller.signal.aborted) {
        setError(requestError);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  };

  const handleClear = () => {
    currentRequest.current?.abort();
    setText("");
    setResult(null);
    setResultText("");
    setError(null);
    setLoading(false);
  };

  return (
    <div id="classify" className="scroll-mt-24 space-y-6">
      <BackendStatus />

      <div className="card accent-violet p-4 sm:p-6">
        <h2 className="text-2xl font-bold">Classify an email</h2>
        <p className="mt-1 mb-4 text-ink-secondary">
          Paste an email's text to see whether the model classifies it as spam or ham, and which words influenced that.
        </p>
        <ClassifierForm
          text={text}
          loading={loading}
          onTextChange={setText}
          onSubmit={handleSubmit}
          onClear={handleClear}
        />
      </div>

      {loading && <LoadingMessage>Classifying your text…</LoadingMessage>}
      {error != null && <ApiErrorMessage error={error} onRetry={handleSubmit} />}
      {result && <PredictionResult result={result} outOfDate={text !== resultText} />}
    </div>
  );
}
