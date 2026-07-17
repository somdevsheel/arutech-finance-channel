import type { Metadata } from "next";
import Link from "next/link";
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
import { getRoles } from "@/lib/admin/session";
import { createRoleAction } from "@/lib/admin/actions";
import { DeleteRoleButton } from "@/components/admin/delete-role-button";

export const metadata: Metadata = {
  title: "Role Management",
  robots: { index: false, follow: false },
};

export default async function AdminRolesPage() {
  const roles = await getRoles();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Role Management</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          System roles are seeded and can&apos;t be deleted. Custom roles can be created here and
          granted specific permissions.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Custom Role</CardTitle>
        </CardHeader>
        <CardContent>
          <form action={createRoleAction} className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" required className="w-48" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Input id="description" name="description" className="w-64" />
            </div>
            <Button type="submit">Create Role</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Roles</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">
                    <Link href={`/admin/roles/${role.id}`} className="hover:underline">
                      {role.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{role.description}</TableCell>
                  <TableCell>
                    <Badge variant={role.is_system ? "secondary" : "outline"}>
                      {role.is_system ? "System" : "Custom"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {!role.is_system && <DeleteRoleButton roleId={role.id} />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
