import { z } from "zod";

// Deliberately loose bounds here (just "positive") rather than duplicating
// domain/loans/products.py's per-product min/max a third time (frontend
// content + backend catalog is already the accepted duplication — see
// docs/phase-7-architecture.md). The backend validates against the real
// per-product bounds and returns a specific error message on submit.
export const loanApplicationSchema = z.object({
  loan_product_slug: z.string().min(1, "Choose a loan product"),
  requested_amount: z.coerce.number().int().positive("Enter the amount you'd like to borrow"),
  tenure_months: z.coerce.number().int().positive("Enter a tenure in months"),
  monthly_income: z.coerce.number().int().positive("Enter your net monthly income"),
  existing_monthly_obligations: z.coerce.number().int().min(0).optional().default(0),
});

export type LoanApplicationInput = z.infer<typeof loanApplicationSchema>;
