export interface NavLink {
  href: string;
  label: string;
}

export const primaryNavLinks: NavLink[] = [
  { href: "/loans", label: "Loan Products" },
  { href: "/tools/emi-calculator", label: "EMI Calculator" },
  { href: "/tools/eligibility-calculator", label: "Eligibility Calculator" },
  { href: "/blog", label: "Blog" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
];

export const footerLinks = {
  company: [
    { href: "/about", label: "About Us" },
    { href: "/careers", label: "Careers" },
    { href: "/blog", label: "Blog" },
    { href: "/contact", label: "Contact" },
  ],
  products: [
    { href: "/loans", label: "All Loan Products" },
    { href: "/tools/emi-calculator", label: "EMI Calculator" },
    { href: "/tools/eligibility-calculator", label: "Eligibility Calculator" },
    { href: "/faqs", label: "FAQs" },
  ],
  legal: [
    { href: "/privacy-policy", label: "Privacy Policy" },
    { href: "/terms", label: "Terms of Service" },
    { href: "/disclaimer", label: "Disclaimer" },
  ],
} satisfies Record<string, NavLink[]>;
