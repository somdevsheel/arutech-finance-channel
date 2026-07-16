import { apiFetch, ApiError } from "@/lib/api-client";
import { getAccessToken } from "@/lib/auth/session";
import type { LoanApplication, LoanDocument } from "@/types/loans";

// Same read-only-by-design rationale as lib/auth/session.ts: Server
// Components can't set cookies, and proxy.ts already guarantees a fresh
// access token before any portal route (including these reads) runs.

export async function getOwnLoanApplications(): Promise<LoanApplication[]> {
  const accessToken = await getAccessToken();
  if (!accessToken) return [];

  try {
    return await apiFetch<LoanApplication[]>("/api/v1/loan-applications/mine", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return [];
    throw error;
  }
}

export async function getOwnLoanApplication(
  applicationId: string,
): Promise<LoanApplication | null> {
  const accessToken = await getAccessToken();
  if (!accessToken) return null;

  try {
    return await apiFetch<LoanApplication>(
      `/api/v1/loan-applications/mine/${applicationId}`,
      { headers: { Authorization: `Bearer ${accessToken}` } },
    );
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 404)) return null;
    throw error;
  }
}

export async function getOwnLoanDocuments(applicationId: string): Promise<LoanDocument[]> {
  const accessToken = await getAccessToken();
  if (!accessToken) return [];

  try {
    return await apiFetch<LoanDocument[]>(
      `/api/v1/loan-applications/mine/${applicationId}/documents`,
      { headers: { Authorization: `Bearer ${accessToken}` } },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return [];
    throw error;
  }
}
