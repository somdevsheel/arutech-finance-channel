import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SignOutButton } from "@/components/portal/sign-out-button";
import type { AuthUser } from "@/types/auth";

// Phase 9 added 8 more admin destinations — too many for a flat nav bar,
// so everything but Dashboard lives under one "Admin Panel" dropdown.
const ADMIN_PANEL_LINKS = [
  { href: "/admin/users", label: "Users" },
  { href: "/admin/roles", label: "Roles & Permissions" },
  { href: "/admin/lenders", label: "Lenders" },
  { href: "/admin/loan-products", label: "Loan Products" },
  { href: "/admin/notification-templates", label: "Notification Templates" },
  { href: "/admin/cms/blog-posts", label: "CMS — Blog Posts" },
  { href: "/admin/settings", label: "Settings" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
];

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
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              Dashboard
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground outline-none hover:bg-muted hover:text-foreground">
                Admin Panel
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {ADMIN_PANEL_LINKS.map((link) => (
                  <DropdownMenuItem key={link.href} render={<Link href={link.href} />}>
                    {link.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium leading-none">{user.full_name}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">{user.email}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-3 focus-visible:ring-ring/50">
              <Avatar className="size-8">
                <AvatarFallback>{initials(user)}</AvatarFallback>
              </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="font-normal md:hidden">
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-medium">{user.full_name}</span>
                  <span className="text-xs text-muted-foreground">{user.email}</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator className="md:hidden" />
              {ADMIN_PANEL_LINKS.map((link) => (
                <DropdownMenuItem
                  key={link.href}
                  render={<Link href={link.href} />}
                  className="md:hidden"
                >
                  {link.label}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator className="md:hidden" />
              <div className="px-1.5 py-1">
                <SignOutButton className="w-full justify-start px-1.5" />
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
