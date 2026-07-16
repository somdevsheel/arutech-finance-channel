import Link from "next/link";
import type { Metadata } from "next";
import { EligibilityCalculatorForm } from "@/components/marketing/eligibility-calculator-form";

export const metadata: Metadata = {
  title: "Loan Eligibility Calculator",
  description:
    "Get an instant estimate of how much you may be able to borrow, based on your income and existing obligations.",
};

export default function EligibilityCalculatorPage() {
  return (
    <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">
          Eligibility Calculator
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          See an instant estimate of what you may qualify for — no credit
          inquiry involved.
        </p>
      </div>

      <div className="mt-12">
        <EligibilityCalculatorForm />
      </div>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        This is a pre-qualification estimate only, not a credit decision or
        offer of credit. Your actual eligibility depends on your chosen
        lender&apos;s full underwriting assessment — see our{" "}
        <Link href="/disclaimer" className="underline underline-offset-2">
          Disclaimer
        </Link>
        .
      </p>
    </section>
  );
}
