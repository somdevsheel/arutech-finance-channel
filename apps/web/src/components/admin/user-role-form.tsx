"use client";

import { useTransition } from "react";
import { toast } from "sonner";
import { setUserRoleAction } from "@/lib/admin/actions";
import type { UserRole } from "@/types/admin";

const ROLES: UserRole[] = ["customer", "employee", "partner", "admin"];

export function UserRoleForm({
  userId,
  currentRole,
}: {
  userId: string;
  currentRole: UserRole;
}) {
  const [isPending, startTransition] = useTransition();

  function handleChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const formData = new FormData();
    formData.set("role", event.target.value);
    startTransition(async () => {
      const result = await setUserRoleAction(userId, formData);
      if (!result.ok) toast.error(result.error);
      else toast.success(`Role updated to ${event.target.value}.`);
    });
  }

  return (
    <select
      defaultValue={currentRole}
      disabled={isPending}
      onChange={handleChange}
      className="rounded-md border border-input bg-background px-2 py-1 text-sm"
    >
      {ROLES.map((role) => (
        <option key={role} value={role}>
          {role}
        </option>
      ))}
    </select>
  );
}
