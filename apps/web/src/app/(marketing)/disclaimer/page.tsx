// Drafted as complete, realistic disclaimer text for a DSA/loan-marketplace
// platform, not placeholder copy — but not a substitute for review by
// qualified legal counsel before real production use.
import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/legal-page";

export const metadata: Metadata = {
  title: "Disclaimer",
  description:
    "Arutech Finance Platform is a loan services platform and DSA, not a bank or NBFC. Read our full disclaimer.",
};

export default function DisclaimerPage() {
  return (
    <LegalPage
      title="Disclaimer"
      effectiveDate="January 1, 2026"
      intro="This page clarifies what Arutech Finance Platform is, and is not, so you can make an informed decision about using our services."
      sections={[
        {
          heading: "Arutech is not a lender",
          paragraphs: [
            "Arutech Finance Platform is a Direct Selling Agent (DSA) and loan services platform. We are not a bank, NBFC, or registered lender, and we do not ourselves lend money or hold any deposit-taking or lending license. All loans facilitated through our platform are issued by our partner banks and non-banking financial companies (NBFCs), who are separately licensed and regulated.",
          ],
        },
        {
          heading: "No guarantee of approval, rate, or terms",
          paragraphs: [
            "Any interest rate, tenure, or loan amount shown on this website — including results from our EMI and Eligibility Calculators — is illustrative and based on ranges published by our partner lenders. It is not an offer of credit and does not guarantee that you will be approved, or that you will receive those exact terms. Final approval and terms are determined solely by the lending partner after their own underwriting assessment.",
          ],
        },
        {
          heading: "Calculators are estimates only",
          paragraphs: [
            "Our EMI Calculator and Eligibility Calculator use standard financial formulas to provide an illustrative estimate. They do not perform a credit bureau check, do not access your actual bank or bureau data, and should not be treated as a substitute for a lender's formal eligibility assessment.",
          ],
        },
        {
          heading: "Third-party content and links",
          paragraphs: [
            "Our website may link to or reference third-party lenders, products, or services. We do not control and are not responsible for the content, accuracy, or practices of third parties, including our lending partners' own websites and terms.",
          ],
        },
        {
          heading: "Not financial or legal advice",
          paragraphs: [
            "Content on this website, including our blog articles, is provided for general informational purposes only and does not constitute financial, legal, or tax advice. Consult a qualified professional before making borrowing decisions specific to your circumstances.",
          ],
        },
        {
          heading: "Contact us",
          paragraphs: [
            "If anything on this page is unclear, contact us at legal@arutech.com before applying for a loan through our platform.",
          ],
        },
      ]}
    />
  );
}
