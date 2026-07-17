"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { revokePermissionAction } from "@/lib/admin/actions";

export function RevokePermissionButton({
  roleId,
  permissionCode,
}: {
  roleId: string;
  permissionCode: string;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    startTransition(async () => {
      const result = await revokePermissionAction(roleId, permissionCode);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      router.refresh();
    });
  }

  return (
    <Button type="button" size="sm" variant="ghost" disabled={isPending} onClick={handleClick}>
      Revoke
    </Button>
  );
}
