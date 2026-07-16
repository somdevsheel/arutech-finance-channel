import { headers } from "next/headers";

/**
 * Server Actions call the API server-to-server, so without this the API
 * would see every customer-portal request as coming from the web
 * container instead of the actual visitor — silently breaking Phase 2's
 * per-route rate limits and audit-log IPs (see
 * docs/phase-4-architecture.md and apps/api's TRUSTED_PROXY_IPS).
 * Forwards whatever nginx/the browser already set; falls back to nothing
 * in plain `pnpm dev` (no proxy in front), same as before Phase 4.
 */
export async function getForwardedRequestHeaders(): Promise<Record<string, string>> {
  const incoming = await headers();
  const forwarded: Record<string, string> = {};

  const forwardedFor = incoming.get("x-forwarded-for");
  if (forwardedFor) forwarded["X-Forwarded-For"] = forwardedFor;

  const userAgent = incoming.get("user-agent");
  if (userAgent) forwarded["User-Agent"] = userAgent;

  return forwarded;
}
