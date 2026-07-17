import type { Metadata } from "next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatInr } from "@/lib/format";
import { getLoanProducts } from "@/lib/admin/session";
import { createLoanProductAction, setLoanProductActiveAction } from "@/lib/admin/actions";
import { ToggleActiveButton } from "@/components/admin/toggle-active-button";

export const metadata: Metadata = {
  title: "Loan Product Management",
  robots: { index: false, follow: false },
};

export default async function AdminLoanProductsPage() {
  const products = await getLoanProducts();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Loan Product Management</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The database-backed catalog {`LoanApplicationService`} validates applications against —
          interest rate, tenure, and amount bounds, plus the required-documents checklist.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Loan Product</CardTitle>
        </CardHeader>
        <CardContent>
          <form action={createLoanProductAction} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="slug">Slug</Label>
              <Input id="slug" name="slug" required placeholder="e.g. top-up-loan" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" required />
            </div>
            <div />
            <div className="space-y-1.5">
              <Label htmlFor="interest_rate_min">Interest Rate Min (%)</Label>
              <Input id="interest_rate_min" name="interest_rate_min" required inputMode="decimal" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="interest_rate_max">Interest Rate Max (%)</Label>
              <Input id="interest_rate_max" name="interest_rate_max" required inputMode="decimal" />
            </div>
            <div />
            <div className="space-y-1.5">
              <Label htmlFor="tenure_min_months">Tenure Min (months)</Label>
              <Input id="tenure_min_months" name="tenure_min_months" required inputMode="numeric" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tenure_max_months">Tenure Max (months)</Label>
              <Input id="tenure_max_months" name="tenure_max_months" required inputMode="numeric" />
            </div>
            <div />
            <div className="space-y-1.5">
              <Label htmlFor="amount_min">Amount Min</Label>
              <Input id="amount_min" name="amount_min" required inputMode="numeric" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="amount_max">Amount Max</Label>
              <Input id="amount_max" name="amount_max" required inputMode="numeric" />
            </div>
            <div />
            <div className="sm:col-span-2 lg:col-span-3 space-y-1.5">
              <Label htmlFor="documents_required">Required Documents (one per line)</Label>
              <Textarea id="documents_required" name="documents_required" rows={3} />
            </div>
            <div className="sm:col-span-2 lg:col-span-3">
              <Button type="submit">Create Product</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Products</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Rate</TableHead>
                  <TableHead>Tenure</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-medium">{product.name}</TableCell>
                    <TableCell>
                      {product.interest_rate_min}% - {product.interest_rate_max}%
                    </TableCell>
                    <TableCell>
                      {product.tenure_min_months}-{product.tenure_max_months} mo
                    </TableCell>
                    <TableCell>
                      {formatInr(product.amount_min)} - {formatInr(product.amount_max)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={product.is_active ? "secondary" : "destructive"}>
                        {product.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <ToggleActiveButton
                        id={product.id}
                        isActive={product.is_active}
                        action={setLoanProductActiveAction}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
