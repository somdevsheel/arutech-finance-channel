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
import { getNotificationTemplates } from "@/lib/admin/session";
import {
  createNotificationTemplateAction,
  setNotificationTemplateActiveAction,
} from "@/lib/admin/actions";
import { ToggleActiveButton } from "@/components/admin/toggle-active-button";

export const metadata: Metadata = {
  title: "Notification Templates",
  robots: { index: false, follow: false },
};

export default async function AdminNotificationTemplatesPage() {
  const templates = await getNotificationTemplates();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Notification Templates</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Email, SMS, and WhatsApp template content. Nothing sends yet — Phase 13&apos;s
          Notification Center will render and deliver these.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Template</CardTitle>
        </CardHeader>
        <CardContent>
          <form action={createNotificationTemplateAction} className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="code">Code</Label>
              <Input id="code" name="code" required placeholder="e.g. loan.approved" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="channel">Channel</Label>
              <select
                id="channel"
                name="channel"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>
            <div className="sm:col-span-2 space-y-1.5">
              <Label htmlFor="subject">Subject (email only)</Label>
              <Input id="subject" name="subject" />
            </div>
            <div className="sm:col-span-2 space-y-1.5">
              <Label htmlFor="body">Body</Label>
              <Textarea
                id="body"
                name="body"
                rows={3}
                placeholder="Use {{variable}} placeholders"
                required
              />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit">Create Template</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Templates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {templates.map((template) => (
                  <TableRow key={template.id}>
                    <TableCell className="font-medium">{template.code}</TableCell>
                    <TableCell className="uppercase">{template.channel}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {template.subject ?? "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={template.is_active ? "secondary" : "destructive"}>
                        {template.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <ToggleActiveButton
                        id={template.id}
                        isActive={template.is_active}
                        action={setNotificationTemplateActiveAction}
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
