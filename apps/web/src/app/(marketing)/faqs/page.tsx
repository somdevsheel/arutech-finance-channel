import type { Metadata } from "next";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { faqs } from "@/content/faqs";
import { faqPageJsonLd } from "@/lib/structured-data";

export const metadata: Metadata = {
  title: "Frequently Asked Questions",
  description:
    "Answers to common questions about eligibility, applying, and repaying loans through Arutech Finance Platform.",
};

const categories = ["General", "Eligibility", "Application", "Repayment"] as const;

export default function FaqsPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqPageJsonLd(faqs)) }}
      />

      <section className="mx-auto max-w-3xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-semibold tracking-tight">
            Frequently Asked Questions
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">
            Can&apos;t find what you&apos;re looking for?{" "}
            <a href="/contact" className="underline underline-offset-2">
              Contact us
            </a>
            .
          </p>
        </div>

        <div className="mt-14 space-y-10">
          {categories.map((category) => {
            const items = faqs.filter((faq) => faq.category === category);
            if (items.length === 0) return null;

            return (
              <div key={category}>
                <h2 className="text-lg font-semibold">{category}</h2>
                <Accordion className="mt-3">
                  {items.map((faq) => (
                    <AccordionItem key={faq.question} value={faq.question}>
                      <AccordionTrigger>{faq.question}</AccordionTrigger>
                      <AccordionContent>
                        <p className="text-muted-foreground">{faq.answer}</p>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}
