"use client";

import { useRef, useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { ActionResult } from "@/lib/auth/actions";

/**
 * A plain `<form action={serverAction}>` can't surface a failed
 * ActionResult — Next.js requires a form action to return void. This
 * wraps the submit in a transition instead, so every Phase 9 admin
 * create-form gets the same toast-on-error / refresh-on-success
 * behavior without each page reimplementing it.
 */
export function AdminCreateForm({
  action,
  className,
  children,
}: {
  action: (formData: FormData) => Promise<ActionResult>;
  className?: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    startTransition(async () => {
      const result = await action(formData);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      toast.success("Created.");
      formRef.current?.reset();
      router.refresh();
    });
  }

  return (
    <form ref={formRef} onSubmit={handleSubmit} className={className} aria-busy={isPending}>
      {children}
    </form>
  );
}
