import { z } from "zod";

const serverEnvSchema = z.object({
  API_INTERNAL_URL: z
    .url()
    .default("http://localhost:8000"),
});

const clientEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: z.url().default("http://localhost:8000"),
  NEXT_PUBLIC_APP_NAME: z.string().default("Arutech Finance Platform"),
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
