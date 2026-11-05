import { Link } from "react-router-dom";

import { RatioBars, ShareBar, StackedBars } from "../components/Charts";
import { useApiResource } from "../hooks/useApiResource";
import { getDatasetResults, getModelsResults } from "../services/api";
import type { DatasetResults, ModelsResults } from "../types/api";
import { bandName, count, metric, share } from "../utils/format";
import { crossStyleBars, errorsByBand, errorShareOfFirstBand, lowestCrossStyleF1, noCloseMatchF1 } from "../utils/results";
import { ClassifierPage } from "./ClassifierPage";

const STEPS = [
  { title: "Paste an email", text: "Your text goes to the API running on this computer, and isn't stored or logged.", accent: "accent-violet" },
  { title: "Prepare the text", text: "It's prepared in the same way as the training data, including lowercasing and unifying numbers.", accent: "accent-pink" },
  { title: "Turn words into numbers", text: "TF-IDF gives each known word a weight, based on this message and the training data.", accent: "accent-amber" },
  { title: "Score and explain", text: "A Linear SVM adds up word weights into a decision score, and shows which words moved it most.", accent: "accent-teal" },
];

interface HeroTileProps {
  label: string;
  value: string;
}

function HeroTile({ label, value }: HeroTileProps) {
  return (
    <div className="hero-tile">
      <dt className="text-sm">{label}</dt>
      <dd className="mt-1 text-2xl font-bold break-words sm:text-3xl">{value}</dd>
    </div>
  );
}

function Hero({ results, dataset }: { results: ModelsResults | null; dataset: DatasetResults | null }) {
  const noCloseMatch = results && noCloseMatchF1(results);
  const crossStyle = results && lowestCrossStyleF1(results);
  return (
    <section aria-labelledby="hero-heading" className="brand-gradient rounded-3xl p-6 shadow-xl sm:p-10">
      <p className="text-sm font-semibold tracking-wide uppercase">Explainable spam detection</p>
      <h1 id="hero-heading" className="mt-2 text-3xl font-extrabold sm:text-5xl">
        Is that email spam? See what the model sees.
      </h1>
      <p className="mt-3 max-w-2xl sm:text-lg">
        Paste an email to get a spam or ham label, a decision score, and the exact words that pushed it each way.
      </p>
      <div className="mt-5 flex flex-wrap gap-3">
        <a href="#classify" className="rounded-full bg-white px-5 py-2.5 font-bold text-violet-900 shadow hover:bg-violet-100">
          Try the classifier
        </a>
        <Link to="/models" className="rounded-full border border-white px-5 py-2.5 font-semibold text-white hover:bg-white/20">
          See the results
        </Link>
      </div>

      {results && (
        <>
          <dl className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <HeroTile label="F1 on held-out test data" value={metric(results.test_evaluation.overall_metrics.f1_spam)} />
            {noCloseMatch !== null && <HeroTile label="F1 with no close training match" value={metric(noCloseMatch)} />}
            {crossStyle !== null && <HeroTile label="Lowest F1 across text styles" value={metric(crossStyle)} />}
            {dataset && <HeroTile label="Emails in the dataset" value={count(dataset.structure.rows)} />}
          </dl>
          <p className="mt-4 text-sm">
            Measured on this one dataset only, so these scores don't show how it would do on a real inbox. The lowest
            score is the most useful warning about unfamiliar email.
          </p>
        </>
      )}
    </section>
  );
}

function HowItWorks() {
  return (
    <section aria-labelledby="how-heading">
      <h2 id="how-heading" className="text-2xl font-bold">
        How it works
      </h2>
      <ol className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map(({ title, text, accent }, position) => (
          <li key={title} className={`card p-4 ${accent}`}>
            <span aria-hidden="true" className="brand-gradient flex h-8 w-8 items-center justify-center rounded-full font-bold">
              {position + 1}
            </span>
            <h3 className="mt-2 font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-ink-secondary">{text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

const ERROR_SERIES = [
  { key: "flagged", name: "Ham flagged", color: "bg-flagged" },
  { key: "missed", name: "Spam missed", color: "bg-missed" },
];

const STYLE_SERIES = [
  { key: "same", name: "Same text style", color: "bg-split-validation" },
  { key: "other", name: "Different text style", color: "bg-flagged" },
];

function Overview({ results, dataset }: { results: ModelsResults; dataset: DatasetResults | null }) {
  const { first, total } = errorShareOfFirstBand(results);
  return (
    <section aria-labelledby="results-heading">
      <h2 id="results-heading" className="text-2xl font-bold">
        What the results show
      </h2>
      <div className="mt-3 grid gap-4 lg:grid-cols-2">
        <div className="card accent-pink space-y-3 p-4 sm:p-6">
          <h3 className="font-semibold">Most errors have no close training match</h3>
          <p className="text-sm text-ink-secondary">
            {count(first)} of {count(total)} test errors are in the first group: messages with no close match in training.
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
        </div>

        <div className="card accent-amber space-y-3 p-4 sm:p-6">
          <h3 className="font-semibold">Scores fall on an unfamiliar text style</h3>
          <p className="text-sm text-ink-secondary">
            A stand-in for email from a new source, on validation data. This isn't proof of how it would do on real email.
          </p>
          <RatioBars
            label="F1 for Spam, trained on one text style and scored on each"
            series={STYLE_SERIES}
            rows={crossStyleBars(results)}
            scaleMax={1}
            formatValue={(value) => (value === 0 || value === 1 ? String(value) : metric(value))}
          />
        </div>

        {dataset && (
          <div className="card accent-teal space-y-3 p-4 sm:p-6 lg:col-span-2">
            <h3 className="font-semibold">The dataset behind it</h3>
            <p className="text-sm text-ink-secondary">
              Its balance doesn't reflect real inboxes, and its licence is {dataset.source.licence.toLowerCase()}.
            </p>
            <ShareBar
              label="Rows by label"
              parts={[
                { name: "Ham", value: dataset.labels.Ham.rows, color: "bg-ham" },
                { name: "Spam", value: dataset.labels.Spam.rows, color: "bg-spam" },
              ]}
              formatPart={({ value }, whole) => `${count(value)} rows (${share(value / whole)})`}
            />
          </div>
        )}
      </div>
    </section>
  );
}

export function HomePage() {
  const models = useApiResource(getModelsResults);
  const dataset = useApiResource(getDatasetResults);

  return (
    <div className="space-y-8">
      <Hero results={models.data} dataset={dataset.data} />
      <ClassifierPage />
      <HowItWorks />
      {models.data && <Overview results={models.data} dataset={dataset.data} />}
    </div>
  );
}
