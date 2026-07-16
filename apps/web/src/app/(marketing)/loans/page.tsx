import Link from "next/link";
import type { Metadata } from "next";
import { ArrowRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { loanProducts } from "@/content/loan-products";
import { formatInr } from "@/lib/format";

export const metadata: Metadata = {
  title: "Loan Products",
  description:
    "Compare personal, home, business, and other loan products from Arutech's partner banks and NBFCs.",
};

export default function LoanProductsPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">
          Loan Products
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Compare rates and terms across our partner network of banks and
          NBFCs.
        </p>
      </div>

      <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {loanProducts.map((product) => (
          <Card key={product.slug} className="flex flex-col justify-between">
            <CardHeader>
              <CardTitle>{product.name}</CardTitle>
              <CardDescription>{product.tagline}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col justify-between gap-4">
              <dl className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Interest rate</dt>
                  <dd className="font-medium">
                    {product.interestRateMin}% - {product.interestRateMax}% p.a.
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Amount</dt>
                  <dd className="font-medium">
                    {formatInr(product.amountMin)} - {formatInr(product.amountMax)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Tenure</dt>
                  <dd className="font-medium">
                    up to {Math.round(product.tenureMaxMonths / 12)} years
                  </dd>
                </div>
              </dl>
              <Button
                variant="outline"
                render={<Link href={`/loans/${product.slug}`} />}
              >
                View details <ArrowRight className="ml-1 size-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
