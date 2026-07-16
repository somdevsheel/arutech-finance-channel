import { clientEnv } from "@/lib/env";

const siteUrl = clientEnv.NEXT_PUBLIC_SITE_URL;

export const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Arutech Finance Platform",
  url: siteUrl,
  description:
    "A loan services platform connecting borrowers with partner banks and NBFCs across India.",
};

export function faqPageJsonLd(faqs: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };
}

export function articleJsonLd(article: {
  title: string;
  description: string;
  datePublished: string;
  author: string;
  slug: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    datePublished: article.datePublished,
    author: { "@type": "Organization", name: article.author },
    url: `${siteUrl}/blog/${article.slug}`,
  };
}
