import type { Metadata } from "next";
import { Mail, MapPin, Phone } from "lucide-react";
import { ContactForm } from "@/components/marketing/contact-form";

export const metadata: Metadata = {
  title: "Contact Us",
  description:
    "Get in touch with the Arutech Finance Platform team for questions about loans, partnerships, or your application.",
};

const contactDetails = [
  {
    icon: Mail,
    label: "Email",
    value: "support@arutech.com",
    href: "mailto:support@arutech.com",
  },
  {
    icon: Phone,
    label: "Phone",
    value: "+91 80 4567 8900",
    href: "tel:+918045678900",
  },
  {
    icon: MapPin,
    label: "Office",
    value: "4th Floor, Prestige Tech Park, Bengaluru, Karnataka 560103",
  },
];

export default function ContactPage() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">Contact Us</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Questions about a loan, your application, or a partnership? We&apos;d
          like to hear from you.
        </p>
      </div>

      <div className="mt-14 grid gap-12 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <ul className="space-y-6">
            {contactDetails.map(({ icon: Icon, label, value, href }) => (
              <li key={label} className="flex gap-4">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="size-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{label}</p>
                  {href ? (
                    <a href={href} className="font-medium hover:underline">
                      {value}
                    </a>
                  ) : (
                    <p className="font-medium">{value}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="lg:col-span-3">
          <ContactForm />
        </div>
      </div>
    </section>
  );
}
