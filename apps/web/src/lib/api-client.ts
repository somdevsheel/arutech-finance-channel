import { clientEnv, serverEnv } from "@/lib/env";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function resolveBaseUrl(): string {
  if (typeof window === "undefined") {
    return serverEnv?.API_INTERNAL_URL ?? clientEnv.NEXT_PUBLIC_API_URL;
  }
  return clientEnv.NEXT_PUBLIC_API_URL;
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  parseJson?: boolean;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { body, parseJson = true, headers, ...rest } = options;
  const baseUrl = resolveBaseUrl();

  const response = await fetch(`${baseUrl}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorBody: unknown = null;
    try {
      errorBody = await response.json();
    } catch {
      // Response had no JSON body; keep errorBody as null.
    }

    const message =
      (errorBody as { detail?: string } | null)?.detail ??
      `Request to ${path} failed with status ${response.status}`;

    throw new ApiError(response.status, message, errorBody);
  }

  if (!parseJson || response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
