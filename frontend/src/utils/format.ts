/** Turn values from the API into readable text. Nothing here creates or changes a result. */

const MODEL_NAMES: Record<string, string> = {
  linear_svm: "Linear SVM",
  logistic_regression: "Logistic Regression",
  multinomial_nb: "Multinomial Naive Bayes",
};

const FEATURE_NAMES: Record<string, string> = {
  word_1: "Single words",
  word_1_2: "Words and bigrams",
};

const STYLE_NAMES: Record<string, string> = {
  digits_only: "Digit style",
  placeholder_only: "Placeholder style",
  neither: "Neither style",
};

const REMOVAL_NAMES: Record<string, string> = {
  baseline_no_removal: "None (baseline)",
  remove_style_300: "Top 300 style-leaning",
  remove_style_1000: "Top 1,000 style-leaning",
  remove_ham_300: "Top 300 Ham-leaning",
  remove_style_300_and_ham_300: "Top 300 style-leaning and top 300 Ham-leaning",
  remove_ham_300_and_spam_300: "Top 300 Ham-leaning and top 300 Spam-leaning",
};

const FLAG_NAMES: Record<string, string> = {
  has_uppercase: "Uppercase letters",
  has_digit: "Digits",
  has_escapenumber: "escapenumber placeholder",
  has_escapelong: "escapelong placeholder",
  has_non_ascii: "Text outside ASCII",
  has_spaced_punctuation: "Spaced punctuation",
  has_url_scheme: "http:// or https://",
  has_https_word: "https as a word",
  has_at_sign: "@ sign",
};

export const modelName = (value: string): string => MODEL_NAMES[value] ?? value;
export const featureName = (value: string): string => FEATURE_NAMES[value] ?? value;
export const styleName = (value: string): string => STYLE_NAMES[value] ?? value;
export const removalName = (value: string): string => REMOVAL_NAMES[value] ?? value;
export const flagName = (value: string): string => FLAG_NAMES[value] ?? value;

export function bandName(value: string): string {
  if (value.endsWith("_and_above")) {
    return `${value.replace("_and_above", "")} and above`;
  }
  const [low, high] = value.split("_to_");
  if (low === undefined || high === undefined) {
    return value;
  }
  return Number(low) === 0 ? `Under ${high}` : `${low} to ${high}`;
}

export function settingText(setting: Record<string, number>): string {
  return Object.entries(setting)
    .map(([name, value]) => `${name}=${value}`)
    .join(", ");
}

export const count = (value: number): string => value.toLocaleString("en-GB");

/** Metrics keep the four decimal places they're saved with. */
export const metric = (value: number): string => value.toFixed(4);

/** Show a share of rows as a percentage. This is never used for a prediction. */
export const share = (value: number | null, decimals = 1): string =>
  value === null ? "Not available" : `${(value * 100).toFixed(decimals)}%`;

export const signed = (value: number, decimals = 3): string =>
  `${value > 0 ? "+" : ""}${value.toFixed(decimals)}`;

export function fileSize(bytes: number): string {
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}
