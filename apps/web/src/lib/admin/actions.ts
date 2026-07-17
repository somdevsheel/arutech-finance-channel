"use server";

import { revalidatePath } from "next/cache";
import { apiFetch, ApiError } from "@/lib/api-client";
import { getAccessTokenOrThrow } from "@/lib/auth/session";
import type { ActionResult } from "@/lib/auth/actions";

// Admin CRUD forms in this phase are plain <form action={...}> bindings,
// not react-hook-form + zod like the customer-facing loan apply form —
// internal admin tooling doesn't carry the same UX bar as a public
// conversion flow, and FormData is enough validation surface once the
// backend re-validates everything anyway (every field below is checked
// again by the service layer). See docs/phase-9-architecture.md.

function fail(error: unknown): { ok: false; error: string } {
  const message =
    error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
  return { ok: false, error: message };
}

async function authedFetch<T>(
  path: string,
  options: { method: string; body?: unknown } = { method: "GET" },
): Promise<T> {
  const accessToken = await getAccessTokenOrThrow();
  return apiFetch<T>(path, {
    method: options.method,
    body: options.body,
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

function str(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

// --- User management -------------------------------------------------

export async function setUserActiveAction(
  userId: string,
  isActive: boolean,
): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/users/${userId}/${isActive ? "activate" : "deactivate"}`, {
      method: "POST",
    });
    revalidatePath("/admin/users");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function setUserRoleAction(userId: string, formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/users/${userId}/role`, {
      method: "POST",
      body: { role: str(formData, "role") },
    });
    revalidatePath("/admin/users");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- Role management ---------------------------------------------------

export async function createRoleAction(formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch("/api/v1/admin/roles", {
      method: "POST",
      body: { name: str(formData, "name"), description: str(formData, "description") },
    });
    revalidatePath("/admin/roles");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function deleteRoleAction(roleId: string): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/roles/${roleId}`, { method: "DELETE" });
    revalidatePath("/admin/roles");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function grantPermissionAction(
  roleId: string,
  formData: FormData,
): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/roles/${roleId}/permissions`, {
      method: "POST",
      body: { permission_code: str(formData, "permission_code") },
    });
    revalidatePath(`/admin/roles/${roleId}`);
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function revokePermissionAction(
  roleId: string,
  permissionCode: string,
): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/roles/${roleId}/permissions/${permissionCode}`, {
      method: "DELETE",
    });
    revalidatePath(`/admin/roles/${roleId}`);
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- Lenders -------------------------------------------------------------

export async function createLenderAction(formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch("/api/v1/lenders", {
      method: "POST",
      body: {
        name: str(formData, "name"),
        type: str(formData, "type"),
        code: str(formData, "code"),
        contact_email: str(formData, "contact_email") || null,
        contact_phone: str(formData, "contact_phone") || null,
        commission_rate_percent: str(formData, "commission_rate_percent") || "1",
      },
    });
    revalidatePath("/admin/lenders");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function setLenderActiveAction(
  lenderId: string,
  isActive: boolean,
): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/lenders/${lenderId}/${isActive ? "activate" : "deactivate"}`, {
      method: "POST",
    });
    revalidatePath("/admin/lenders");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- Loan products ---------------------------------------------------------

export async function createLoanProductAction(formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch("/api/v1/loan-products", {
      method: "POST",
      body: {
        slug: str(formData, "slug"),
        name: str(formData, "name"),
        interest_rate_min: str(formData, "interest_rate_min"),
        interest_rate_max: str(formData, "interest_rate_max"),
        tenure_min_months: Number(str(formData, "tenure_min_months")),
        tenure_max_months: Number(str(formData, "tenure_max_months")),
        amount_min: Number(str(formData, "amount_min")),
        amount_max: Number(str(formData, "amount_max")),
        documents_required: str(formData, "documents_required")
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean),
      },
    });
    revalidatePath("/admin/loan-products");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function setLoanProductActiveAction(
  productId: string,
  isActive: boolean,
): Promise<ActionResult> {
  try {
    await authedFetch(
      `/api/v1/loan-products/${productId}/${isActive ? "activate" : "deactivate"}`,
      { method: "POST" },
    );
    revalidatePath("/admin/loan-products");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- Notification templates -----------------------------------------------

export async function createNotificationTemplateAction(formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch("/api/v1/notification-templates", {
      method: "POST",
      body: {
        code: str(formData, "code"),
        channel: str(formData, "channel"),
        subject: str(formData, "subject") || null,
        body: str(formData, "body"),
      },
    });
    revalidatePath("/admin/notification-templates");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function setNotificationTemplateActiveAction(
  templateId: string,
  isActive: boolean,
): Promise<ActionResult> {
  try {
    await authedFetch(
      `/api/v1/notification-templates/${templateId}/${isActive ? "activate" : "deactivate"}`,
      { method: "POST" },
    );
    revalidatePath("/admin/notification-templates");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- CMS blog posts ----------------------------------------------------

export async function createBlogPostAction(formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch("/api/v1/cms/blog-posts", {
      method: "POST",
      body: {
        slug: str(formData, "slug"),
        title: str(formData, "title"),
        excerpt: str(formData, "excerpt"),
        author: str(formData, "author"),
        reading_minutes: Number(str(formData, "reading_minutes") || "1"),
        sections: [{ heading: null, paragraphs: [str(formData, "body")] }],
        tags: str(formData, "tags")
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      },
    });
    revalidatePath("/admin/cms/blog-posts");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function setBlogPostPublishedAction(
  postId: string,
  isPublished: boolean,
): Promise<ActionResult> {
  try {
    await authedFetch(
      `/api/v1/cms/blog-posts/${postId}/${isPublished ? "publish" : "unpublish"}`,
      { method: "POST" },
    );
    revalidatePath("/admin/cms/blog-posts");
    revalidatePath("/blog");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function deleteBlogPostAction(postId: string): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/cms/blog-posts/${postId}`, { method: "DELETE" });
    revalidatePath("/admin/cms/blog-posts");
    revalidatePath("/blog");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

// --- Settings --------------------------------------------------------------

export async function updateSettingAction(key: string, formData: FormData): Promise<ActionResult> {
  try {
    await authedFetch(`/api/v1/admin/settings/${key}`, {
      method: "PUT",
      body: { value: str(formData, "value") },
    });
    revalidatePath("/admin/settings");
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}
