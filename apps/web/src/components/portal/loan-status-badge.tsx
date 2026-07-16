import { Badge } from "@/components/ui/badge";
import type { LoanApplicationStatus } from "@/types/loans";

const STATUS_META: Record<
  LoanApplicationStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  draft: { label: "Draft", variant: "secondary" },
  submitted: { label: "Submitted", variant: "outline" },
  under_review: { label: "Under review", variant: "outline" },
  approved: { label: "Approved", variant: "default" },
  rejected: { label: "Rejected", variant: "destructive" },
  sanctioned: { label: "Sanctioned", variant: "default" },
  disbursed: { label: "Disbursed", variant: "default" },
  closed: { label: "Closed", variant: "secondary" },
  withdrawn: { label: "Withdrawn", variant: "secondary" },
};

export function LoanStatusBadge({ status }: { status: LoanApplicationStatus }) {
  const meta = STATUS_META[status];
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}
