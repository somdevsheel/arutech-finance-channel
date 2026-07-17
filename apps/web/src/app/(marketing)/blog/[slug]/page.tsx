import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getPublishedBlogPost, listPublishedBlogPosts } from "@/lib/cms/session";
import { formatDate } from "@/lib/format";
import { articleJsonLd } from "@/lib/structured-data";

export const revalidate = 300;

export async function generateStaticParams() {
  const posts = await listPublishedBlogPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPublishedBlogPost(slug);
  if (!post) return {};

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: "article",
      publishedTime: post.published_at ?? undefined,
    },
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPublishedBlogPost(slug);
  if (!post) notFound();

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(
            articleJsonLd({
              title: post.title,
              description: post.excerpt,
              datePublished: post.published_at ?? "",
              author: post.author,
              slug: post.slug,
            }),
          ),
        }}
      />

      <article className="mx-auto max-w-2xl px-4 py-20 sm:px-6 lg:px-8">
        <p className="text-sm text-muted-foreground">
          {post.published_at && formatDate(post.published_at)} &middot; {post.reading_minutes} min
          read &middot; {post.author}
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          {post.title}
        </h1>
        <div className="mt-3 flex flex-wrap gap-2">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="mt-10 space-y-8">
          {post.sections.map((section, index) => (
            <div key={section.heading ?? index}>
              {section.heading && (
                <h2 className="text-xl font-semibold tracking-tight">
                  {section.heading}
                </h2>
              )}
              <div className="mt-3 space-y-4 text-muted-foreground">
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}
