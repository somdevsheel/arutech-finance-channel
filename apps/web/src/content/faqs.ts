export interface Faq {
  question: string;
  answer: string;
  category: "General" | "Eligibility" | "Application" | "Repayment";
}

export const faqs: Faq[] = [
  {
    category: "General",
    question: "What is Arutech Finance Platform?",
    answer:
      "Arutech is a loan services platform that connects borrowers with our partner banks and NBFCs. We're a Direct Selling Agent (DSA) — we help you compare offers, prepare your application, and track it through to disbursal, but the loan itself is issued by the lending partner, not by Arutech.",
  },
  {
    category: "General",
    question: "Does Arutech charge me anything to apply?",
    answer:
      "No. Comparing loan offers and submitting an application through Arutech is free for borrowers. Any processing fees are charged by the lending partner directly and are disclosed upfront in your sanction letter before you accept an offer.",
  },
  {
    category: "General",
    question: "Is my personal and financial data safe?",
    answer:
      "Yes. We only share your application data with the lenders you choose to apply to, use encryption in transit and at rest, and never sell your information to third parties. See our Privacy Policy for full details.",
  },
  {
    category: "Eligibility",
    question: "What CIBIL score do I need to qualify?",
    answer:
      "It varies by loan type and lender, but a CIBIL score of 700 or above generally qualifies you for the best rates across most of our partner lenders. Scores between 650-700 can still qualify for some products, often at a higher interest rate.",
  },
  {
    category: "Eligibility",
    question: "Can self-employed applicants apply?",
    answer:
      "Yes. Self-employed applicants can apply for personal, business, home, and loan-against-property products. You'll typically need 2 years of ITR and bank statements instead of salary slips.",
  },
  {
    category: "Eligibility",
    question: "I have an existing loan. Can I still apply?",
    answer:
      "Yes, as long as your total EMI obligations (existing plus the new loan) stay within the lender's income-to-EMI ratio guidelines. Use our Eligibility Calculator for a quick estimate before you apply.",
  },
  {
    category: "Application",
    question: "How long does approval take?",
    answer:
      "Personal and gold loans are often approved within 24-48 hours for eligible applicants. Home loans, business loans, and loan-against-property typically take 5-10 business days due to property or business due diligence.",
  },
  {
    category: "Application",
    question: "Can I apply to more than one lender at once?",
    answer:
      "Yes. We route eligible applications to multiple partner lenders in parallel so you can compare final offers before accepting one. Accepting one offer doesn't obligate you to any others.",
  },
  {
    category: "Application",
    question: "What happens after I submit my documents?",
    answer:
      "Your application moves through verification, credit assessment, and — for secured loans — collateral valuation, with your relationship manager keeping you updated at each stage. You can also track status from your customer dashboard once it's live.",
  },
  {
    category: "Repayment",
    question: "Can I prepay or foreclose my loan early?",
    answer:
      "Most of our partner lenders allow prepayment and foreclosure, often without penalty after an initial lock-in period (commonly 6-12 months). Exact terms are specific to your sanction letter — we'll flag any foreclosure charges before you accept an offer.",
  },
  {
    category: "Repayment",
    question: "What happens if I miss an EMI payment?",
    answer:
      "Contact your lender or your Arutech relationship manager as soon as possible — most lenders offer a short grace period, but missed payments are reported to credit bureaus and can affect your CIBIL score, so it's best to address it early.",
  },
];
