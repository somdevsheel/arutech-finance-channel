import type { Metadata } from "next";
import { Card, CardContent } from "@/components/ui/card";
import { getSettings } from "@/lib/admin/session";
import { SettingRow } from "@/components/admin/setting-row";

export const metadata: Metadata = {
  title: "Settings",
  robots: { index: false, follow: false },
};

export default async function AdminSettingsPage() {
  const settings = await getSettings();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Typed key-value configuration — covers feature flags and workflow toggles too, not just
          plain settings. Keys are fixed (seeded by migration); only values can change here.
        </p>
      </div>

      <Card>
        <CardContent className="divide-y pt-6">
          {settings.map((setting) => (
            <SettingRow key={setting.key} setting={setting} />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
