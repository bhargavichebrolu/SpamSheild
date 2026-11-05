import { useEffect } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";

import { ClassifierPage } from "./pages/ClassifierPage";
import { DatasetPage } from "./pages/DatasetPage";
import { ModelsPage } from "./pages/ModelsPage";

const PAGES = [
  { path: "/", label: "Classify", title: "Classify an email" },
  { path: "/models", label: "Models", title: "Model comparison" },
  { path: "/dataset", label: "Dataset", title: "Dataset explorer" },
];

function NotFoundPage() {
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p>
        <Link className="text-link underline" to="/">
          Go to the classifier
        </Link>
      </p>
    </div>
  );
}

export function App() {
  const { pathname } = useLocation();

  useEffect(() => {
    const page = PAGES.find(({ path }) => path === pathname);
    document.title = page ? `${page.title} | SpamShield AI` : "Page not found | SpamShield AI";
  }, [pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:rounded focus:bg-surface focus:p-2"
      >
        Skip to main content
      </a>

      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="text-lg font-semibold text-ink">
            SpamShield AI
          </Link>
          <nav aria-label="Main">
            <ul className="flex gap-1">
              {PAGES.map(({ path, label }) => (
                <li key={path}>
                  <NavLink
                    to={path}
                    end
                    className={({ isActive }) =>
                      `block rounded px-3 py-2 text-sm font-medium hover:bg-line ${isActive ? "bg-line text-ink" : "text-ink-secondary"}`
                    }
                  >
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Routes>
          <Route path="/" element={<ClassifierPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/dataset" element={<DatasetPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      <footer className="border-t border-line bg-surface">
        <p className="mx-auto max-w-5xl px-4 py-3 text-sm text-ink-secondary">
          A learning and research prototype, not an email security product. Don't use it to block, delete or move email,
          or to detect phishing, fraud or malware.
        </p>
      </footer>
    </div>
  );
}
