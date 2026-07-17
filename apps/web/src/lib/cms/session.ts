import { apiFetch, ApiError } from "@/lib/api-client";
import type { BlogPost } from "@/types/admin";

// Public, unauthenticated reads of published content — no access token
// involved, unlike lib/admin/session.ts. Backs the marketing site's
// /blog pages, which moved off the static content/blog-posts.ts file in
// Phase 9 (see docs/phase-9-architecture.md).

export async function listPublishedBlogPosts(): Promise<BlogPost[]> {
  // Absorbs failures (including build-time "API unreachable", e.g. a CI
  // stage that builds the web image before the API is up — see
  // docs/phase-9-architecture.md) into an empty list rather than
  // crashing the page/build. A public listing quietly showing zero
  // posts is a safer degradation than a 500 for site visitors;
  // getPublishedBlogPost (a specific slug) doesn't do this same
  // blanket catch, since silently turning "API down" into "post not
  // found" would be actively misleading.
  try {
    return await apiFetch<BlogPost[]>("/api/v1/public/blog-posts");
  } catch {
    return [];
  }
}

export async function getPublishedBlogPost(slug: string): Promise<BlogPost | null> {
  try {
    return await apiFetch<BlogPost>(`/api/v1/public/blog-posts/${slug}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
