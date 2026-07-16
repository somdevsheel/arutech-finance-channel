export interface JobOpening {
  slug: string;
  title: string;
  department: string;
  location: string;
  type: "Full-time" | "Contract";
  description: string;
  responsibilities: string[];
  requirements: string[];
}

export const jobOpenings: JobOpening[] = [
  {
    slug: "senior-backend-engineer",
    title: "Senior Backend Engineer",
    department: "Engineering",
    location: "Bengaluru / Remote (India)",
    type: "Full-time",
    description:
      "Build and scale the systems that power loan origination, credit decisioning, and partner integrations across our bank and NBFC network.",
    responsibilities: [
      "Design and ship APIs for the loan origination and CRM platforms",
      "Own reliability and performance for services handling sensitive financial data",
      "Partner with the credit and risk team on decisioning workflows",
    ],
    requirements: [
      "4+ years building production backend systems (Python, Go, or similar)",
      "Experience with relational databases at scale",
      "Comfortable working in a regulated, security-conscious environment",
    ],
  },
  {
    slug: "credit-underwriter",
    title: "Credit Underwriter",
    department: "Risk & Credit",
    location: "Mumbai",
    type: "Full-time",
    description:
      "Assess borrower and business creditworthiness across our personal, business, and secured loan products, working closely with our partner banks and NBFCs.",
    responsibilities: [
      "Review financial statements, bank statements, and bureau reports",
      "Recommend approval terms within lender-specific policy guidelines",
      "Identify fraud indicators and escalate high-risk applications",
    ],
    requirements: [
      "2+ years in credit underwriting or risk assessment",
      "Working knowledge of CIBIL/credit bureau reports",
      "Bachelor's degree in finance, commerce, or a related field",
    ],
  },
  {
    slug: "business-development-associate",
    title: "Business Development Associate",
    department: "Partnerships",
    location: "Pune",
    type: "Full-time",
    description:
      "Grow and manage relationships with bank and NBFC partners, and identify new lending partners to expand the products we can offer borrowers.",
    responsibilities: [
      "Onboard new lending partners and negotiate commercial terms",
      "Track partner performance (approval rates, turnaround time, disbursal volume)",
      "Work with product and engineering on partner API integrations",
    ],
    requirements: [
      "2+ years in business development, preferably in BFSI",
      "Comfortable presenting to bank and NBFC stakeholders",
      "Strong ownership of commercial relationships end to end",
    ],
  },
  {
    slug: "customer-support-specialist",
    title: "Customer Support Specialist",
    department: "Operations",
    location: "Remote (India)",
    type: "Full-time",
    description:
      "Be the first point of contact for borrowers navigating their loan application, from document collection through disbursal.",
    responsibilities: [
      "Respond to customer queries over phone, email, and chat",
      "Coordinate document collection and follow-ups with applicants",
      "Escalate stuck applications to the right internal team",
    ],
    requirements: [
      "1+ years in a customer-facing support role",
      "Clear written and verbal communication in English and Hindi",
      "Comfortable working with CRM and ticketing tools",
    ],
  },
];
