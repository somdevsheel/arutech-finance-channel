"use server";

import { apiFetch, ApiError } from "@/lib/api-client";
import { getAccessTokenOrThrow } from "@/lib/auth/session";
import type { ActionResult } from "@/lib/auth/actions";
import { loanApplicationSchema } from "@/lib/loans/schemas";
import type { LoanApplication, LoanDocument } from "@/types/loans";

function fail(error: unknown): { ok: false; error: string } {
  const message = error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
  return { ok: false, error: message };
}

/**
 * Creates a DRAFT application and immediately submits it — the two-step
 * create/submit distinction the API supports (so a future "save as
 * draft" feature has somewhere to plug in) is collapsed into one action
 * here, since a lingering draft state has no UX value yet: applying is a
 * single form, one submit, one result, like the rest of this portal.
 */
export async function applyForLoanAction(
  input: unknown,
): Promise<ActionResult<{ application: LoanApplication }>> {
  const parsed = loanApplicationSchema.safeParse(input);
  if (!parsed.success) return { ok: false, error: "Check the highlighted fields and try again." };

  try {
    const accessToken = await getAccessTokenOrThrow();
    const headers = { Authorization: `Bearer ${accessToken}` };

    const created = await apiFetch<LoanApplication>("/api/v1/loan-applications", {
      method: "POST",
      body: parsed.data,
      headers,
    });
    const submitted = await apiFetch<LoanApplication>(
      `/api/v1/loan-applications/mine/${created.id}/submit`,
      { method: "POST", headers },
    );
    return { ok: true, data: { application: submitted } };
  } catch (error) {
    return fail(error);
  }
}

export async function withdrawApplicationAction(applicationId: string): Promise<ActionResult> {
  try {
    const accessToken = await getAccessTokenOrThrow();
    await apiFetch(`/api/v1/loan-applications/mine/${applicationId}/withdraw`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return { ok: true, data: undefined };
  } catch (error) {
    return fail(error);
  }
}

export async function submitDocumentAction(
  applicationId: string,
  documentId: string,
): Promise<ActionResult<{ document: LoanDocument }>> {
  try {
    const accessToken = await getAccessTokenOrThrow();
    const document = await apiFetch<LoanDocument>(
      `/api/v1/loan-applications/mine/${applicationId}/documents/${documentId}/submit`,
      { method: "POST", headers: { Authorization: `Bearer ${accessToken}` } },
    );
    return { ok: true, data: { document } };
  } catch (error) {
    return fail(error);
  }
}
