export interface BlogSection {
  heading?: string;
  paragraphs: string[];
}

export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  author: string;
  publishedAt: string; // ISO date
  readingMinutes: number;
  tags: string[];
  sections: BlogSection[];
}

export const blogPosts: BlogPost[] = [
  {
    slug: "understanding-your-cibil-score",
    title: "Understanding Your CIBIL Score (And How to Improve It)",
    excerpt:
      "Your CIBIL score is the single number lenders look at first. Here's what actually moves it, and what doesn't.",
    author: "Arutech Editorial Team",
    publishedAt: "2026-05-12",
    readingMinutes: 6,
    tags: ["Credit Score", "Personal Finance"],
    sections: [
      {
        paragraphs: [
          "A CIBIL score is a three-digit number between 300 and 900 that summarizes your credit history — how much you've borrowed, how reliably you've repaid it, and how you use credit day to day. Most lenders in India treat 750 and above as a strong score, 700-750 as acceptable, and anything below 650 as high risk.",
        ],
      },
      {
        heading: "What actually affects your score",
        paragraphs: [
          "Payment history carries the most weight — a single missed credit card payment or EMI can knock 50-100 points off your score and stays on your report for years. Credit utilization is next: using more than 30% of your available credit card limit regularly signals risk to lenders, even if you pay it off in full every month.",
          "The length of your credit history and the mix of credit types (credit cards, personal loans, home loans) matter too, though less than the first two. Applying for multiple loans or cards in a short window also dings your score, since each hard inquiry is recorded.",
        ],
      },
      {
        heading: "What doesn't affect your score",
        paragraphs: [
          "Checking your own score doesn't hurt it — that's a 'soft inquiry' and is treated differently from a lender's hard inquiry. Your salary isn't part of the score calculation either, though lenders do look at it separately when deciding how much to lend you.",
        ],
      },
      {
        heading: "Practical steps if your score needs work",
        paragraphs: [
          "Pay every EMI and credit card bill on or before the due date — set up autopay if you tend to forget. Keep credit card usage under 30% of your limit, and pay down existing balances before applying for a new loan. Avoid applying to multiple lenders in a short period; use a pre-qualification tool (like our Eligibility Calculator) instead, which doesn't create a hard inquiry.",
        ],
      },
    ],
  },
  {
    slug: "how-dsa-partners-speed-up-loan-approvals",
    title: "How a DSA Partner Actually Speeds Up Your Loan Approval",
    excerpt:
      "A Direct Selling Agent isn't just a middleman — done well, it removes the friction that slows loan applications down.",
    author: "Arutech Editorial Team",
    publishedAt: "2026-04-03",
    readingMinutes: 5,
    tags: ["DSA", "Loan Process"],
    sections: [
      {
        paragraphs: [
          "If you've applied for a loan directly with a bank before, you know the drill: a branch visit, a stack of physical documents, a follow-up call two weeks later asking for one more form. A DSA platform like Arutech exists to compress that timeline, not by cutting corners, but by doing the preparation work upfront.",
        ],
      },
      {
        heading: "Matching you to lenders who'll actually say yes",
        paragraphs: [
          "Every bank and NBFC has different underwriting appetite — one might favor salaried applicants with a specific employer list, another might be more flexible on self-employed income. A DSA that works with many lenders can route your application to the ones most likely to approve it quickly, instead of you guessing and getting rejected (which itself can affect your credit score).",
        ],
      },
      {
        heading: "Getting your documentation right the first time",
        paragraphs: [
          "Most delays in loan processing come from incomplete or inconsistent documentation — a bank statement that doesn't match the income stated, a missing signature, an expired ID proof. A DSA reviews your application before it reaches the lender, catching these issues when they're a two-minute fix instead of a two-week delay.",
        ],
      },
      {
        heading: "One application, multiple offers",
        paragraphs: [
          "Rather than applying separately to three or four banks (and taking three or four credit inquiries in the process), a DSA platform can submit your application to multiple partners in parallel, so you compare final offers side by side and choose the best rate and terms.",
        ],
      },
    ],
  },
  {
    slug: "5-tips-to-improve-loan-eligibility",
    title: "5 Practical Ways to Improve Your Loan Eligibility",
    excerpt:
      "Small changes 2-3 months before you apply can meaningfully change what you qualify for.",
    author: "Arutech Editorial Team",
    publishedAt: "2026-03-18",
    readingMinutes: 4,
    tags: ["Eligibility", "Personal Finance"],
    sections: [
      {
        paragraphs: [
          "Loan eligibility isn't just your income — lenders weigh your existing obligations, credit history, and stability just as heavily. Here are five changes that move the needle, roughly in order of impact.",
        ],
      },
      {
        heading: "1. Pay down existing EMIs and credit card balances",
        paragraphs: [
          "Lenders calculate eligibility using your Fixed Obligation to Income Ratio (FOIR) — the share of your monthly income already committed to EMIs and credit card minimums. Closing a small existing loan or paying off a credit card balance directly increases how much new EMI you can qualify for.",
        ],
      },
      {
        heading: "2. Add a co-applicant",
        paragraphs: [
          "For home loans and education loans especially, adding a co-applicant with a stable income (a spouse or parent) combines both incomes for eligibility purposes, which can substantially raise your approved loan amount.",
        ],
      },
      {
        heading: "3. Correct errors on your credit report",
        paragraphs: [
          "It's common for credit reports to show a loan as still open after you've closed it, or to misreport a payment as late. Request your report from CIBIL directly and raise a dispute for any inaccuracies before you apply — this can take a few weeks, so do it early.",
        ],
      },
      {
        heading: "4. Choose a longer tenure",
        paragraphs: [
          "A longer tenure lowers your monthly EMI for the same loan amount, which can bring your FOIR back within a lender's guidelines. You'll pay more interest over the life of the loan, but it can be the difference between approval and rejection — and most lenders allow prepayment later once your finances improve.",
        ],
      },
      {
        heading: "5. Time your application around income stability",
        paragraphs: [
          "Lenders generally want to see at least 1 year in your current job (salaried) or 2-3 years of business vintage (self-employed). If you've just switched jobs or started a business, it's often worth waiting a few months rather than applying immediately.",
        ],
      },
    ],
  },
];

export function getBlogPostBySlug(slug: string): BlogPost | undefined {
  return blogPosts.find((post) => post.slug === slug);
}
