import { clientEnv } from "@/lib/env";

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

export const analyticsEnabled = Boolean(clientEnv.NEXT_PUBLIC_GA_MEASUREMENT_ID);

/** No-op whenever NEXT_PUBLIC_GA_MEASUREMENT_ID is unset (every dev/CI
 * environment) or gtag hasn't loaded yet — callers never need to guard. */
export function trackPageview(url: string): void {
  if (!analyticsEnabled || typeof window === "undefined" || !window.gtag) return;
  window.gtag("event", "page_view", { page_path: url });
}

export function trackEvent(
  name: string,
  params?: Record<string, string | number | boolean>,
): void {
  if (!analyticsEnabled || typeof window === "undefined" || !window.gtag) return;
  window.gtag("event", name, params);
}
