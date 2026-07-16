// Drafted as complete, realistic policy text for a lending-adjacent
// platform, not placeholder copy — but this is not a substitute for review
// by qualified legal counsel before real production use, particularly for
// compliance with the Digital Personal Data Protection Act, 2023 and RBI
// data-handling guidance for lending service providers.
import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/legal-page";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Arutech Finance Platform collects, uses, and protects your data.",
};

export default function PrivacyPolicyPage() {
  return (
    <LegalPage
      title="Privacy Policy"
      effectiveDate="January 1, 2026"
      intro="This policy explains what personal and financial information Arutech Finance Platform ('Arutech', 'we', 'us') collects when you use our website and services, how we use it, and the choices you have."
      sections={[
        {
          heading: "1. Information we collect",
          paragraphs: [
            "We collect information you provide directly, such as your name, contact details, income, employment, and identity documents (PAN, Aadhaar) submitted as part of a loan application or eligibility check.",
          ],
          bullets: [
            "Contact information: name, email, phone number, address",
            "Financial information: income, employment, existing obligations, bank statements",
            "Identity documents: PAN, Aadhaar, or other KYC documents you upload",
            "Usage data: pages visited, device and browser information, and approximate location from IP address",
          ],
        },
        {
          heading: "2. How we use your information",
          paragraphs: [
            "We use your information to operate the platform and to facilitate loan applications with our partner banks and NBFCs.",
          ],
          bullets: [
            "To assess loan eligibility and route your application to suitable lending partners",
            "To verify your identity and prevent fraud",
            "To communicate with you about your application status",
            "To improve our website and services, including analytics on aggregate usage patterns",
          ],
        },
        {
          heading: "3. Who we share your information with",
          paragraphs: [
            "We share your application data only with the specific lending partners you choose to apply to, and with service providers who help us operate the platform (such as identity verification and cloud hosting providers), under contractual confidentiality obligations.",
            "We do not sell your personal information to third parties, and we do not share your data with lenders you have not chosen to apply to.",
          ],
        },
        {
          heading: "4. Data security",
          paragraphs: [
            "We encrypt data in transit (TLS) and at rest, restrict access to personal and financial data to personnel who need it to perform their role, and log access to sensitive records for audit purposes.",
          ],
        },
        {
          heading: "5. Data retention",
          paragraphs: [
            "We retain application data for as long as needed to service your loan and to meet regulatory record-keeping requirements, after which it is deleted or anonymized in line with applicable law.",
          ],
        },
        {
          heading: "6. Your rights",
          paragraphs: [
            "You can request a copy of the personal data we hold about you, ask us to correct inaccurate information, or request deletion of data we are not legally required to retain, by contacting us at privacy@arutech.com.",
          ],
        },
        {
          heading: "7. Cookies and analytics",
          paragraphs: [
            "We use cookies and similar technologies for essential site functionality and, where enabled, aggregate analytics to understand how visitors use our site. You can control cookies through your browser settings.",
          ],
        },
        {
          heading: "8. Changes to this policy",
          paragraphs: [
            "We may update this policy from time to time. Material changes will be reflected by updating the effective date above.",
          ],
        },
        {
          heading: "9. Contact us",
          paragraphs: [
            "For questions about this policy or your data, contact us at privacy@arutech.com.",
          ],
        },
      ]}
    />
  );
}
