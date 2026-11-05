import type { ClassifyResponse } from "../types/api";
import { count, signed } from "../utils/format";
import { StatusMessage } from "./StatusMessage";
import { TermContributions } from "./TermContributions";

/**
 * Below this many recognised words, the page shows a caution. This is a judgement about what
 * to display, not a measured reliability boundary, and it doesn't change the prediction.
 */
export const SHORT_MESSAGE_RECOGNISED_WORDS = 5;

interface PredictionResultProps {
  result: ClassifyResponse;
  outOfDate: boolean;
}

export function PredictionResult({ result, outOfDate }: PredictionResultProps) {
  const isSpam = result.label === "spam";
  const fewWords = result.terms_recognised < SHORT_MESSAGE_RECOGNISED_WORDS;

  return (
    <section aria-labelledby="result-heading" className="space-y-5 rounded border border-line bg-surface p-4 sm:p-6">
      <h2 id="result-heading" className="sr-only">
        Result
      </h2>

      {outOfDate && (
        <StatusMessage tone="info" title="The text has changed since this result">
          <p>Classify again to get a result for the current text.</p>
        </StatusMessage>
      )}

      <div className={outOfDate ? "space-y-5 opacity-60" : "space-y-5"}>
        <div className="flex flex-wrap items-baseline gap-x-8 gap-y-3">
          <p className="flex items-center gap-3">
            <span aria-hidden="true" className={`h-3 w-3 rounded-full ${isSpam ? "bg-spam" : "bg-ham"}`} />
            <span className="text-3xl font-semibold" data-testid="prediction-label">
              {isSpam ? "Spam" : "Ham"}
            </span>
            <span className="text-sm text-ink-secondary">{isSpam ? "unwanted or deceptive" : "legitimate"}</span>
          </p>
          <p>
            <span className="text-sm text-ink-secondary">Decision score </span>
            <span className="text-xl font-semibold" data-testid="decision-score">
              {signed(result.score)}
            </span>
          </p>
        </div>

        <p className="text-sm text-ink-secondary">
          The decision score shows which side of the model's decision boundary this text falls on, and how far from it,
          in the model's own units. Positive leans spam, and negative leans ham. It isn't a probability or a measure of
          how likely the label is to be correct, so this model shows no percentage. This result can be wrong, especially
          for email unlike its training data.
        </p>

        {fewWords && (
          <StatusMessage
            tone="caution"
            title={`Only ${count(result.terms_recognised)} recognised ${result.terms_recognised === 1 ? "word" : "words"}`}
          >
            <p>
              The model had little to go on, so treat this result with extra caution. Its starting score is{" "}
              {signed(result.explanation.intercept)}, which counts towards the final score.
            </p>
            <p>
              Showing this below {SHORT_MESSAGE_RECOGNISED_WORDS} recognised words is a display warning, not a measured
              reliability boundary. It doesn't change the model's prediction.
            </p>
          </StatusMessage>
        )}

        <dl className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div className="flex gap-2">
            <dt className="text-ink-secondary">Recognised words</dt>
            <dd className="font-medium" data-testid="terms-recognised">
              {count(result.terms_recognised)}
            </dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-ink-secondary">Characters</dt>
            <dd className="font-medium">{count(result.text_length)}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-ink-secondary">Model version</dt>
            <dd className="font-medium">{result.model_version}</dd>
          </div>
        </dl>

        <TermContributions explanation={result.explanation} score={result.score} />
      </div>
    </section>
  );
}
