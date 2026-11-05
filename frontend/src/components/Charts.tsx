/**
 * Charts built from plain HTML, so that they resize with the page. They only draw the values
 * they're given. Every value is also written as text, so nothing depends on colour or hover,
 * and no text sits on a coloured fill.
 */

import { count, signed } from "../utils/format";

export interface ChartSeries {
  key: string;
  name: string;
  /** A Tailwind background class, such as bg-spam. */
  color: string;
}

export function ChartLegend({ series }: { series: ChartSeries[] }) {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-secondary">
      {series.map(({ key, name, color }) => (
        <li key={key} className="flex items-center gap-2">
          <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-full ${color}`} />
          {name}
        </li>
      ))}
    </ul>
  );
}

const barWidth = (value: number, largest: number): string =>
  `${largest > 0 ? Math.max((value / largest) * 100, value > 0 ? 1 : 0) : 0}%`;

export interface StackedRow {
  label: string;
  detail?: string;
  highlight?: boolean;
  values: Record<string, number>;
}

interface StackedBarsProps {
  label: string;
  series: ChartSeries[];
  rows: StackedRow[];
}

/** Compare totals across rows, with each row split into parts. All rows share one scale. */
export function StackedBars({ label, series, rows }: StackedBarsProps) {
  const total = (row: StackedRow) => series.reduce((sum, { key }) => sum + (row.values[key] ?? 0), 0);
  const largest = Math.max(...rows.map(total), 0);

  return (
    <figure className="space-y-3">
      <ChartLegend series={series} />
      <ul aria-label={label} className="space-y-3">
        {rows.map((row) => {
          const rowTotal = total(row);
          return (
            <li key={row.label} className={row.highlight ? "rounded-lg bg-highlight p-2" : undefined}>
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
                <span className="font-medium">
                  {row.label}
                  {row.detail && <span className="font-normal text-ink-secondary"> {row.detail}</span>}
                </span>
                <span className="text-ink-secondary tabular-nums">
                  {series.map(({ key, name }) => `${count(row.values[key] ?? 0)} ${name.toLowerCase()}`).join(", ")}
                </span>
              </div>
              <div aria-hidden="true" className="mt-1 h-3 border-l border-axis">
                <div className="flex h-3 gap-0.5" style={{ width: barWidth(rowTotal, largest) }}>
                  {series.map(({ key, name, color }) => {
                    const value = row.values[key] ?? 0;
                    return value > 0 ? (
                      <div
                        key={key}
                        title={`${name}: ${count(value)}`}
                        className={`h-3 last:rounded-r ${color}`}
                        style={{ flexGrow: value, flexBasis: 0 }}
                      />
                    ) : null;
                  })}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}

export interface RatioRow {
  label: string;
  value: number;
  /** Which series this row belongs to. */
  seriesKey: string;
}

interface RatioBarsProps {
  label: string;
  series: ChartSeries[];
  rows: RatioRow[];
  /** The full bar width represents this value, which is written on the axis. */
  scaleMax: number;
  formatValue: (value: number) => string;
}

/** Compare values from zero on one scale, so that differences are drawn at their true size. */
export function RatioBars({ label, series, rows, scaleMax, formatValue }: RatioBarsProps) {
  return (
    <figure className="space-y-3">
      <ChartLegend series={series} />
      <ul aria-label={label} className="space-y-3">
        {rows.map((row) => {
          const color = series.find(({ key }) => key === row.seriesKey)?.color ?? "bg-axis";
          return (
            <li key={row.label}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 font-medium break-words">{row.label}</span>
                <span className="shrink-0 font-semibold tabular-nums">{formatValue(row.value)}</span>
              </div>
              <div aria-hidden="true" className="mt-1 h-3 border-l border-axis">
                <div
                  title={`${row.label}: ${formatValue(row.value)}`}
                  className={`h-3 rounded-r ${color}`}
                  style={{ width: barWidth(row.value, scaleMax) }}
                />
              </div>
            </li>
          );
        })}
      </ul>
      <div aria-hidden="true" className="flex justify-between border-t border-axis pt-1 text-xs text-ink-secondary tabular-nums">
        <span>{formatValue(0)}</span>
        <span>{formatValue(scaleMax)}</span>
      </div>
    </figure>
  );
}

export interface GroupedRow {
  label: string;
  values: Record<string, number>;
}

interface GroupedBarsProps {
  label: string;
  series: ChartSeries[];
  rows: GroupedRow[];
  formatValue: (value: number) => string;
}

/** Compare two or more series side by side, for each row. All bars share one scale. */
export function GroupedBars({ label, series, rows, formatValue }: GroupedBarsProps) {
  const largest = Math.max(...rows.flatMap((row) => series.map(({ key }) => row.values[key] ?? 0)), 0);
  return (
    <figure className="space-y-3">
      <ChartLegend series={series} />
      <ul aria-label={label} className="grid gap-x-8 gap-y-4 sm:grid-cols-2">
        {rows.map((row) => (
          <li key={row.label} className="min-w-0">
            <p className="text-sm font-medium break-words">{row.label}</p>
            <div className="mt-1 space-y-1 border-l border-axis">
              {series.map(({ key, name, color }) => {
                const value = row.values[key] ?? 0;
                return (
                  <div key={key} className="flex items-center gap-2 text-xs text-ink-secondary">
                    <div className="min-w-0 flex-1">
                      <div
                        aria-hidden="true"
                        title={`${name}: ${formatValue(value)}`}
                        className={`h-2.5 rounded-r ${color}`}
                        style={{ width: barWidth(value, largest) }}
                      />
                    </div>
                    <span className="w-24 shrink-0 text-right tabular-nums">
                      {name} {formatValue(value)}
                    </span>
                  </div>
                );
              })}
            </div>
          </li>
        ))}
      </ul>
    </figure>
  );
}

export interface SharePart {
  name: string;
  value: number;
  color: string;
}

interface ShareBarProps {
  label: string;
  parts: SharePart[];
  formatPart: (part: SharePart, total: number) => string;
}

/** One whole, split into parts. The legend carries the numbers, so no text sits on colour. */
export function ShareBar({ label, parts, formatPart }: ShareBarProps) {
  const total = parts.reduce((sum, { value }) => sum + value, 0);
  return (
    <figure className="space-y-2">
      <div
        role="img"
        aria-label={`${label}: ${parts.map((part) => `${part.name}, ${formatPart(part, total)}`).join("; ")}`}
        className="flex h-5 w-full gap-0.5"
      >
        {parts.map(({ name, value, color }) => (
          <div
            key={name}
            title={name}
            className={`h-full first:rounded-l-lg last:rounded-r-lg ${color}`}
            style={{ flexGrow: value, flexBasis: 0 }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {parts.map((part) => (
          <li key={part.name} className="flex items-center gap-2">
            <span aria-hidden="true" className={`h-2.5 w-2.5 rounded-full ${part.color}`} />
            {part.name}: {formatPart(part, total)}
          </li>
        ))}
      </ul>
    </figure>
  );
}

/** The smallest scale that keeps the marker on the track, and doesn't exaggerate small scores. */
export function gaugeLimit(score: number): number {
  return Math.max(2, Math.ceil(Math.abs(score)));
}

/**
 * Show where a decision score falls, between leaning ham and leaning spam. It's a position on
 * the model's own scale, not a percentage or a chance of being correct.
 */
export function DecisionGauge({ score }: { score: number }) {
  const limit = gaugeLimit(score);
  const position = 50 + (score / limit) * 50;
  return (
    <figure
      role="img"
      aria-label={`Decision score ${signed(score)}, on a scale from ${signed(-limit, 0)} to ${signed(limit, 0)}. Negative leans ham, and positive leans spam.`}
      className="max-w-xl"
    >
      <div className="relative pt-2 pb-1">
        <div className="gauge-track h-3 rounded-full" />
        <div aria-hidden="true" className="absolute top-0 bottom-0 left-1/2 w-px bg-ink" />
        <div
          aria-hidden="true"
          data-testid="gauge-marker"
          className="absolute top-0.5 h-6 w-6 -translate-x-1/2 rounded-full border-4 border-surface bg-ink shadow-md"
          style={{ left: `${position}%` }}
        />
      </div>
      <figcaption aria-hidden="true" className="mt-1 grid grid-cols-3 text-xs text-ink-secondary">
        <span>{signed(-limit, 0)} leans ham</span>
        <span className="text-center">0 boundary</span>
        <span className="text-right">leans spam {signed(limit, 0)}</span>
      </figcaption>
    </figure>
  );
}
