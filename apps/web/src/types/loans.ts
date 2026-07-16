export type LoanApplicationStatus =
  | "draft"
  | "submitted"
  | "under_review"
  | "approved"
  | "rejected"
  | "sanctioned"
  | "disbursed"
  | "closed"
  | "withdrawn";

export type KycStatus = "pending" | "verified" | "rejected";
export type VerificationStatus = "pending" | "verified" | "rejected";
export type EligibilityStatus = "pending" | "eligible" | "ineligible";
export type RiskCategory = "low" | "medium" | "high";
export type CommissionStatus = "pending" | "approved" | "paid";
export type LoanDocumentStatus = "pending" | "submitted" | "verified" | "rejected";

export interface LoanApplication {
  id: string;
  customer_user_id: string;
  lead_id: string | null;
  loan_product_slug: string;
  requested_amount: number;
  tenure_months: number;
  interest_rate: string;
  monthly_income: number;
  existing_monthly_obligations: number;
  status: LoanApplicationStatus;
  kyc_status: KycStatus;
  verification_status: VerificationStatus;
  eligibility_status: EligibilityStatus;
  credit_score: number | null;
  risk_category: RiskCategory | null;
  assigned_to: string | null;
  rejection_reason: string | null;
  sanctioned_amount: number | null;
  sanctioned_tenure_months: number | null;
  sanction_date: string | null;
  disbursed_amount: number | null;
  disbursement_date: string | null;
  disbursement_reference: string | null;
  commission_amount: number | null;
  commission_status: CommissionStatus | null;
  closure_date: string | null;
  closure_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LoanDocument {
  id: string;
  application_id: string;
  document_type: string;
  status: LoanDocumentStatus;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}
