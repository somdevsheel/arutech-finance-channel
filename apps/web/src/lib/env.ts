import { z } from "zod";

const serverEnvSchema = z.object({
  API_INTERNAL_URL: z
    .url()
    .default("http://localhost:8000"),
});

const clientEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: z.url().default("http://localhost:8000"),
  NEXT_PUBLIC_APP_NAME: z.string().default("Arutech Finance Platform"),
  // Canonical origin used for sitemap/robots URLs, JSON-LD, and OG tags.
  NEXT_PUBLIC_SITE_URL: z.url().default("http://localhost:3000"),
  // Unset by default (every dev/CI environment): analytics stays a no-op
  // until a real GA4 measurement ID is configured. See lib/analytics.ts.
  NEXT_PUBLIC_GA_MEASUREMENT_ID: z.string().optional(),
});

function parseServerEnv() {
  const parsed = serverEnvSchema.safeParse({
    API_INTERNAL_URL: process.env.API_INTERNAL_URL,
  });

  if (!parsed.success) {
    throw new Error(
      `Invalid server environment variables: ${parsed.error.message}`,
    );
  }

  return parsed.data;
}

function parseClientEnv() {
  const parsed = clientEnvSchema.safeParse({
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL,
    NEXT_PUBLIC_GA_MEASUREMENT_ID: process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID,
  });

  if (!parsed.success) {
    throw new Error(
      `Invalid client environment variables: ${parsed.error.message}`,
    );
  }

  return parsed.data;
}

export const clientEnv = parseClientEnv();

export const serverEnv = typeof window === "undefined" ? parseServerEnv() : undefined;
