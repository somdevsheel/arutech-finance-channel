"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmiBreakdownBar } from "@/components/marketing/emi-breakdown-bar";
import { calculateEmi } from "@/lib/loan-calculations";
import { formatInr } from "@/lib/format";

const emiFormSchema = z.object({
  loanAmount: z.coerce.number().min(10_000).max(100_000_000),
  interestRate: z.coerce.number().min(0).max(50),
  tenureYears: z.coerce.number().min(1).max(30),
});

// `z.coerce.number()` accepts raw (pre-coercion) input distinct from its
// parsed output, so useForm needs both generics — otherwise its inferred
// field-value type conflicts with what the resolver actually produces.
type EmiFormInput = z.input<typeof emiFormSchema>;
type EmiFormOutput = z.output<typeof emiFormSchema>;

const defaultValues: EmiFormInput = {
  loanAmount: 1_000_000,
  interestRate: 10.5,
  tenureYears: 5,
};

export function EmiCalculatorForm() {
  const {
    register,
    watch,
    formState: { errors },
  } = useForm<EmiFormInput, unknown, EmiFormOutput>({
    resolver: zodResolver(emiFormSchema),
    defaultValues,
    mode: "onChange",
  });

  const values = watch();
  const parsed = emiFormSchema.safeParse(values);
  const result = parsed.success
    ? calculateEmi(parsed.data.loanAmount, parsed.data.interestRate, parsed.data.tenureYears * 12)
    : null;

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Loan details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="loanAmount">Loan amount (₹)</Label>
            <Input
              id="loanAmount"
              type="number"
              step="1000"
              {...register("loanAmount")}
            />
            {errors.loanAmount && (
              <p className="text-xs text-destructive">
                Enter an amount between ₹10,000 and ₹10,00,00,000.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="interestRate">Interest rate (% p.a.)</Label>
            <Input
              id="interestRate"
              type="number"
              step="0.1"
              {...register("interestRate")}
            />
            {errors.interestRate && (
              <p className="text-xs text-destructive">
                Enter a rate between 0% and 50%.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tenureYears">Tenure (years)</Label>
            <Input
              id="tenureYears"
              type="number"
              step="1"
              {...register("tenureYears")}
            />
            {errors.tenureYears && (
              <p className="text-xs text-destructive">
                Enter a tenure between 1 and 30 years.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your estimated EMI</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {result ? (
            <>
              <div>
                <p className="text-sm text-muted-foreground">Monthly EMI</p>
                <p className="text-4xl font-semibold tracking-tight">
                  {formatInr(Math.round(result.emi))}
                </p>
              </div>
              <EmiBreakdownBar
                principal={parsed.success ? parsed.data.loanAmount : 0}
                totalInterest={result.totalInterest}
              />
              <div className="grid grid-cols-2 gap-4 border-t pt-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Total interest</p>
                  <p className="font-medium">
                    {formatInr(Math.round(result.totalInterest))}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Total payment</p>
                  <p className="font-medium">
                    {formatInr(Math.round(result.totalPayment))}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Enter valid loan details to see your EMI estimate.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
