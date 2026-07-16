"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { withdrawApplicationAction } from "@/lib/loans/actions";

export function WithdrawApplicationButton({ applicationId }: { applicationId: string }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleWithdraw() {
    startTransition(async () => {
      const result = await withdrawApplicationAction(applicationId);
      if (!result.ok) {
        toast.error(result.error);
        return;
      }
      toast.success("Application withdrawn");
      router.refresh();
    });
  }

  return (
    <Button type="button" variant="destructive" disabled={isPending} onClick={handleWithdraw}>
      {isPending ? "Withdrawing..." : "Withdraw application"}
    </Button>
  );
}
