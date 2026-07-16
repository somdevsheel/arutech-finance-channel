import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/session";
import { LoanApplyForm } from "@/components/portal/loan-apply-form";
import { getLoanProductBySlug } from "@/content/loan-products";

export const metadata: Metadata = {
  title: "Apply for a Loan",
  robots: { index: false, follow: false },
};

export default async function ApplyForLoanPage({
  searchParams,
}: {
  searchParams: Promise<{ product?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const { product } = await searchParams;
  const initialProductSlug = product && getLoanProductBySlug(product) ? product : undefined;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Apply for a loan</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Tell us a bit about what you need — you can track the status right after you submit.
        </p>
      </div>
      <LoanApplyForm initialProductSlug={initialProductSlug} />
    </div>
  );
}
