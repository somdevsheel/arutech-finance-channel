import { afterEach, describe, expect, it, vi } from "vitest";
import { accessTokenCookieOptions, refreshTokenCookieOptions } from "@/lib/auth/constants";

describe("session cookie options", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("is not marked secure outside production, so http://localhost still works", () => {
    vi.stubEnv("NODE_ENV", "development");
    expect(accessTokenCookieOptions().secure).toBe(false);
  });

  it("is marked secure in production", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(accessTokenCookieOptions().secure).toBe(true);
  });

  it("gives the refresh cookie a longer lifetime than the access cookie", () => {
    expect(refreshTokenCookieOptions().maxAge).toBeGreaterThan(
      accessTokenCookieOptions().maxAge,
    );
  });

  it("scopes both cookies to the whole site as httpOnly, lax cookies", () => {
    for (const options of [accessTokenCookieOptions(), refreshTokenCookieOptions()]) {
      expect(options.httpOnly).toBe(true);
      expect(options.sameSite).toBe("lax");
      expect(options.path).toBe("/");
    }
  });
});
