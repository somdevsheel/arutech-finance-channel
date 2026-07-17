import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ArrowRight, CheckCircle2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getLoanProductBySlug, loanProducts } from "@/content/loan-products";
import { formatInr } from "@/lib/format";

export function generateStaticParams() {
  return loanProducts.map((product) => ({ slug: product.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const product = getLoanProductBySlug(slug);
  if (!product) return {};

  return {
    title: product.name,
    description: product.description,
  };
}

export default async function LoanProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = getLoanProductBySlug(slug);
  if (!product) notFound();

  return (
    <>
      <section className="border-b bg-muted/30">
        <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {product.name}
          </h1>
          <p className="mt-3 text-lg text-muted-foreground">
            {product.tagline}
          </p>
          <p className="mt-4 max-w-2xl text-muted-foreground">
            {product.description}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button size="lg" render={<Link href={`/applications/apply?product=${product.slug}`} />}>
              Apply Now <ArrowRight className="ml-1 size-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              render={<Link href="/tools/eligibility-calculator" />}
            >
              Check Your Eligibility
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-8 sm:grid-cols-3">
          <div className="rounded-xl border p-5">
            <p className="text-sm text-muted-foreground">Interest Rate</p>
            <p className="mt-1 text-2xl font-semibold">
              {product.interestRateMin}% - {product.interestRateMax}%
            </p>
            <p className="text-xs text-muted-foreground">per annum</p>
          </div>
          <div className="rounded-xl border p-5">
            <p className="text-sm text-muted-foreground">Loan Amount</p>
            <p className="mt-1 text-2xl font-semibold">
              {formatInr(product.amountMin)}
            </p>
            <p className="text-xs text-muted-foreground">
              up to {formatInr(product.amountMax)}
            </p>
          </div>
          <div className="rounded-xl border p-5">
            <p className="text-sm text-muted-foreground">Tenure</p>
            <p className="mt-1 text-2xl font-semibold">
              {Math.round(product.tenureMinMonths / 12) || "< 1"} -{" "}
              {Math.round(product.tenureMaxMonths / 12)} yrs
            </p>
          </div>
        </div>

        <div className="mt-14 grid gap-10 sm:grid-cols-2">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <CheckCircle2 className="size-5 text-primary" /> Key Features
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
              {product.features.map((feature) => (
                <li key={feature} className="flex gap-2">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <CheckCircle2 className="size-5 text-primary" /> Eligibility
              Highlights
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
              {product.eligibilityHighlights.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-14">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <FileText className="size-5 text-primary" /> Documents Required
          </h2>
          <ul className="mt-4 grid gap-2.5 text-sm text-muted-foreground sm:grid-cols-2">
            {product.documentsRequired.map((doc) => (
              <li key={doc} className="flex gap-2">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                {doc}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-14 rounded-xl border bg-muted/30 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Rates and terms shown are indicative ranges from our partner
            lenders and are not a guarantee of approval. See our{" "}
            <Link href="/disclaimer" className="underline underline-offset-2">
              Disclaimer
            </Link>{" "}
            for details.
          </p>
          <Button className="mt-4" render={<Link href="/tools/emi-calculator" />}>
            Estimate Your EMI
          </Button>
        </div>
      </section>
    </>
  );
}
