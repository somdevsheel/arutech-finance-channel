import { describe, expect, it, vi, afterEach } from "vitest";
import { apiFetch, ApiError } from "@/lib/api-client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on a successful response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch<{ status: string }>("/api/v1/health");

    expect(result).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/health"),
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("throws ApiError with the response detail on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not found" }), { status: 404 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/api/v1/missing")).rejects.toMatchObject({
      status: 404,
      message: "Not found",
    });
  });

  it("throws a generic ApiError when the error body is not JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("internal error", { status: 500 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    let caught: ApiError | undefined;
    try {
      await apiFetch("/api/v1/health");
    } catch (e) {
      caught = e as ApiError;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught?.status).toBe(500);
  });

  it("returns undefined for 204 responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch("/api/v1/health");

    expect(result).toBeUndefined();
  });
});
