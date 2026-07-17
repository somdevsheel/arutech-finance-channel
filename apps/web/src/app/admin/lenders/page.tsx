import type { Metadata } from "next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getLenders } from "@/lib/admin/session";
import { createLenderAction, setLenderActiveAction } from "@/lib/admin/actions";
import { AdminCreateForm } from "@/components/admin/admin-create-form";
import { ToggleActiveButton } from "@/components/admin/toggle-active-button";

export const metadata: Metadata = {
  title: "Lender Management",
  robots: { index: false, follow: false },
};

export default async function AdminLendersPage() {
  const lenders = await getLenders();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Lender Management</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Banks and NBFCs this DSA routes applications to, with their commission rate.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Lender</CardTitle>
        </CardHeader>
        <CardContent>
          <AdminCreateForm
            action={createLenderAction}
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          >
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="code">Code</Label>
              <Input id="code" name="code" required placeholder="e.g. HDFC" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="type">Type</Label>
              <select
                id="type"
                name="type"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
              >
                <option value="bank">Bank</option>
                <option value="nbfc">NBFC</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contact_email">Contact Email</Label>
              <Input id="contact_email" name="contact_email" type="email" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contact_phone">Contact Phone</Label>
              <Input id="contact_phone" name="contact_phone" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="commission_rate_percent">Commission Rate (%)</Label>
              <Input
                id="commission_rate_percent"
                name="commission_rate_percent"
                defaultValue="1"
                inputMode="decimal"
              />
            </div>
            <div className="sm:col-span-2 lg:col-span-3">
              <Button type="submit">Create Lender</Button>
            </div>
          </AdminCreateForm>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Lenders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Commission</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lenders.map((lender) => (
                  <TableRow key={lender.id}>
                    <TableCell className="font-medium">{lender.name}</TableCell>
                    <TableCell className="text-muted-foreground">{lender.code}</TableCell>
                    <TableCell className="uppercase">{lender.type}</TableCell>
                    <TableCell>{lender.commission_rate_percent}%</TableCell>
                    <TableCell>
                      <Badge variant={lender.is_active ? "secondary" : "destructive"}>
                        {lender.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <ToggleActiveButton
                        id={lender.id}
                        isActive={lender.is_active}
                        action={setLenderActiveAction}
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
