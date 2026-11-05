import { useEffect } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";

import { DatasetPage } from "./pages/DatasetPage";
import { HomePage } from "./pages/HomePage";
import { ModelsPage } from "./pages/ModelsPage";

const PAGES = [
  { path: "/", label: "Classify", title: "Classify an email" },
  { path: "/models", label: "Models", title: "Model comparison" },
  { path: "/dataset", label: "Dataset", title: "Dataset explorer" },
];

function ShieldLogo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-7 w-7" fill="none">
      <path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Z" fill="white" />
      <path d="m8.5 12 2.5 2.5 4.5-5" stroke="#6d28d9" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

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
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-10 focus:rounded focus:bg-surface focus:p-2"
      >
        Skip to main content
      </a>

      <header className="brand-gradient sticky top-0 z-[5] shadow-lg">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 text-xl font-extrabold text-white">
            <ShieldLogo />
            SpamShield AI
          </Link>
          <nav aria-label="Main">
            <ul className="flex gap-1">
              {PAGES.map(({ path, label }) => (
                <li key={path}>
                  <NavLink to={path} end className="nav-link">
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/dataset" element={<DatasetPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      <footer className="brand-gradient mt-6">
        <p className="mx-auto max-w-6xl px-4 py-4 text-sm">
          A learning and research prototype, not an email security product. Don't use it to block, delete or move email,
          or to detect phishing, fraud or malware.
        </p>
      </footer>
    </div>
  );
}
