// Drafted as complete, realistic terms for a DSA/loan-marketplace
// platform, not placeholder copy — but not a substitute for review by
// qualified legal counsel before real production use.
import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/legal-page";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The terms governing your use of the Arutech Finance Platform website and services.",
};

export default function TermsPage() {
  return (
    <LegalPage
      title="Terms of Service"
      effectiveDate="January 1, 2026"
      intro="These terms govern your use of the Arutech Finance Platform website and services. By using our platform, you agree to these terms."
      sections={[
        {
          heading: "1. Our role",
          paragraphs: [
            "Arutech operates as a Direct Selling Agent (DSA) and loan services platform. We help you compare loan products and submit applications to our partner banks and NBFCs. Arutech is not a bank or NBFC, does not itself lend money, and does not guarantee approval of any application.",
          ],
        },
        {
          heading: "2. Eligibility to use our services",
          paragraphs: [
            "You must be at least 18 years old and capable of entering into a legally binding contract to use our services. Information you provide during registration or application must be accurate and complete.",
          ],
        },
        {
          heading: "3. Your responsibilities",
          bullets: [
            "Provide accurate, truthful information in your application and supporting documents",
            "Keep your account credentials confidential and notify us of any unauthorized use",
            "Use the platform only for legitimate loan inquiries, not fraudulent or abusive purposes",
          ],
          paragraphs: [],
        },
        {
          heading: "4. No guarantee of approval or terms",
          paragraphs: [
            "Submitting an application through Arutech does not guarantee approval, a specific interest rate, or specific loan terms. Final approval, interest rate, and terms are determined solely by the lending partner based on their own underwriting criteria.",
          ],
        },
        {
          heading: "5. Fees",
          paragraphs: [
            "Arutech does not charge borrowers to compare loan offers or submit an application. Any processing fees, foreclosure charges, or other costs are charged by the lending partner directly and disclosed in your sanction letter before you accept an offer.",
          ],
        },
        {
          heading: "6. Intellectual property",
          paragraphs: [
            "All content on this website, including text, graphics, logos, and software, is the property of Arutech or its licensors and may not be reproduced without permission.",
          ],
        },
        {
          heading: "7. Limitation of liability",
          paragraphs: [
            "To the maximum extent permitted by law, Arutech is not liable for any decision made by a lending partner, including rejection of an application, or for indirect or consequential losses arising from use of our platform.",
          ],
        },
        {
          heading: "8. Termination",
          paragraphs: [
            "We may suspend or terminate your access to the platform if you violate these terms or use the platform in a way that risks harm to Arutech, our partners, or other users.",
          ],
        },
        {
          heading: "9. Governing law",
          paragraphs: [
            "These terms are governed by the laws of India, and any disputes are subject to the exclusive jurisdiction of the courts in Bengaluru, Karnataka.",
          ],
        },
        {
          heading: "10. Changes to these terms",
          paragraphs: [
            "We may update these terms from time to time. Continued use of the platform after changes take effect constitutes acceptance of the revised terms.",
          ],
        },
        {
          heading: "11. Contact us",
          paragraphs: ["Questions about these terms can be sent to legal@arutech.com."],
        },
      ]}
    />
  );
}
