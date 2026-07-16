import { afterEach, describe, expect, it, vi } from "vitest";
import { trackEvent, trackPageview } from "@/lib/analytics";

describe("analytics", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete window.gtag;
  });

  it("does not throw when gtag is unavailable", () => {
    expect(() => trackPageview("/loans")).not.toThrow();
    expect(() => trackEvent("cta_click")).not.toThrow();
  });

  it("does not call gtag because NEXT_PUBLIC_GA_MEASUREMENT_ID is unset in tests", () => {
    const gtagMock = vi.fn();
    window.gtag = gtagMock;

    trackPageview("/loans");
    trackEvent("cta_click", { label: "apply-now" });

    // analyticsEnabled is computed once from clientEnv at module load, and
    // the test environment never sets a measurement ID — this is the
    // no-op path every dev/CI run actually exercises.
    expect(gtagMock).not.toHaveBeenCalled();
  });
});
