/** Small pieces shared by the Models and Dataset pages. */

import { useEffect, useRef, useState, type ReactNode } from "react";

import type { Metrics } from "../types/api";
import { count, share } from "../utils/format";

export type Accent = "violet" | "pink" | "teal" | "amber" | "blue";

export function PageBanner({ title, children }: { title: string; children: ReactNode }) {
  return (
    <header className="brand-gradient rounded-3xl p-6 shadow-xl sm:p-8">
      <h1 className="text-3xl font-extrabold sm:text-4xl">{title}</h1>
      <p className="mt-2 max-w-3xl sm:text-lg">{children}</p>
    </header>
  );
}

export function PageSection({ title, accent = "violet", children }: { title: string; accent?: Accent; children: ReactNode }) {
  return (
    <section className={`card accent-${accent} space-y-3 p-4 sm:p-6`}>
      <h2 className="text-xl font-bold">{title}</h2>
      {children}
    </section>
  );
}

export function StatTile({ label, value, accent = "violet" }: { label: string; value: string; accent?: Accent }) {
  return (
    <div className={`stat-tile accent-${accent}`}>
      <dt className="text-sm text-ink-secondary">{label}</dt>
      <dd className="mt-1 text-2xl font-bold break-words">{value}</dd>
    </div>
  );
}

export function StatGrid({ children }: { children: ReactNode }) {
  return <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">{children}</dl>;
}

interface TableScrollProps {
  label: string;
  /** Shown above the scrolling area, so it stays readable however wide the table is. */
  description?: ReactNode;
  children: ReactNode;
}

/**
 * A table that scrolls within its own space on a narrow screen, so the page itself doesn't.
 * It can take keyboard focus, so people not using a mouse can scroll it too, and it says when
 * there's more to see, because a cut-off table can look complete.
 */
export function TableScroll({ label, description, children }: TableScrollProps) {
  const region = useRef<HTMLDivElement>(null);
  const [overflowing, setOverflowing] = useState(false);

  useEffect(() => {
    const element = region.current;
    if (!element) {
      return;
    }
    const measure = () => setOverflowing(element.scrollWidth > element.clientWidth);
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  return (
    <div className="space-y-1">
      {description && <p className="text-sm text-ink-secondary">{description}</p>}
      {overflowing && (
        <p className="text-xs text-ink-secondary" data-testid="scroll-hint">
          Scroll sideways to see all columns.
        </p>
      )}
      <div ref={region} role="region" aria-label={label} tabIndex={0} className="overflow-x-auto">
        {children}
      </div>
    </div>
  );
}

export function ConfusionMatrix({ metrics, caption }: { metrics: Metrics; caption: string }) {
  const ham = metrics.true_ham + metrics.ham_flagged_as_spam;
  const spam = metrics.true_spam + metrics.spam_missed;
  return (
    <TableScroll label={caption} description={caption}>
      <table className="data-table" aria-label={caption}>
        <thead>
          <tr>
            <th scope="col">Actual</th>
            <th scope="col">Predicted Ham</th>
            <th scope="col">Predicted Spam</th>
            <th scope="col">Error rate</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Ham ({count(ham)})</th>
            <td>{count(metrics.true_ham)}</td>
            <td>{count(metrics.ham_flagged_as_spam)}</td>
            <td>{share(ham ? metrics.ham_flagged_as_spam / ham : null)} wrongly flagged</td>
          </tr>
          <tr>
            <th scope="row">Spam ({count(spam)})</th>
            <td>{count(metrics.spam_missed)}</td>
            <td>{count(metrics.true_spam)}</td>
            <td>{share(spam ? metrics.spam_missed / spam : null)} missed</td>
          </tr>
        </tbody>
      </table>
    </TableScroll>
  );
}

interface LabelBalanceBarProps {
  ham: { rows: number; share: number };
  spam: { rows: number; share: number };
}

/** One whole split into two parts. The legend carries the numbers, so no text sits on colour. */
export function LabelBalanceBar({ ham, spam }: LabelBalanceBarProps) {
  return (
    <div>
      <div
        role="img"
        aria-label={`Ham ${share(ham.share)}, Spam ${share(spam.share)}`}
        className="flex h-5 w-full gap-0.5"
      >
        <div className="h-full rounded-l-lg bg-ham" style={{ width: `${ham.share * 100}%` }} />
        <div className="h-full rounded-r-lg bg-spam" style={{ width: `${spam.share * 100}%` }} />
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <li className="flex items-center gap-2">
          <span aria-hidden="true" className="h-2.5 w-2.5 rounded-full bg-ham" />
          Ham: {count(ham.rows)} rows ({share(ham.share)})
        </li>
        <li className="flex items-center gap-2">
          <span aria-hidden="true" className="h-2.5 w-2.5 rounded-full bg-spam" />
          Spam: {count(spam.rows)} rows ({share(spam.share)})
        </li>
      </ul>
    </div>
  );
}
