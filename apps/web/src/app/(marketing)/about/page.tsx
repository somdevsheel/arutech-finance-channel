import type { Metadata } from "next";
import { Handshake, Scale, ShieldCheck, Sparkles } from "lucide-react";
import { SectionHeading } from "@/components/marketing/section-heading";

export const metadata: Metadata = {
  title: "About Us",
  description:
    "Arutech Finance Platform is a loan services platform connecting borrowers with partner banks and NBFCs across India.",
};

const values = [
  {
    icon: Scale,
    title: "Transparency first",
    description:
      "Every rate, fee, and term is disclosed before you accept an offer — no fine print surprises after disbursal.",
  },
  {
    icon: Handshake,
    title: "Partner, not just a platform",
    description:
      "We work with our lending partners on approval quality, not just volume, so the matches we make are ones both sides want.",
  },
  {
    icon: ShieldCheck,
    title: "Data handled responsibly",
    description:
      "Your financial information is shared only with the lenders you choose to apply to, and never sold to third parties.",
  },
  {
    icon: Sparkles,
    title: "Built for the whole journey",
    description:
      "From your first eligibility check to post-disbursal support, we stay involved rather than handing you off after approval.",
  },
];

export default function AboutPage() {
  return (
    <>
      <section className="border-b bg-muted/30">
        <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            Making borrowing feel less like paperwork
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            Arutech Finance Platform exists to close the gap between what
            borrowers need and what banks and NBFCs can actually offer them —
            without a dozen branch visits in between.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="max-w-none">
          <h2 className="text-2xl font-semibold tracking-tight">Our story</h2>
          <p className="mt-4 text-muted-foreground">
            Getting a loan in India often means visiting multiple bank
            branches, filling out the same form five times, and waiting weeks
            to hear back — only to find out you didn&apos;t qualify for the
            rate you were quoted. Arutech was built to fix that: a single
            place to check what you actually qualify for, compare real offers
            from multiple lenders, and track your application without
            chasing anyone for updates.
          </p>
          <p className="mt-4 text-muted-foreground">
            We work as a Direct Selling Agent (DSA) for our partner banks and
            NBFCs — we don&apos;t lend money ourselves, but we do the work of
            matching your application to lenders likely to approve it,
            reviewing your documentation before it&apos;s submitted, and keeping
            you informed at every stage. See our{" "}
            <a href="/disclaimer" className="underline underline-offset-2">
              Disclaimer
            </a>{" "}
            for more on how that relationship works.
          </p>
        </div>
      </section>

      <section className="border-t bg-muted/30">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="What we stand for"
            title="The principles behind how we operate"
          />
          <div className="mt-14 grid gap-8 sm:grid-cols-2">
            {values.map(({ icon: Icon, title, description }) => (
              <div key={title} className="flex gap-4">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="size-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
