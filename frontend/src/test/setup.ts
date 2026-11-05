import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Remove each test's page, so that results can't carry over into the next test.
afterEach(cleanup);
