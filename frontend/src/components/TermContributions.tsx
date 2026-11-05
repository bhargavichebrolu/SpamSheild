import type { Explanation, TermContribution } from "../types/api";
import { signed } from "../utils/format";

function displayTerm(term: string): string {
  return term === "escapenumber" ? "escapenumber (a number)" : term;
}

interface TermListProps {
  title: string;
  swatch: string;
  terms: TermContribution[];
  largest: number;
}

function TermList({ title, swatch, terms, largest }: TermListProps) {
  return (
    <section aria-label={title} className="min-w-0">
      <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold">
        <span aria-hidden="true" className={`inline-block h-2.5 w-2.5 rounded-full ${swatch}`} />
        {title}
      </h4>
      {terms.length === 0 ? (
        <p className="text-sm text-ink-secondary">None in this message.</p>
      ) : (
        <ul className="space-y-2">
          {terms.map(({ term, contribution }) => (
            <li key={term}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 break-words">{displayTerm(term)}</span>
                <span className="shrink-0 tabular-nums text-ink-secondary">{signed(contribution)}</span>
              </div>
              <div aria-hidden="true" className="mt-1 h-2 border-l border-axis">
                <div
                  title={`${term}: ${signed(contribution)}`}
                  className={`h-2 rounded-r ${swatch}`}
                  style={{ width: `${Math.max((Math.abs(contribution) / largest) * 100, 1)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

interface TermContributionsProps {
  explanation: Explanation;
  score: number;
}

/** Show which terms moved the score. All values and bars use the same scale. */
export function TermContributions({ explanation, score }: TermContributionsProps) {
  const { spam_terms: spamTerms, ham_terms: hamTerms, other_terms_total: otherTotal, intercept, note } = explanation;
  const largest = Math.max(...[...spamTerms, ...hamTerms].map(({ contribution }) => Math.abs(contribution)), 1e-9);
  const spamTotal = spamTerms.reduce((total, { contribution }) => total + contribution, 0);
  const hamTotal = hamTerms.reduce((total, { contribution }) => total + contribution, 0);

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-lg font-semibold">Words that influenced this score</h3>
        <p className="mt-1 text-sm text-ink-secondary">{note}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <TermList title="Pushed towards spam" swatch="bg-spam" terms={spamTerms} largest={largest} />
        <TermList title="Pushed towards ham" swatch="bg-ham" terms={hamTerms} largest={largest} />
      </div>

      <div className="overflow-x-auto">
        <table className="data-table max-w-md">
          <caption>How the decision score adds up</caption>
          <tbody>
            <tr>
              <th scope="row">Model's starting score (intercept)</th>
              <td>{signed(intercept)}</td>
            </tr>
            <tr>
              <th scope="row">Listed terms towards spam</th>
              <td>{signed(spamTotal)}</td>
            </tr>
            <tr>
              <th scope="row">Listed terms towards ham</th>
              <td>{signed(hamTotal)}</td>
            </tr>
            <tr>
              <th scope="row">All other terms</th>
              <td>{signed(otherTotal)}</td>
            </tr>
            <tr>
              <th scope="row" className="font-semibold">
                Decision score
              </th>
              <td className="font-semibold">{signed(score)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
