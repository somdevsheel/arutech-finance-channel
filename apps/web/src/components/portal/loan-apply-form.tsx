"use client";

import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { loanProducts, getLoanProductBySlug } from "@/content/loan-products";
import { formatInr } from "@/lib/format";
import { applyForLoanAction } from "@/lib/loans/actions";

const applyFormSchema = z.object({
  loan_product_slug: z.string().min(1, "Choose a loan product"),
  requested_amount: z.coerce.number().int().positive(),
  tenure_months: z.coerce.number().int().positive(),
  monthly_income: z.coerce.number().int().positive(),
  existing_monthly_obligations: z.coerce.number().int().min(0),
});

type ApplyFormInput = z.input<typeof applyFormSchema>;
type ApplyFormOutput = z.output<typeof applyFormSchema>;

export function LoanApplyForm({ initialProductSlug }: { initialProductSlug?: string }) {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ApplyFormInput, unknown, ApplyFormOutput>({
    resolver: zodResolver(applyFormSchema),
    defaultValues: {
      loan_product_slug: initialProductSlug ?? "personal-loan",
      requested_amount: 200_000,
      tenure_months: 24,
      monthly_income: 50_000,
      existing_monthly_obligations: 0,
    },
  });

  const selectedSlug = watch("loan_product_slug");
  const product = getLoanProductBySlug(selectedSlug);

  async function onSubmit(values: ApplyFormOutput) {
    const result = await applyForLoanAction(values);
    if (!result.ok) {
      toast.error(result.error);
      return;
    }
    toast.success(
      result.data.application.eligibility_status === "eligible"
        ? "Application submitted — you look eligible based on what you shared."
        : "Application submitted — our team will follow up on eligibility.",
    );
    router.push(`/applications/${result.data.application.id}`);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Application details</CardTitle>
        <CardDescription>
          Rates and limits vary by product; we&apos;ll validate against the exact range for
          the one you choose.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="loan_product_slug">Loan type</Label>
            <Select
              value={selectedSlug}
              onValueChange={(value) => {
                if (value) setValue("loan_product_slug", value);
              }}
            >
              <SelectTrigger id="loan_product_slug" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {loanProducts.map((p) => (
                  <SelectItem key={p.slug} value={p.slug}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {product && (
              <p className="text-xs text-muted-foreground">
                {formatInr(product.amountMin)} – {formatInr(product.amountMax)} ·{" "}
                {product.interestRateMin}%–{product.interestRateMax}% p.a. ·{" "}
                {Math.round(product.tenureMinMonths / 12) || "< 1"}–
                {Math.round(product.tenureMaxMonths / 12)} yrs
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="requested_amount">Amount you&apos;d like to borrow (₹)</Label>
            <Input
              id="requested_amount"
              type="number"
              step="1000"
              {...register("requested_amount")}
            />
            {errors.requested_amount && (
              <p className="text-xs text-destructive">Enter a positive amount.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tenure_months">Tenure (months)</Label>
            <Input id="tenure_months" type="number" step="1" {...register("tenure_months")} />
            {errors.tenure_months && (
              <p className="text-xs text-destructive">Enter a tenure in months.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="monthly_income">Net monthly income (₹)</Label>
            <Input
              id="monthly_income"
              type="number"
              step="1000"
              {...register("monthly_income")}
            />
            {errors.monthly_income && (
              <p className="text-xs text-destructive">Enter your net monthly income.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="existing_monthly_obligations">
              Existing monthly EMIs / obligations (₹)
            </Label>
            <Input
              id="existing_monthly_obligations"
              type="number"
              step="500"
              {...register("existing_monthly_obligations")}
            />
            {errors.existing_monthly_obligations && (
              <p className="text-xs text-destructive">Enter 0 or a positive amount.</p>
            )}
          </div>

          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting ? "Submitting..." : "Submit application"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
