import type { ReactNode } from "react";

import { GroupedBars, ShareBar, StackedBars } from "../components/Charts";
import { LabelBalanceBar, PageBanner, PageSection, StatGrid, StatTile, TableScroll } from "../components/ResultsParts";
import { ApiErrorMessage, LoadingMessage, StatusMessage } from "../components/StatusMessage";
import { useApiResource } from "../hooks/useApiResource";
import { getDatasetResults } from "../services/api";
import type { DatasetResults } from "../types/api";
import { count, fileSize, flagName, share, styleName } from "../utils/format";
import { numberStyleRows, wordShareRows } from "../utils/results";

const LABEL_SERIES = [
  { key: "ham", name: "Ham", color: "bg-ham" },
  { key: "spam", name: "Spam", color: "bg-spam" },
];

const SPLIT_COLORS: Record<string, string> = {
  train: "bg-split-train",
  validation: "bg-split-validation",
  test: "bg-split-test",
};

function Overview({ data }: { data: DatasetResults }) {
  const missing = Object.values(data.missing_values).reduce((total, value) => total + value, 0);
  const empty = Object.values(data.blank_text.empty_rows).reduce((total, value) => total + value, 0);
  return (
    <PageSection title="Overview" accent="violet">
      <StatGrid>
        <StatTile label="Rows" value={count(data.structure.rows)} accent="violet" />
        <StatTile label="Columns" value={data.structure.columns.join(", ")} accent="pink" />
        <StatTile label="Missing values" value={count(missing)} accent="amber" />
        <StatTile label="Empty text rows" value={count(empty)} accent="teal" />
      </StatGrid>
      <h3 className="pt-2 font-semibold">Label balance</h3>
      <LabelBalanceBar ham={data.labels.Ham} spam={data.labels.Spam} />
      <p className="text-sm text-ink-secondary">
        This balance describes the dataset, not real inboxes, where the share of spam may be very different.
      </p>
    </PageSection>
  );
}

function SourceRow({ term, children }: { term: string; children: ReactNode }) {
  return (
    <div className="border-b border-line py-2 sm:grid sm:grid-cols-[10rem_minmax(0,1fr)] sm:gap-4">
      <dt className="text-sm font-medium">{term}</dt>
      <dd className="min-w-0 text-sm break-words">{children}</dd>
    </div>
  );
}

function Source({ data }: { data: DatasetResults }) {
  const { source, file } = data;
  return (
    <PageSection title="Source" accent="blue">
      <dl>
        <SourceRow term="Reported source">
          <a className="break-all text-link underline" href={source.reported_source_url} rel="noreferrer" target="_blank">
            {source.reported_source_url}
          </a>
        </SourceRow>
        <SourceRow term="Licence">
          <span className="font-semibold" data-testid="licence">
            {source.licence}
          </span>
        </SourceRow>
        <SourceRow term="Original sources">{source.original_sources}</SourceRow>
        <SourceRow term="Label accuracy">{source.label_accuracy}</SourceRow>
        <SourceRow term="File">
          {file.name} ({file.format}, {fileSize(file.size_bytes)})
        </SourceRow>
        <SourceRow term="SHA-256">
          <span className="break-all">{file.sha256}</span>
        </SourceRow>
      </dl>
      <p className="text-sm text-ink-secondary">{source.note}</p>
    </PageSection>
  );
}

