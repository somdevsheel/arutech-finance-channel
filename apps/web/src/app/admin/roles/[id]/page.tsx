import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getPermissions, getRolePermissions, getRoles } from "@/lib/admin/session";
import { grantPermissionAction } from "@/lib/admin/actions";
import { AdminCreateForm } from "@/components/admin/admin-create-form";
import { RevokePermissionButton } from "@/components/admin/revoke-permission-button";

export const metadata: Metadata = {
  title: "Role Detail",
  robots: { index: false, follow: false },
};

export default async function AdminRoleDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [roles, permissions, allPermissions] = await Promise.all([
    getRoles(),
    getRolePermissions(id),
    getPermissions(),
  ]);
  const role = roles.find((r) => r.id === id);
  if (!role) notFound();

  const grantedCodes = new Set(permissions.map((p) => p.code));
  const available = allPermissions.filter((p) => !grantedCodes.has(p.code));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{role.name}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{role.description}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Granted Permissions</CardTitle>
        </CardHeader>
        <CardContent>
          {permissions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No permissions granted yet.</p>
          ) : (
            <ul className="space-y-2">
              {permissions.map((permission) => (
                <li key={permission.id} className="flex items-center justify-between gap-3">
                  <div>
                    <Badge variant="secondary">{permission.code}</Badge>
                    <span className="ml-2 text-sm text-muted-foreground">
                      {permission.description}
                    </span>
                  </div>
                  <RevokePermissionButton roleId={role.id} permissionCode={permission.code} />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {available.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Grant a Permission</CardTitle>
          </CardHeader>
          <CardContent>
            <AdminCreateForm
              action={grantPermissionAction.bind(null, role.id)}
              className="flex flex-wrap items-end gap-3"
            >
              <select
                name="permission_code"
                required
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              >
                {available.map((permission) => (
                  <option key={permission.id} value={permission.code}>
                    {permission.code}
                  </option>
                ))}
              </select>
              <Button type="submit" size="sm">
                Grant
              </Button>
            </AdminCreateForm>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
