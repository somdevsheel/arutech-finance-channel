import Link from "next/link";
import type { Metadata } from "next";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { listPublishedBlogPosts } from "@/lib/cms/session";
import { formatDate } from "@/lib/format";

export const revalidate = 300;

export const metadata: Metadata = {
  title: "Blog",
  description:
    "Practical guidance on credit scores, loan eligibility, and borrowing smart from the Arutech editorial team.",
};

export default async function BlogIndexPage() {
  const blogPosts = await listPublishedBlogPosts();

  return (
    <section className="mx-auto max-w-5xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">Blog</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Practical guidance on credit, eligibility, and borrowing smart.
        </p>
      </div>

      <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {blogPosts.map((post) => (
          <Link key={post.slug} href={`/blog/${post.slug}`}>
            <Card className="h-full transition-colors hover:border-primary/40">
              <CardHeader>
                <p className="text-xs text-muted-foreground">
                  {post.published_at && formatDate(post.published_at)} &middot;{" "}
                  {post.reading_minutes} min read
                </p>
                <CardTitle className="mt-1 text-lg leading-snug">
                  {post.title}
                </CardTitle>
                <CardDescription className="mt-2 line-clamp-3">
                  {post.excerpt}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