function Duplicates({ data }: { data: DatasetResults }) {
  const { duplicates } = data;
  return (
    <PageSection title="Duplicates and conflicting labels" accent="pink">
      <TableScroll label="Duplicate checks">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Check</th>
              <th scope="col">Rows</th>
              <th scope="col">Texts with both labels</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Identical rows (same label and text)</th>
              <td>{count(duplicates.identical_rows)}</td>
              <td>Not applicable</td>
            </tr>
            <tr>
              <th scope="row">Exact duplicate text</th>
              <td>{count(duplicates.exact_duplicate_text_rows)}</td>
              <td>
                {count(duplicates.exact_conflicting_labels.texts)} texts, {count(duplicates.exact_conflicting_labels.rows)} rows
              </td>
            </tr>
            <tr>
              <th scope="row">Same after lowercasing and collapsing spaces</th>
              <td>{count(duplicates.normalised_duplicate_rows)}</td>
              <td>
                {count(duplicates.normalised_conflicting_labels.texts)} texts,{" "}
                {count(duplicates.normalised_conflicting_labels.rows)} rows
              </td>
            </tr>
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

function Lengths({ data }: { data: DatasetResults }) {
  const { lengths } = data;
  const rows = [
    ["Ham", lengths.by_label.Ham],
    ["Spam", lengths.by_label.Spam],
  ] as const;
  return (
    <PageSection title="Message length" accent="amber">
      <GroupedBars
        label="Median message length in characters, for each label"
        series={LABEL_SERIES}
        rows={[
          {
            label: "Median length, in characters",
            values: { ham: lengths.by_label.Ham.median, spam: lengths.by_label.Spam.median },
          },
          {
            label: "95th percentile length, in characters",
            values: { ham: lengths.by_label.Ham.p95, spam: lengths.by_label.Spam.p95 },
          },
        ]}
        formatValue={count}
      />
      <TableScroll label="Message length in characters" description="In characters, excluding empty rows">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Label</th>
              <th scope="col">Rows</th>
              <th scope="col">Median</th>
              <th scope="col">Mean</th>
              <th scope="col">95th percentile</th>
              <th scope="col">99th percentile</th>
              <th scope="col">Longest</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, summary]) => (
              <tr key={label}>
                <th scope="row">{label}</th>
                <td>{count(summary.rows)}</td>
                <td>{count(summary.median)}</td>
                <td>{count(summary.mean)}</td>
                <td>{count(summary.p95)}</td>
                <td>{count(summary.p99)}</td>
                <td>{count(summary.max)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <TableScroll label="Rows over a length">
        <table className="data-table max-w-sm">
          <thead>
            <tr>
              <th scope="col">Length</th>
              <th scope="col">Rows</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(lengths.rows_over_chars)
              .sort(([first], [second]) => Number(first) - Number(second))
              .map(([limit, rows_]) => (
                <tr key={limit}>
                  <th scope="row">Over {count(Number(limit))} characters</th>
                  <td>{count(rows_)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

function TextFormat({ data }: { data: DatasetResults }) {
  const { text_format: textFormat, word_shares: wordShares } = data;
  return (
    <PageSection title="Text format" accent="teal">
      <p className="text-sm text-ink-secondary">
        The text was processed before this project received it. No row mixes digits with the number placeholder, which
        is evidence of separately processed sources, although the sources themselves aren't verified.
      </p>
      <h3 className="pt-2 font-semibold">Rows by number style and label</h3>
      <StackedBars label="Rows by number style and label" series={LABEL_SERIES} rows={numberStyleRows(data)} />
      <h3 className="pt-2 font-semibold">How often possible source words appear</h3>
      <GroupedBars
        label="Share of rows containing each word, for each label"
        series={LABEL_SERIES}
        rows={wordShareRows(data)}
        formatValue={(value) => share(value)}
      />
      <TableScroll label="How rows write numbers" description="How rows write numbers">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Style</th>
              <th scope="col">Ham rows</th>
              <th scope="col">Spam rows</th>
              <th scope="col">With spaced punctuation</th>
            </tr>
          </thead>
          <tbody>
            {textFormat.number_styles.map((style) => (
              <tr key={style.style}>
                <th scope="row">{styleName(style.style)}</th>
                <td>{count(style.ham_rows)}</td>
                <td>{count(style.spam_rows)}</td>
                <td>{share(style.spaced_punctuation_share)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <TableScroll label="Format checks" description={`Format checks, across ${count(textFormat.rows_analysed)} non-blank rows`}>
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Rows containing</th>
              <th scope="col">Ham rows</th>
              <th scope="col">Ham share</th>
              <th scope="col">Spam rows</th>
              <th scope="col">Spam share</th>
            </tr>
          </thead>
          <tbody>
            {textFormat.flags.map((flag) => (
              <tr key={flag.name}>
                <th scope="row">{flagName(flag.name)}</th>
                <td>{count(flag.ham_rows)}</td>
                <td>{share(flag.ham_share, 2)}</td>
                <td>{count(flag.spam_rows)}</td>
                <td>{share(flag.spam_share, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <TableScroll label="Marker words" description="Words that may reveal a message's source or processing">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Word</th>
              <th scope="col">Ham rows containing it</th>
              <th scope="col">Spam rows containing it</th>
            </tr>
          </thead>
          <tbody>
            {wordShares.map(({ word, shares }) => (
              <tr key={word}>
                <th scope="row">{word}</th>
                <td>{share(shares.Ham, 2)}</td>
                <td>{share(shares.Spam, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

function Preparation({ data }: { data: DatasetResults }) {
  const { preparation } = data;
  const { cleaning } = preparation;
  const rules: [string, number, string][] = [
    ["Blank text", cleaning.removed_blank, "Nothing to learn from"],
    ["No word of two or more characters", cleaning.removed_no_word_tokens, "The word features would be empty"],
    [
      `Same text under both labels (${count(cleaning.conflicting_label_texts)} texts)`,
      cleaning.removed_conflicting_labels,
      "The label can't be trusted",
    ],
    ["Repeat of a text (first copy kept)", cleaning.removed_duplicates, "Copies across splits would turn testing into recognition"],
  ];
  return (
    <PageSection title="Cleaning and splits" accent="violet">
      <h3 className="font-semibold">How the rows were split</h3>
      <ShareBar
        label="Rows in each split"
        parts={preparation.splits.map(({ split, total }) => ({
          name: split.charAt(0).toUpperCase() + split.slice(1),
          value: total,
          color: SPLIT_COLORS[split] ?? "bg-axis",
        }))}
        formatPart={({ value }, whole) => `${count(value)} rows (${share(value / whole)})`}
      />
      <TableScroll
        label="Cleaning rules"
        description={`${count(cleaning.rows_in)} rows in, ${count(cleaning.rows_kept)} kept. Rows are compared after preprocessing, and the raw file isn't changed.`}
      >
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Rule</th>
              <th scope="col">Rows removed</th>
              <th scope="col" className="!text-left">
                Why
              </th>
            </tr>
          </thead>
          <tbody>
            {rules.map(([rule, removed, reason]) => (
              <tr key={rule}>
                <th scope="row">{rule}</th>
                <td>{count(removed)}</td>
                <td className="!text-left">{reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <TableScroll
        label="Data splits"
        description={`Stratified by ${preparation.stratified_by}, with random seed ${preparation.random_seed}. ${count(preparation.preprocessed_texts_shared_between_splits)} preprocessed texts appear in more than one split.`}
      >
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Split</th>
              <th scope="col">Rows</th>
              <th scope="col">Ham</th>
              <th scope="col">Spam</th>
              <th scope="col">Spam share</th>
            </tr>
          </thead>
          <tbody>
            {preparation.splits.map((split) => (
              <tr key={split.split}>
                <th scope="row" className="capitalize">
                  {split.split}
                </th>
                <td>{count(split.total)}</td>
                <td>{count(split.ham)}</td>
                <td>{count(split.spam)}</td>
                <td>{share(split.spam_share)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </PageSection>
  );
}

export function DatasetPage() {
  const { data, error, loading, retry } = useApiResource(getDatasetResults);

  return (
    <div className="space-y-6">
      <PageBanner title="Dataset explorer">
        Aggregate statistics computed from the project's dataset, served by the API. No email text is shown.
      </PageBanner>

      {loading && <LoadingMessage>Loading dataset statistics…</LoadingMessage>}
      {error != null && <ApiErrorMessage error={error} onRetry={retry} />}
      {data && (
        <>
          <StatusMessage tone="caution" title={`Licence: ${data.source.licence}`}>
            <p>{data.source.note}</p>
          </StatusMessage>
          <Overview data={data} />
          <Source data={data} />
          <Duplicates data={data} />
          <Lengths data={data} />
          <TextFormat data={data} />
          <Preparation data={data} />
        </>
      )}
    </div>
  );
}
