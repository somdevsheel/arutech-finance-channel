import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLoanProductBySlug } from "@/content/loan-products";
import { formatDate, formatInr } from "@/lib/format";
import { LoanStatusBadge } from "@/components/portal/loan-status-badge";
import type { LoanApplication } from "@/types/loans";

export function LoanApplicationCard({ application }: { application: LoanApplication }) {
  const product = getLoanProductBySlug(application.loan_product_slug);

  return (
    <Link href={`/applications/${application.id}`}>
      <Card className="transition-colors hover:bg-muted/40">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>{product?.name ?? application.loan_product_slug}</CardTitle>
            <LoanStatusBadge status={application.status} />
          </div>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Requested</span>
            <span className="font-medium">{formatInr(application.requested_amount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Tenure</span>
            <span className="font-medium">{application.tenure_months} months</span>
          </div>
          {application.created_at && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Applied on</span>
              <span className="font-medium">{formatDate(application.created_at)}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
