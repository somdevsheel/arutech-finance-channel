import { z } from "zod";

// Mirrors apps/api's _validate_password_strength (api/v1/schemas/auth.py):
// min 8 chars, at least one letter, at least one digit.
const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128)
  .refine((value) => /[A-Za-z]/.test(value), {
    message: "Password must contain at least one letter",
  })
  .refine((value) => /\d/.test(value), {
    message: "Password must contain at least one digit",
  });

const otpCodeSchema = z
  .string()
  .length(6, "Enter the 6-digit code")
  .regex(/^\d{6}$/, "The code must be 6 digits");

export const loginSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  full_name: z.string().min(1, "Enter your full name").max(255),
  email: z.email("Enter a valid email address"),
  phone: z.string().max(20).optional().or(z.literal("")),
  password: passwordSchema,
});
export type RegisterInput = z.infer<typeof registerSchema>;

export const otpRequestSchema = z.object({
  email: z.email("Enter a valid email address"),
});
export type OtpRequestInput = z.infer<typeof otpRequestSchema>;

export const otpVerifySchema = z.object({
  email: z.email("Enter a valid email address"),
  code: otpCodeSchema,
});
export type OtpVerifyInput = z.infer<typeof otpVerifySchema>;

export const passwordResetRequestSchema = z.object({
  email: z.email("Enter a valid email address"),
});
export type PasswordResetRequestInput = z.infer<typeof passwordResetRequestSchema>;

export const passwordResetConfirmSchema = z.object({
  email: z.email("Enter a valid email address"),
  code: otpCodeSchema,
  new_password: passwordSchema,
});
export type PasswordResetConfirmInput = z.infer<typeof passwordResetConfirmSchema>;
