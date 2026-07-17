"use client";

import { useTransition } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import type { ActionResult } from "@/lib/auth/actions";

export function ToggleActiveButton({
  id,
  isActive,
  action,
  activeLabel = "Deactivate",
  inactiveLabel = "Activate",
}: {
  id: string;
  isActive: boolean;
  action: (id: string, isActive: boolean) => Promise<ActionResult>;
  activeLabel?: string;
  inactiveLabel?: string;
}) {
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    startTransition(async () => {
      const result = await action(id, !isActive);
      if (!result.ok) toast.error(result.error);
    });
  }

  return (
    <Button
      type="button"
      size="sm"
      variant="outline"
      disabled={isPending}
      onClick={handleClick}
    >
      {isActive ? activeLabel : inactiveLabel}
    </Button>
  );
}
