"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { deleteRoleAction } from "@/lib/admin/actions";

export function DeleteRoleButton({ roleId }: { roleId: string }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    if (!confirm("Delete this role? This cannot be undone.")) return;
    startTransition(async () => {
      const result = await deleteRoleAction(roleId);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      router.refresh();
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
      Delete
    </Button>
  );
}
