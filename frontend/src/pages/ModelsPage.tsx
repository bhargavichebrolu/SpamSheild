import { RatioBars, StackedBars } from "../components/Charts";
import { ConfusionMatrix, PageBanner, PageSection, StatGrid, StatTile, TableScroll } from "../components/ResultsParts";
import { ApiErrorMessage, LoadingMessage, StatusMessage } from "../components/StatusMessage";
import { useApiResource } from "../hooks/useApiResource";
import { getModelsResults } from "../services/api";
import type { CrossStyleRun, ModelsResults } from "../types/api";
import { bandName, count, featureName, metric, modelName, removalName, settingText, share, styleName } from "../utils/format";
import { bestRunPerCombination, crossStyleBars, errorsByBand } from "../utils/results";

const ERROR_SERIES = [
  { key: "flagged", name: "Ham flagged", color: "bg-flagged" },
  { key: "missed", name: "Spam missed", color: "bg-missed" },
];

const STYLE_SERIES = [
  { key: "same", name: "Same text style", color: "bg-split-validation" },
  { key: "other", name: "Different text style", color: "bg-flagged" },
];

function crossStyleName(run: CrossStyleRun): string {
  const parts = [styleName(run.training_style)];
  if (run.name.endsWith("matched_size")) {
    parts.push("matched size");
  }
  if (run.words_removed > 0) {
    parts.push(`${count(run.words_removed)} words removed`);
  }
  return parts.join(", ");
}

