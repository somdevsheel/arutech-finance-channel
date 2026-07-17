import type { MetadataRoute } from "next";
import { listPublishedBlogPosts } from "@/lib/cms/session";
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

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticEntries: MetadataRoute.Sitemap = staticRoutes.map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: new Date(),
  }));

  const loanEntries: MetadataRoute.Sitemap = loanProducts.map((product) => ({
    url: `${siteUrl}/loans/${product.slug}`,
    lastModified: new Date(),
  }));

  const blogPosts = await listPublishedBlogPosts();
  const blogEntries: MetadataRoute.Sitemap = blogPosts.map((post) => ({
    url: `${siteUrl}/blog/${post.slug}`,
    lastModified: post.published_at ? new Date(post.published_at) : new Date(),
  }));

  return [...staticEntries, ...loanEntries, ...blogEntries];
}
