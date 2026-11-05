import { useCallback, useEffect, useState } from "react";

export interface ApiResource<T> {
  data: T | null;
  error: unknown;
  loading: boolean;
  retry: () => void;
}

/** Load something from the API when a page opens, with a way to try again. */
export function useApiResource<T>(load: (signal: AbortSignal) => Promise<T>): ApiResource<T> {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{ data: T | null; error: unknown; loading: boolean }>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState({ data: null, error: null, loading: true });
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) {
          setState({ data, error: null, loading: false });
        }
      },
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setState({ data: null, error, loading: false });
        }
      },
    );
    return () => controller.abort();
  }, [load, attempt]);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  return { ...state, retry };
}
