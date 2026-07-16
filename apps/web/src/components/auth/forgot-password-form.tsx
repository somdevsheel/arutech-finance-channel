"use client";

import { useState } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  passwordResetConfirmSchema,
  passwordResetRequestSchema,
  type PasswordResetConfirmInput,
  type PasswordResetRequestInput,
} from "@/lib/auth/schemas";
import { confirmPasswordResetAction, requestPasswordResetAction } from "@/lib/auth/actions";

type Step = "request" | "confirm" | "done";

export function ForgotPasswordForm() {
  const [step, setStep] = useState<Step>("request");

  const requestForm = useForm<PasswordResetRequestInput>({
    resolver: zodResolver(passwordResetRequestSchema),
  });
  const confirmForm = useForm<PasswordResetConfirmInput>({
    resolver: zodResolver(passwordResetConfirmSchema),
  });

  async function onRequestSubmit(values: PasswordResetRequestInput) {
    const result = await requestPasswordResetAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    confirmForm.setValue("email", values.email);
    setStep("confirm");
    toast.success("If that account exists, a reset code is on its way.");
  }

  async function onConfirmSubmit(values: PasswordResetConfirmInput) {
    const result = await confirmPasswordResetAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    setStep("done");
  }

  if (step === "done") {
    return (
      <div className="space-y-4 rounded-xl border bg-background p-6 text-center shadow-sm">
        <h1 className="text-lg font-semibold">Password updated</h1>
        <p className="text-sm text-muted-foreground">
          Sign in with your new password.
        </p>
        <Button render={<Link href="/login" />} className="w-full">
          Go to sign in
        </Button>
      </div>
    );
  }

  if (step === "confirm") {
    return (
      <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
        <div>
          <h1 className="text-lg font-semibold">Reset your password</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter the code we emailed you and choose a new password.
          </p>
        </div>
        <form onSubmit={confirmForm.handleSubmit(onConfirmSubmit)} className="space-y-4">
          <input type="hidden" {...confirmForm.register("email")} />
          <div className="space-y-1.5">
            <Label htmlFor="code">Verification code</Label>
            <Input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              {...confirmForm.register("code")}
            />
            {confirmForm.formState.errors.code && (
              <p className="text-xs text-destructive">
                {confirmForm.formState.errors.code.message}
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new_password">New password</Label>
            <Input id="new_password" type="password" {...confirmForm.register("new_password")} />
            {confirmForm.formState.errors.new_password && (
              <p className="text-xs text-destructive">
                {confirmForm.formState.errors.new_password.message}
              </p>
            )}
          </div>
          <Button
            type="submit"
            disabled={confirmForm.formState.isSubmitting}
            className="w-full"
          >
            {confirmForm.formState.isSubmitting ? "Resetting..." : "Reset password"}
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
      <div>
        <h1 className="text-lg font-semibold">Forgot your password?</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you a reset code.
        </p>
      </div>
      <form onSubmit={requestForm.handleSubmit(onRequestSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...requestForm.register("email")} />
          {requestForm.formState.errors.email && (
            <p className="text-xs text-destructive">
              {requestForm.formState.errors.email.message}
            </p>
          )}
        </div>
        <Button type="submit" disabled={requestForm.formState.isSubmitting} className="w-full">
          {requestForm.formState.isSubmitting ? "Sending..." : "Send reset code"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-foreground hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
