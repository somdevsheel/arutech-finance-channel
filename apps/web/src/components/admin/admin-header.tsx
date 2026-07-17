import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SignOutButton } from "@/components/portal/sign-out-button";
import type { AuthUser } from "@/types/auth";

function initials(user: AuthUser): string {
  const fromName = user.full_name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return fromName || user.email[0]?.toUpperCase() || "?";
}

export function AdminHeader({ user }: { user: AuthUser }) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/admin/dashboard" className="text-lg font-semibold tracking-tight">
            Arutech <span className="text-muted-foreground">Admin</span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            <Link
              href="/admin/dashboard"
              className="rounded-lg bg-muted px-3 py-2 text-sm font-medium text-foreground"
            >
              Dashboard
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium leading-none">{user.full_name}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{user.email}</p>
          </div>
          <Avatar className="size-8">
            <AvatarFallback>{initials(user)}</AvatarFallback>
          </Avatar>
          <SignOutButton />
        </div>
      </div>
    </header>
  );
}
