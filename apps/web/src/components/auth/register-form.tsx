"use client";

import { useState } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { registerSchema, type RegisterInput } from "@/lib/auth/schemas";
import { registerAction } from "@/lib/auth/actions";

export function RegisterForm() {
  const [registered, setRegistered] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterInput) {
    const result = await registerAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    setRegistered(true);
  }

  if (registered) {
    return (
      <div className="space-y-4 rounded-xl border bg-background p-6 text-center shadow-sm">
        <h1 className="text-lg font-semibold">Account created</h1>
        <p className="text-sm text-muted-foreground">
          You can sign in now with the email and password you just set.
        </p>
        <Button render={<Link href="/login" />} className="w-full">
          Go to sign in
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-5 rounded-xl border bg-background p-6 shadow-sm">
      <div>
        <h1 className="text-lg font-semibold">Create your account</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Set up customer portal access to track your loan applications.
        </p>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" {...register("full_name")} />
          {errors.full_name && (
            <p className="text-xs text-destructive">{errors.full_name.message}</p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register("email")} />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="phone">Phone (optional)</Label>
          <Input id="phone" type="tel" {...register("phone")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register("password")} />
          {errors.password && (
            <p className="text-xs text-destructive">{errors.password.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            At least 8 characters, with a letter and a digit.
          </p>
        </div>
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-foreground hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
