import type { MetadataRoute } from "next";
import { blogPosts } from "@/content/blog-posts";
import { clientEnv } from "@/lib/env";
import { loanProducts } from "@/content/loan-products";

const siteUrl = clientEnv.NEXT_PUBLIC_SITE_URL;

const staticRoutes = [
  "",
  "/about",
  "/careers",
  "/contact",
  "/faqs",
  "/privacy-policy",
  "/terms",
  "/disclaimer",
  "/loans",
  "/blog",
  "/tools/emi-calculator",
  "/tools/eligibility-calculator",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const staticEntries: MetadataRoute.Sitemap = staticRoutes.map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: new Date(),
  }));

  const loanEntries: MetadataRoute.Sitemap = loanProducts.map((product) => ({
    url: `${siteUrl}/loans/${product.slug}`,
    lastModified: new Date(),
  }));

  const blogEntries: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: `${siteUrl}/blog/${post.slug}`,
    lastModified: new Date(post.publishedAt),
  }));

  return [...staticEntries, ...loanEntries, ...blogEntries];
}
