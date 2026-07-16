import Link from "next/link";
import type { Metadata } from "next";
import { EmiCalculatorForm } from "@/components/marketing/emi-calculator-form";

export const metadata: Metadata = {
  title: "EMI Calculator",
  description:
    "Estimate your monthly loan EMI, total interest, and total payment for any loan amount, interest rate, and tenure.",
};

export default function EmiCalculatorPage() {
  return (
    <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">
          EMI Calculator
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Estimate your monthly installment before you apply.
        </p>
      </div>

      <div className="mt-12">
        <EmiCalculatorForm />
      </div>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        This is an illustrative estimate using standard EMI formulas, not a
        loan offer. Actual EMI depends on the final rate and terms your
        lender approves — see our{" "}
        <Link href="/disclaimer" className="underline underline-offset-2">
          Disclaimer
        </Link>
        .
      </p>
    </section>
  );
}
