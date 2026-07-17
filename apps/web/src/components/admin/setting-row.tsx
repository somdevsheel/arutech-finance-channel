"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { updateSettingAction } from "@/lib/admin/actions";
import type { SystemSetting } from "@/types/admin";

export function SettingRow({ setting }: { setting: SystemSetting }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await updateSettingAction(setting.key, formData);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      toast.success("Setting updated.");
      router.refresh();
    });
  }

  return (
    <form action={handleSubmit} className="flex flex-wrap items-center justify-between gap-3 py-4">
      <div>
        <p className="text-sm font-medium">{setting.key}</p>
        <p className="text-xs text-muted-foreground">{setting.description}</p>
      </div>
      <div className="flex items-center gap-2">
        {setting.value_type === "boolean" ? (
          <select
            name="value"
            defaultValue={setting.value}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : (
          <input
            name="value"
            defaultValue={setting.value}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
        )}
        <Button type="submit" size="sm" disabled={isPending}>
          Save
        </Button>
      </div>
    </form>
  );
}
