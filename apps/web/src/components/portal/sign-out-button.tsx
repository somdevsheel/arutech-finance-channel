"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { logoutAction } from "@/lib/auth/actions";
import { cn } from "@/lib/utils";

export function SignOutButton({ className }: { className?: string }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleSignOut() {
    startTransition(async () => {
      await logoutAction();
      router.push("/login");
    });
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className={cn(className)}
      onClick={handleSignOut}
      disabled={isPending}
    >
      {isPending ? "Signing out..." : "Sign out"}
    </Button>
  );
}