function SelectedModel({ results }: { results: ModelsResults }) {
  const { final_model: finalModel, selection, comparison_runs: runs } = results;
  const selected = selection.selected;
  const best = runs.reduce((top, run) => (run.metrics.f1_spam > top.metrics.f1_spam ? run : top));
  const selectedIsBest = best.metrics.f1_spam === selected.metrics.f1_spam;

  return (
    <PageSection title="Selected model" accent="teal">
      <StatGrid>
        <StatTile label="Model" value={modelName(finalModel.model)} accent="teal" />
        <StatTile label="Features" value={featureName(finalModel.features)} accent="teal" />
        <StatTile label="Setting" value={settingText(finalModel.setting)} accent="teal" />
        <StatTile label="Words excluded" value={count(finalModel.removed_word_count)} accent="teal" />
      </StatGrid>
      <p className="text-sm text-ink-secondary">
        Trained on {count(finalModel.training_rows)} rows, with a vocabulary of {count(finalModel.vocabulary_size)} words.
        Version {finalModel.model_version}.
      </p>
      <h3 className="pt-2 font-semibold">The selection rule, fixed before any comparison was run</h3>
      <ol className="list-decimal space-y-1 pl-5 text-sm">
        {selection.rule.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <p className="text-sm text-ink-secondary">
        F1 scores within {selection.rule.f1_tie_margin} of the best count as tied. The rule used {selection.split_used}{" "}
        results only.
        {!selectedIsBest &&
          ` The selected model isn't the highest F1: ${modelName(best.model)} with ${featureName(best.features).toLowerCase()} scored ${metric(best.metrics.f1_spam)}, against ${metric(selected.metrics.f1_spam)}. That gap is inside the tie margin, and the selected model flags ${count(best.metrics.ham_flagged_as_spam - selected.metrics.ham_flagged_as_spam)} fewer legitimate messages.`}
      </p>
    </PageSection>
  );
}

function TestResults({ results }: { results: ModelsResults }) {
  const test = results.test_evaluation;
  const metrics = test.overall_metrics;
  return (
    <PageSection title="Final test results" accent="violet">
      <p className="text-sm text-ink-secondary">
        The frozen model was evaluated once, on {count(test.rows)} held-out messages. These scores only describe this
        dataset's sources.
      </p>
      {!test.report_matches_saved_model && (
        <StatusMessage tone="caution" title="These results don't describe the saved model file">
          <p>The saved file's hash doesn't match the one recorded when it was evaluated.</p>
        </StatusMessage>
      )}
      <StatGrid>
        <StatTile label="F1 (Spam)" value={metric(metrics.f1_spam)} accent="violet" />
        <StatTile label="Precision (Spam)" value={metric(metrics.precision_spam)} accent="pink" />
        <StatTile label="Recall (Spam)" value={metric(metrics.recall_spam)} accent="amber" />
        <StatTile label="ROC-AUC" value={metric(test.roc_auc)} accent="teal" />
      </StatGrid>
      <ConfusionMatrix metrics={metrics} caption="Test split: predictions against actual labels" />
      <h3 className="pt-2 font-semibold">By similarity to training data</h3>
      <p className="text-sm text-ink-secondary">
        Each message is grouped by its closest training message. The first row is a fairer guide to messages without a
        close match, but they still come from this dataset's sources.
      </p>
      <StackedBars
        label="Test errors by similarity to training data"
        series={ERROR_SERIES}
        rows={errorsByBand(results).map(({ band, rows, flagged, missed }) => ({
          label: bandName(band),
          detail: `(${count(rows)} messages)`,
          values: { flagged, missed },
        }))}
      />
      <TableScroll label="Test results by similarity to training data">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Closest training message</th>
              <th scope="col">Messages</th>
              <th scope="col">Share of messages</th>
              <th scope="col">F1 (Spam)</th>
              <th scope="col">Ham flagged</th>
              <th scope="col">Spam missed</th>
            </tr>
          </thead>
          <tbody>
            {test.similarity_bands.map((band) => (
              <tr key={band.band}>
                <th scope="row">{bandName(band.band)}</th>
                <td>{count(band.rows)}</td>
                <td>{share(band.share_of_rows)}</td>
                <td>{band.metrics ? metric(band.metrics.f1_spam) : "No messages"}</td>
                <td>{band.metrics ? count(band.metrics.ham_flagged_as_spam) : "No messages"}</td>
                <td>{band.metrics ? count(band.metrics.spam_missed) : "No messages"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

function ComparisonTable({ results }: { results: ModelsResults }) {
  const { comparison_runs: runs, selection, feature_sets: featureSets } = results;
  const selected = selection.selected;
  const isSelected = (run: (typeof runs)[number]) =>
    run.model === selected.model &&
    run.features === selected.features &&
    settingText(run.setting) === settingText(selected.setting);

  return (
    <PageSection title="Model comparison" accent="pink">
      <p className="text-sm text-ink-secondary">
        All {count(runs.length)} runs used the same split, and within each feature set every model used the same
        features. These are {selection.split_used} results, from {count(featureSets[0]?.train_rows ?? 0)} training rows
        and {count(featureSets[0]?.validation_rows ?? 0)} {selection.split_used} rows.
      </p>
      <h3 className="pt-2 font-semibold">Errors for each model and feature set</h3>
      <p className="text-sm text-ink-secondary">
        Each row is the selected run, or that combination's highest-F1 run. Shorter is better, with fewest errors first.
      </p>
      <StackedBars
        label="Validation errors for each model and feature set"
        series={ERROR_SERIES}
        rows={bestRunPerCombination(results).map(({ label, detail, flagged, missed, selected: isChosen }) => ({
          label: isChosen ? `${label} (selected)` : label,
          detail: `(${detail})`,
          highlight: isChosen,
          values: { flagged, missed },
        }))}
      />
      <h3 className="pt-2 font-semibold">All runs</h3>
      <TableScroll label="All model comparison runs">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col">Features</th>
              <th scope="col">Setting</th>
              <th scope="col">F1 (Spam)</th>
              <th scope="col">Precision</th>
              <th scope="col">Recall</th>
              <th scope="col">Ham flagged</th>
              <th scope="col">Spam missed</th>
              <th scope="col">ROC-AUC</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={`${run.features}-${run.model}-${settingText(run.setting)}`} data-highlight={isSelected(run)}>
                <th scope="row">
                  {modelName(run.model)}
                  {isSelected(run) && <span className="ml-2 font-semibold">(selected)</span>}
                </th>
                <td>{featureName(run.features)}</td>
                <td>{settingText(run.setting)}</td>
                <td>{metric(run.metrics.f1_spam)}</td>
                <td>{metric(run.metrics.precision_spam)}</td>
                <td>{metric(run.metrics.recall_spam)}</td>
                <td>{count(run.metrics.ham_flagged_as_spam)}</td>
                <td>{count(run.metrics.spam_missed)}</td>
                <td>{metric(run.roc_auc)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <ConfusionMatrix metrics={selected.metrics} caption={`Selected model on ${selection.split_used} data, before words were excluded`} />
    </PageSection>
  );
}

function SourceLeakageResults({ results }: { results: ModelsResults }) {
  const leakage = results.source_leakage;
  const decision = leakage.removal_decision;
  return (
    <PageSection title="Source-leakage experiment" accent="amber">
      <StatusMessage tone="caution" title="What this does and doesn't show">
        <p>{leakage.interpretation_note}</p>
      </StatusMessage>

      <h3 className="pt-2 font-semibold">Training on one text style, and scoring on each style</h3>
      <p className="text-sm text-ink-secondary">
        The dataset's digit and placeholder styles are used as a stand-in for separate sources. Lower scores on a
        different style suggest the model may struggle with unfamiliar email.
      </p>
      <RatioBars
        label="F1 for Spam, trained on one text style and scored on each"
        series={STYLE_SERIES}
        rows={crossStyleBars(results)}
        scaleMax={1}
        formatValue={(value) => (value === 0 || value === 1 ? String(value) : metric(value))}
      />
      <TableScroll label="Cross-style results">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Trained on</th>
              <th scope="col">Training rows</th>
              <th scope="col">Scored on</th>
              <th scope="col">Messages</th>
              <th scope="col">F1 (Spam)</th>
              <th scope="col">Ham flagged</th>
              <th scope="col">Spam missed</th>
            </tr>
          </thead>
          <tbody>
            {leakage.cross_style.flatMap((run) =>
              run.scores.map((score) => (
                <tr key={`${run.name}-${score.scored_on}`}>
                  <th scope="row">{crossStyleName(run)}</th>
                  <td>{count(run.training_rows)}</td>
                  <td>{styleName(score.scored_on)}</td>
                  <td>{count(score.rows)}</td>
                  <td>{metric(score.metrics.f1_spam)}</td>
                  <td>{count(score.metrics.ham_flagged_as_spam)}</td>
                  <td>{count(score.metrics.spam_missed)}</td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </TableScroll>

      <h3 className="pt-2 font-semibold">Removing likely source-marker words</h3>
      <p className="text-sm text-ink-secondary">
        Word lists were built from training data only, and are estimates. Data used: {leakage.split_used}.
      </p>
      <TableScroll label="Marker removal results">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Words removed</th>
              <th scope="col">Count</th>
              <th scope="col">F1 (Spam)</th>
              <th scope="col">Ham flagged</th>
              <th scope="col">Spam missed</th>
            </tr>
          </thead>
          <tbody>
            {leakage.marker_removal.map((run) => (
              <tr key={run.name} data-highlight={run.name === decision.candidate && decision.adopt}>
                <th scope="row">
                  {removalName(run.name)}
                  {run.name === decision.candidate && decision.adopt && <span className="ml-2 font-semibold">(used)</span>}
                </th>
                <td>{count(run.words_removed)}</td>
                <td>{metric(run.metrics.f1_spam)}</td>
                <td>{count(run.metrics.ham_flagged_as_spam)}</td>
                <td>{count(run.metrics.spam_missed)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

export function ModelsPage() {
  const { data, error, loading, retry } = useApiResource(getModelsResults);

  return (
    <div className="space-y-6">
      <PageBanner title="Model comparison">
        Every number here comes from the project's saved experiment reports, served by the API.
      </PageBanner>

      {loading && <LoadingMessage>Loading saved results…</LoadingMessage>}
      {error != null && <ApiErrorMessage error={error} onRetry={retry} />}
      {data && (
        <>
          <TestResults results={data} />
          <SelectedModel results={data} />
          <ComparisonTable results={data} />
          <SourceLeakageResults results={data} />
          <PageSection title="Limitations" accent="blue">
            <ul className="list-disc space-y-1 pl-5 text-sm">
              {data.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </PageSection>
        </>
      )}
    </div>
  );
}
