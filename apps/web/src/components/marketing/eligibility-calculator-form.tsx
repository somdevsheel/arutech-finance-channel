"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { loanProducts } from "@/content/loan-products";
import { calculateEligibility } from "@/lib/loan-calculations";
import { formatInr } from "@/lib/format";

const eligibilityFormSchema = z.object({
  netMonthlyIncome: z.coerce.number().min(5_000).max(10_000_000),
  existingMonthlyObligations: z.coerce.number().min(0).max(10_000_000),
  loanProductSlug: z.string(),
  tenureYears: z.coerce.number().min(1).max(30),
});

// `z.coerce.number()` accepts raw (pre-coercion) input distinct from its
// parsed output, so useForm needs both generics — otherwise its inferred
// field-value type conflicts with what the resolver actually produces.
type EligibilityFormInput = z.input<typeof eligibilityFormSchema>;
type EligibilityFormOutput = z.output<typeof eligibilityFormSchema>;

const defaultValues: EligibilityFormInput = {
  netMonthlyIncome: 75_000,
  existingMonthlyObligations: 5_000,
  loanProductSlug: "personal-loan",
  tenureYears: 5,
};

export function EligibilityCalculatorForm() {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = useForm<EligibilityFormInput, unknown, EligibilityFormOutput>({
    resolver: zodResolver(eligibilityFormSchema),
    defaultValues,
    mode: "onChange",
  });

  const values = watch();
  const parsed = eligibilityFormSchema.safeParse(values);
  const selectedProduct = loanProducts.find(
    (product) => product.slug === values.loanProductSlug,
  );
  const assumedRate = selectedProduct
    ? (selectedProduct.interestRateMin + selectedProduct.interestRateMax) / 2
    : 12;

  const result = parsed.success
    ? calculateEligibility({
        netMonthlyIncome: parsed.data.netMonthlyIncome,
        existingMonthlyObligations: parsed.data.existingMonthlyObligations,
        annualRatePercent: assumedRate,
        tenureMonths: parsed.data.tenureYears * 12,
      })
    : null;

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your financial details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5">
            <Label htmlFor="netMonthlyIncome">Net monthly income (₹)</Label>
            <Input
              id="netMonthlyIncome"
              type="number"
              step="1000"
              {...register("netMonthlyIncome")}
            />
            {errors.netMonthlyIncome && (
              <p className="text-xs text-destructive">
                Enter an income between ₹5,000 and ₹1,00,00,000.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="existingMonthlyObligations">
              Existing monthly EMIs / obligations (₹)
            </Label>
            <Input
              id="existingMonthlyObligations"
              type="number"
              step="500"
              {...register("existingMonthlyObligations")}
            />
            {errors.existingMonthlyObligations && (
              <p className="text-xs text-destructive">Enter 0 or a positive amount.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="loanProductSlug">Loan type</Label>
            <Select
              value={values.loanProductSlug}
              onValueChange={(value) => {
                if (value) setValue("loanProductSlug", value);
              }}
            >
              <SelectTrigger id="loanProductSlug" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {loanProducts.map((product) => (
                  <SelectItem key={product.slug} value={product.slug}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tenureYears">Desired tenure (years)</Label>
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
          <CardTitle className="text-base">Your estimated eligibility</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {result ? (
            <>
              <div>
                <p className="text-sm text-muted-foreground">
                  Estimated maximum loan amount
                </p>
                <p className="text-4xl font-semibold tracking-tight">
                  {formatInr(Math.round(result.maxLoanAmount))}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4 border-t pt-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Max affordable EMI</p>
                  <p className="font-medium">
                    {formatInr(Math.round(result.maxAffordableEmi))}/mo
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Assumed rate</p>
                  <p className="font-medium">{assumedRate.toFixed(1)}% p.a.</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Based on lenders typically allowing up to {result.foirPercent}%
                of net income toward all EMIs combined (FOIR).
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Enter valid financial details to see your eligibility estimate.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
