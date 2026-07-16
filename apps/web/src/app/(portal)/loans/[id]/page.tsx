import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getCurrentUser } from "@/lib/auth/session";
import { getOwnLoanApplication, getOwnLoanDocuments } from "@/lib/loans/session";
import { getLoanProductBySlug } from "@/content/loan-products";
import { formatDate, formatInr } from "@/lib/format";
import { LoanStatusBadge } from "@/components/portal/loan-status-badge";
import { DocumentChecklist } from "@/components/portal/document-checklist";
import { WithdrawApplicationButton } from "@/components/portal/withdraw-application-button";

export const metadata: Metadata = {
  title: "Loan Application",
  robots: { index: false, follow: false },
};

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b py-2.5 text-sm last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export default async function LoanApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const { id } = await params;
  const application = await getOwnLoanApplication(id);
  if (!application) notFound();

  const documents = await getOwnLoanDocuments(id);
  const product = getLoanProductBySlug(application.loan_product_slug);
  const canWithdraw = application.status === "draft" || application.status === "submitted";

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {product?.name ?? application.loan_product_slug}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Applied {application.created_at ? formatDate(application.created_at) : "recently"}
          </p>
        </div>
        <LoanStatusBadge status={application.status} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Application details</CardTitle>
        </CardHeader>
        <CardContent>
          <Field label="Requested amount" value={formatInr(application.requested_amount)} />
          <Field label="Tenure" value={`${application.tenure_months} months`} />
          <Field label="Interest rate" value={`${application.interest_rate}% p.a.`} />
          <Field label="Net monthly income" value={formatInr(application.monthly_income)} />
          {application.eligibility_status !== "pending" && (
            <Field
              label="Eligibility"
              value={application.eligibility_status === "eligible" ? "Eligible" : "Not eligible"}
            />
          )}
        </CardContent>
      </Card>

      {application.status === "rejected" && application.rejection_reason && (
        <Card>
          <CardHeader>
            <CardTitle>Why this application was declined</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{application.rejection_reason}</p>
          </CardContent>
        </Card>
      )}

      {application.sanctioned_amount !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Sanction terms</CardTitle>
          </CardHeader>
          <CardContent>
            <Field label="Sanctioned amount" value={formatInr(application.sanctioned_amount)} />
            <Field
              label="Sanctioned tenure"
              value={`${application.sanctioned_tenure_months} months`}
            />
            {application.sanction_date && (
              <Field label="Sanctioned on" value={formatDate(application.sanction_date)} />
            )}
          </CardContent>
        </Card>
      )}

      {application.disbursed_amount !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Disbursement</CardTitle>
          </CardHeader>
          <CardContent>
            <Field label="Disbursed amount" value={formatInr(application.disbursed_amount)} />
            {application.disbursement_date && (
              <Field label="Disbursed on" value={formatDate(application.disbursement_date)} />
            )}
            {application.disbursement_reference && (
              <Field label="Reference" value={application.disbursement_reference} />
            )}
          </CardContent>
        </Card>
      )}

      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <DocumentChecklist applicationId={application.id} documents={documents} />
          </CardContent>
        </Card>
      )}

      {canWithdraw && <WithdrawApplicationButton applicationId={application.id} />}
    </div>
  );
}
