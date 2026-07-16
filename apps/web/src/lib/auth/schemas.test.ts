import { describe, expect, it } from "vitest";
import {
  loginSchema,
  otpVerifySchema,
  passwordResetConfirmSchema,
  registerSchema,
} from "@/lib/auth/schemas";

describe("registerSchema", () => {
  const base = {
    full_name: "Ada Lovelace",
    email: "ada@example.com",
    password: "s3cure-pass",
  };

  it("accepts a valid registration payload", () => {
    expect(registerSchema.safeParse(base).success).toBe(true);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = registerSchema.safeParse({ ...base, password: "a1" });
    expect(result.success).toBe(false);
  });

  it("rejects a password with no digit", () => {
    const result = registerSchema.safeParse({ ...base, password: "onlyletters" });
    expect(result.success).toBe(false);
  });

  it("rejects a password with no letter", () => {
    const result = registerSchema.safeParse({ ...base, password: "12345678" });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = registerSchema.safeParse({ ...base, email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("allows an empty phone", () => {
    expect(registerSchema.safeParse({ ...base, phone: "" }).success).toBe(true);
  });
});

describe("loginSchema", () => {
  it("rejects an empty password", () => {
    const result = loginSchema.safeParse({ email: "ada@example.com", password: "" });
    expect(result.success).toBe(false);
  });
});

describe("otpVerifySchema", () => {
  it("requires exactly 6 digits", () => {
    expect(
      otpVerifySchema.safeParse({ email: "ada@example.com", code: "12345" }).success,
    ).toBe(false);
    expect(
      otpVerifySchema.safeParse({ email: "ada@example.com", code: "1234ab" }).success,
    ).toBe(false);
    expect(
      otpVerifySchema.safeParse({ email: "ada@example.com", code: "123456" }).success,
    ).toBe(true);
  });
});

describe("passwordResetConfirmSchema", () => {
  it("applies the same password strength rules as registration", () => {
    const result = passwordResetConfirmSchema.safeParse({
      email: "ada@example.com",
      code: "123456",
      new_password: "weak",
    });
    expect(result.success).toBe(false);
  });
});
