import { describe, expect, it } from "vitest";

import { bandName, count, featureName, fileSize, flagName, metric, modelName, removalName, settingText, share, signed, styleName } from "./format";

describe("format", () => {
  it("names similarity bands", () => {
    expect(bandName("0.00_to_0.80")).toBe("Under 0.80");
    expect(bandName("0.80_to_0.90")).toBe("0.80 to 0.90");
    expect(bandName("0.95_and_above")).toBe("0.95 and above");
    expect(bandName("unexpected")).toBe("unexpected");
  });

  it("names models, features, styles, removals and flags, keeping unknown values", () => {
    expect(modelName("linear_svm")).toBe("Linear SVM");
    expect(modelName("something_new")).toBe("something_new");
    expect(featureName("word_1_2")).toBe("Words and bigrams");
    expect(styleName("digits_only")).toBe("Digit style");
    expect(removalName("baseline_no_removal")).toBe("None (baseline)");
    expect(flagName("has_digit")).toBe("Digits");
  });

  it("formats numbers", () => {
    expect(count(193852)).toBe("193,852");
    expect(metric(0.5)).toBe("0.5000");
    expect(share(0.473)).toBe("47.3%");
    expect(share(0.12345, 2)).toBe("12.35%");
    expect(share(null)).toBe("Not available");
    expect(fileSize(2097152)).toBe("2.0 MB");
    expect(settingText({ C: 10 })).toBe("C=10");
  });

  it("always shows the direction of a score", () => {
    expect(signed(1.5)).toBe("+1.500");
    expect(signed(-1.5)).toBe("-1.500");
    expect(signed(0)).toBe("0.000");
  });
});
