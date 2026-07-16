export interface LoanProduct {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  interestRateMin: number;
  interestRateMax: number;
  tenureMinMonths: number;
  tenureMaxMonths: number;
  amountMin: number;
  amountMax: number;
  features: string[];
  eligibilityHighlights: string[];
  documentsRequired: string[];
}

export const loanProducts: LoanProduct[] = [
  {
    slug: "personal-loan",
    name: "Personal Loan",
    tagline: "Unsecured funding for whatever life brings next",
    description:
      "A collateral-free loan you can use for medical expenses, a wedding, travel, debt consolidation, or anything else — sanctioned in as little as 24 hours through our partner banks and NBFCs.",
    interestRateMin: 10.5,
    interestRateMax: 24,
    tenureMinMonths: 12,
    tenureMaxMonths: 60,
    amountMin: 50_000,
    amountMax: 4_000_000,
    features: [
      "No collateral or guarantor required",
      "Disbursal in 24-48 hours for eligible applicants",
      "Flexible tenure from 1 to 5 years",
      "Prepayment and foreclosure supported by most partner lenders",
    ],
    eligibilityHighlights: [
      "Age 21-58 years",
      "Minimum net monthly income of ₹25,000",
      "CIBIL score of 700 or higher preferred",
      "At least 1 year in current job or 2 years in business",
    ],
    documentsRequired: [
      "PAN card",
      "Aadhaar card",
      "Last 3 months' salary slips or 2 years' ITR for self-employed",
      "Last 6 months' bank statements",
    ],
  },
  {
    slug: "home-loan",
    name: "Home Loan",
    tagline: "Finance your first home or your next one",
    description:
      "Compare home loan offers from multiple banks and housing finance companies in one place, for purchase, construction, or balance transfer, with tenures stretching up to 30 years.",
    interestRateMin: 8.4,
    interestRateMax: 11.5,
    tenureMinMonths: 60,
    tenureMaxMonths: 360,
    amountMin: 500_000,
    amountMax: 50_000_000,
    features: [
      "Up to 90% of property value financed",
      "Balance transfer to a lower rate with top-up options",
      "Tenure up to 30 years to keep EMIs manageable",
      "Tax benefits under Sections 24(b) and 80C",
    ],
    eligibilityHighlights: [
      "Age 23-65 years (at loan maturity)",
      "Stable income source, salaried or self-employed",
      "CIBIL score of 750 or higher for the best rates",
      "Clear title on the property being financed",
    ],
    documentsRequired: [
      "PAN and Aadhaar card",
      "Income proof (salary slips or ITR)",
      "Property documents and sale agreement",
      "Last 6 months' bank statements",
    ],
  },
  {
    slug: "business-loan",
    name: "Business Loan",
    tagline: "Working capital and growth funding for your business",
    description:
      "Term loans and working capital lines for proprietorships, partnerships, and private limited companies, matched to lenders who understand your industry and cash flow cycle.",
    interestRateMin: 11,
    interestRateMax: 22,
    tenureMinMonths: 12,
    tenureMaxMonths: 84,
    amountMin: 100_000,
    amountMax: 20_000_000,
    features: [
      "Collateral-free options up to ₹50 lakh",
      "Overdraft and term loan structures available",
      "Funding for working capital, equipment, or expansion",
      "GST and banking-based underwriting for faster decisions",
    ],
    eligibilityHighlights: [
      "Business vintage of at least 2 years",
      "Minimum annual turnover of ₹10 lakh",
      "Business and promoter CIBIL score of 700+",
      "Profitable in at least 1 of the last 2 years",
    ],
    documentsRequired: [
      "PAN card of business and proprietor/partners/directors",
      "GST returns for the last 12 months",
      "Last 2 years' financial statements and ITR",
      "Last 12 months' bank statements",
    ],
  },
  {
    slug: "loan-against-property",
    name: "Loan Against Property",
    tagline: "Unlock the value of property you already own",
    description:
      "Borrow against residential or commercial property for business expansion, education, medical costs, or debt consolidation, at rates well below unsecured borrowing.",
    interestRateMin: 9,
    interestRateMax: 14,
    tenureMinMonths: 36,
    tenureMaxMonths: 180,
    amountMin: 500_000,
    amountMax: 30_000_000,
    features: [
      "Up to 65% of property market value",
      "Lower rates than personal or business loans",
      "Tenure up to 15 years",
      "Property continues to generate rental income if leased",
    ],
    eligibilityHighlights: [
      "Age 25-65 years",
      "Clear, marketable title on the property",
      "Stable income to service the EMI",
      "CIBIL score of 700 or higher",
    ],
    documentsRequired: [
      "PAN and Aadhaar card",
      "Property title deed and encumbrance certificate",
      "Income proof (salary slips or ITR)",
      "Last 6 months' bank statements",
    ],
  },
  {
    slug: "car-loan",
    name: "Car Loan",
    tagline: "Drive away in your new car sooner",
    description:
      "New and used car financing with quick approvals, matched to the dealer network and lender panel that gets you the best on-road price.",
    interestRateMin: 8.5,
    interestRateMax: 13,
    tenureMinMonths: 12,
    tenureMaxMonths: 84,
    amountMin: 100_000,
    amountMax: 5_000_000,
    features: [
      "Up to 90% on-road price financed",
      "New and pre-owned cars both eligible",
      "Same-day approval for salaried applicants",
      "No prepayment penalty after 6 months on most lenders",
    ],
    eligibilityHighlights: [
      "Age 21-60 years",
      "Minimum net monthly income of ₹20,000",
      "CIBIL score of 700 or higher preferred",
      "Valid driving license not required to apply",
    ],
    documentsRequired: [
      "PAN and Aadhaar card",
      "Income proof (salary slips or ITR)",
      "Proforma invoice from the dealer",
      "Last 3 months' bank statements",
    ],
  },
  {
    slug: "education-loan",
    name: "Education Loan",
    tagline: "Invest in an education without draining your savings",
    description:
      "Funding for tuition, living expenses, and travel for undergraduate, postgraduate, and professional courses in India and abroad, with moratorium periods aligned to your course length.",
    interestRateMin: 9.5,
    interestRateMax: 15,
    tenureMinMonths: 60,
    tenureMaxMonths: 180,
    amountMin: 100_000,
    amountMax: 15_000_000,
    features: [
      "Covers tuition, hostel, travel, and equipment costs",
      "Moratorium until 6-12 months after course completion",
      "Co-applicant income considered for larger amounts",
      "Interest subsidy schemes available for eligible applicants",
    ],
    eligibilityHighlights: [
      "Confirmed admission to a recognized institution",
      "Co-applicant (parent/guardian) with stable income",
      "Course-specific eligibility varies by lender",
      "Collateral required above ₹7.5 lakh with most lenders",
    ],
    documentsRequired: [
      "Admission letter and fee structure",
      "PAN and Aadhaar of applicant and co-applicant",
      "Co-applicant's income proof",
      "Academic records (10th, 12th, and prior degree)",
    ],
  },
  {
    slug: "gold-loan",
    name: "Gold Loan",
    tagline: "Fast, secured funding against your gold jewellery",
    description:
      "Same-day loans against gold jewellery with purity-based valuation, ideal for short-term needs where you want lower interest rates than an unsecured loan.",
    interestRateMin: 7.5,
    interestRateMax: 16,
    tenureMinMonths: 3,
    tenureMaxMonths: 36,
    amountMin: 10_000,
    amountMax: 2_500_000,
    features: [
      "Disbursal within hours of gold valuation",
      "Up to 75% of gold value as per RBI guidelines",
      "Minimal documentation, no income proof required",
      "Bullet repayment and EMI options both available",
    ],
    eligibilityHighlights: [
      "Age 18 years or above",
      "Ownership of gold jewellery (18-24 karat)",
      "No minimum income or CIBIL score requirement at most lenders",
      "Valid photo ID for KYC",
    ],
    documentsRequired: [
      "PAN or Aadhaar card for KYC",
      "Proof of address",
      "Gold ownership (jewellery brought in-person for valuation)",
    ],
  },
];

export function getLoanProductBySlug(slug: string): LoanProduct | undefined {
  return loanProducts.find((product) => product.slug === slug);
}
