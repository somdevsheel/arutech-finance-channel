import Link from "next/link";
import type { Metadata } from "next";
import {
  ArrowRight,
  Banknote,
  Calculator,
  Clock,
  FileCheck,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SectionHeading } from "@/components/marketing/section-heading";
import { loanProducts } from "@/content/loan-products";
import { organizationJsonLd } from "@/lib/structured-data";

export const metadata: Metadata = {
  title: "Compare & Apply for Loans from Top Banks & NBFCs",
  description:
    "Arutech Finance Platform helps you compare personal, home, business, and other loan offers from partner banks and NBFCs, and apply in minutes.",
};

const valueProps = [
  {
    icon: Users,
    title: "Multiple lenders, one application",
    description:
      "Compare offers from partner banks and NBFCs side by side instead of applying separately to each one.",
  },
  {
    icon: Clock,
    title: "Fast, paperless process",
    description:
      "Upload documents digitally and get decisions in as little as 24-48 hours for eligible applications.",
  },
  {
    icon: Banknote,
    title: "Free to compare and apply",
    description:
      "We never charge borrowers to compare offers or submit an application. Lender fees are always disclosed upfront.",
  },
  {
    icon: ShieldCheck,
    title: "Bank-grade security",
    description:
      "Your data is encrypted in transit and at rest, and only ever shared with the lenders you choose to apply to.",
  },
];

const steps = [
  {
    step: "1",
    title: "Check your eligibility",
    description:
      "Use our free Eligibility Calculator to get an instant estimate before you apply — no credit inquiry involved.",
  },
  {
    step: "2",
    title: "Submit one application",
    description:
      "Tell us what you need once. We match you to the partner banks and NBFCs most likely to approve it.",
  },
  {
    step: "3",
    title: "Compare real offers",
    description:
      "Review sanction terms side by side — interest rate, tenure, and fees — before accepting one.",
  },
  {
    step: "4",
    title: "Get funded",
    description:
      "Complete verification with your chosen lender and receive disbursal directly to your account.",
  },
];

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
      />

      <section className="border-b bg-gradient-to-b from-muted/40 to-background">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
              The easiest way to compare and apply for a loan
            </h1>
            <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
              Arutech connects you with partner banks and NBFCs for personal,
              home, business, and other loans — one application, multiple
              offers, no branch visits required.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" render={<Link href="/loans" />}>
                Explore Loan Products <ArrowRight className="ml-1 size-4" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                render={<Link href="/tools/eligibility-calculator" />}
              >
                <Calculator className="mr-1 size-4" />
                Check Your Eligibility
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Why Arutech"
          title="Built to make borrowing less painful"
          description="We handle the comparison shopping and paperwork friction so you can focus on choosing the right offer."
        />
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {valueProps.map(({ icon: Icon, title, description }) => (
            <Card key={title} className="border-muted-foreground/10">
              <CardHeader>
                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="size-5 text-primary" />
                </div>
                <CardTitle className="mt-3 text-base">{title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-y bg-muted/30">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="How it works"
            title="From application to disbursal in four steps"
          />
          <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map(({ step, title, description }) => (
              <div key={step} className="relative">
                <span className="text-4xl font-bold text-primary/20">
                  {step}
                </span>
                <h3 className="mt-2 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Loan Products"
          title="Financing for whatever comes next"
          description="Seven loan products, matched across our partner network of banks and NBFCs."
        />
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {loanProducts.slice(0, 6).map((product) => (
            <Card key={product.slug} className="flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-base">{product.name}</CardTitle>
                <CardDescription>{product.tagline}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {product.interestRateMin}% - {product.interestRateMax}% p.a.
                </p>
                <Button
                  variant="link"
                  className="mt-2 h-auto p-0"
                  render={<Link href={`/loans/${product.slug}`} />}
                >
                  Learn more <ArrowRight className="ml-1 size-3.5" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mt-10 text-center">
          <Button variant="outline" render={<Link href="/loans" />}>
            View all loan products <ArrowRight className="ml-1 size-4" />
          </Button>
        </div>
      </section>

      <section className="border-t bg-primary text-primary-foreground">
        <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <FileCheck className="mx-auto size-10" />
          <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Ready to see what you qualify for?
          </h2>
          <p className="mt-4 text-lg text-primary-foreground/80">
            It takes less than five minutes, and checking your eligibility
            estimate never affects your credit score.
          </p>
          <Button
            size="lg"
            variant="secondary"
            className="mt-8"
            render={<Link href="/tools/eligibility-calculator" />}
          >
            Check Eligibility Now <ArrowRight className="ml-1 size-4" />
          </Button>
        </div>
      </section>
    </>
  );
}
