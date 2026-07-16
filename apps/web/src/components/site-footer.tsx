import Link from "next/link";
import { footerLinks } from "@/content/nav-links";

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { href: string; label: string }[];
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <ul className="mt-3 space-y-2">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-1">
            <span className="text-lg font-semibold tracking-tight">
              Arutech Finance
            </span>
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">
              A loan services platform connecting borrowers with partner banks
              and NBFCs across India.
            </p>
          </div>
          <FooterColumn title="Company" links={footerLinks.company} />
          <FooterColumn title="Products" links={footerLinks.products} />
          <FooterColumn title="Legal" links={footerLinks.legal} />
        </div>

        <div className="mt-10 flex flex-col gap-4 border-t pt-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>
            &copy; {new Date().getFullYear()} Arutech Finance Platform. All
            rights reserved.
          </p>
          <p className="max-w-2xl text-xs">
            Arutech is a loan services platform and Direct Selling Agent
            (DSA). We are not a bank or NBFC and do not ourselves lend money —
            see our{" "}
            <Link href="/disclaimer" className="underline underline-offset-2">
              Disclaimer
            </Link>{" "}
            for details.
          </p>
        </div>
      </div>
    </footer>
  );
}
