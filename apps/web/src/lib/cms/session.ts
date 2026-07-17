import { apiFetch, ApiError } from "@/lib/api-client";
import type { BlogPost } from "@/types/admin";

// Public, unauthenticated reads of published content — no access token
// involved, unlike lib/admin/session.ts. Backs the marketing site's
// /blog pages, which moved off the static content/blog-posts.ts file in
// Phase 9 (see docs/phase-9-architecture.md).

export async function listPublishedBlogPosts(): Promise<BlogPost[]> {
  return apiFetch<BlogPost[]>("/api/v1/public/blog-posts");
}

export async function getPublishedBlogPost(slug: string): Promise<BlogPost | null> {
  try {
    return await apiFetch<BlogPost>(`/api/v1/public/blog-posts/${slug}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
