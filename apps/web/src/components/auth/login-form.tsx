"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  loginSchema,
  otpRequestSchema,
  otpVerifySchema,
  type LoginInput,
  type OtpRequestInput,
  type OtpVerifyInput,
} from "@/lib/auth/schemas";
import { loginAction, requestOtpAction, verifyOtpAction } from "@/lib/auth/actions";

type Mode = "password" | "otp-request" | "otp-verify";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/dashboard";
  const [mode, setMode] = useState<Mode>("password");
  const [otpEmail, setOtpEmail] = useState("");

  const passwordForm = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });
  const otpRequestForm = useForm<OtpRequestInput>({ resolver: zodResolver(otpRequestSchema) });
  const otpVerifyForm = useForm<OtpVerifyInput>({ resolver: zodResolver(otpVerifySchema) });

  async function onPasswordSubmit(values: LoginInput) {
    const result = await loginAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    router.push(next);
  }

  async function onOtpRequestSubmit(values: OtpRequestInput) {
    const result = await requestOtpAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    setOtpEmail(values.email);
    otpVerifyForm.setValue("email", values.email);
    setMode("otp-verify");
    toast.success("If that account exists, a code is on its way.");
  }

  async function onOtpVerifySubmit(values: OtpVerifyInput) {
    const result = await verifyOtpAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    router.push(next);
  }

  if (mode === "otp-verify") {
    return (
      <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
        <div>
          <h1 className="text-lg font-semibold">Enter your code</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            We sent a 6-digit code to {otpEmail}.
          </p>
        </div>
        <form onSubmit={otpVerifyForm.handleSubmit(onOtpVerifySubmit)} className="space-y-4">
          <input type="hidden" {...otpVerifyForm.register("email")} />
          <div className="space-y-1.5">
            <Label htmlFor="code">Verification code</Label>
            <Input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              {...otpVerifyForm.register("code")}
            />
            {otpVerifyForm.formState.errors.code && (
              <p className="text-xs text-destructive">
                {otpVerifyForm.formState.errors.code.message}
              </p>
            )}
          </div>
          <Button
            type="submit"
            disabled={otpVerifyForm.formState.isSubmitting}
            className="w-full"
          >
            {otpVerifyForm.formState.isSubmitting ? "Verifying..." : "Verify & sign in"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={() => setMode("otp-request")}
          >
            Use a different email
          </Button>
        </form>
      </div>
    );
  }

  if (mode === "otp-request") {
    return (
      <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
        <div>
          <h1 className="text-lg font-semibold">Sign in with a code</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            We&apos;ll email you a one-time verification code.
          </p>
        </div>
        <form onSubmit={otpRequestForm.handleSubmit(onOtpRequestSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="otp-email">Email</Label>
            <Input id="otp-email" type="email" {...otpRequestForm.register("email")} />
            {otpRequestForm.formState.errors.email && (
              <p className="text-xs text-destructive">
                {otpRequestForm.formState.errors.email.message}
              </p>
            )}
          </div>
          <Button
            type="submit"
            disabled={otpRequestForm.formState.isSubmitting}
            className="w-full"
          >
            {otpRequestForm.formState.isSubmitting ? "Sending..." : "Send code"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={() => setMode("password")}
          >
            Back to password sign-in
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
      <div>
        <h1 className="text-lg font-semibold">Sign in</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome back to the Arutech customer portal.
        </p>
      </div>
      <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...passwordForm.register("email")} />
          {passwordForm.formState.errors.email && (
            <p className="text-xs text-destructive">
              {passwordForm.formState.errors.email.message}
            </p>
          )}
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Forgot password?
            </Link>
          </div>
          <Input id="password" type="password" {...passwordForm.register("password")} />
          {passwordForm.formState.errors.password && (
            <p className="text-xs text-destructive">
              {passwordForm.formState.errors.password.message}
            </p>
          )}
        </div>
        <Button type="submit" disabled={passwordForm.formState.isSubmitting} className="w-full">
          {passwordForm.formState.isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={() => setMode("otp-request")}
        >
          Sign in with a one-time code
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-medium text-foreground hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
