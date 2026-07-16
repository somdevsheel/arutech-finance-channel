import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCurrentUser } from "@/lib/auth/session";
import { getOwnLoanApplications } from "@/lib/loans/session";
import { LoanApplicationCard } from "@/components/portal/loan-application-card";

export const metadata: Metadata = {
  title: "Loan Applications",
  robots: { index: false, follow: false },
};

export default async function LoansPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const applications = await getOwnLoanApplications();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Loan applications</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Track every application you&apos;ve submitted.
          </p>
        </div>
        <Button render={<Link href="/loans/apply" />}>
          <Plus className="size-4" /> Apply for a loan
        </Button>
      </div>

      {applications.length === 0 ? (
        <div className="rounded-xl border bg-background p-10 text-center">
          <p className="text-sm text-muted-foreground">
            You haven&apos;t applied for a loan yet.
          </p>
          <Button className="mt-4" render={<Link href="/loans/apply" />}>
            Apply for a loan
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {applications.map((application) => (
            <LoanApplicationCard key={application.id} application={application} />
          ))}
        </div>
      )}
    </div>
  );
}
