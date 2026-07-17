"""add phase 9 admin panel tables

Revision ID: a9e3b9b15ff5
Revises: 855cc489f8bf
Create Date: 2026-07-17 15:12:08.551726

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9e3b9b15ff5'
down_revision: Union[str, Sequence[str], None] = '855cc489f8bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen at the time this migration was written — not imported from
# `infrastructure.database.seed_data` (permissions) or
# `domain.loans.products` (loan products). See migration c422da52af08's
# own comment for why migrations never import a live/growing module.
_NEW_PERMISSIONS: list[tuple[str, str]] = [
    ("lenders.read", "View the bank/NBFC lender catalog"),
    ("lenders.manage", "Create, update, and (de)activate lenders"),
    ("loan_products.read", "View the loan product catalog"),
    ("loan_products.manage", "Create, update, and (de)activate loan products"),
    ("notification_templates.read", "View notification templates"),
    ("notification_templates.manage", "Create, update, and (de)activate notification templates"),
    ("cms.read", "View CMS content, including unpublished drafts"),
    ("cms.manage", "Create, update, publish, and unpublish CMS content"),
    ("settings.read", "View system settings"),
    ("settings.manage", "Update system settings"),
]
# Admin-only — see seed_data.py's comment on why Phase 9 permissions
# aren't granted to employee.
_NEW_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [code for code, _ in _NEW_PERMISSIONS],
}

# A frozen copy of domain/loans/products.py's LOAN_PRODUCTS at the time
# this migration was written — the initial catalog Phase 7 already
# validated applications against as a hardcoded dict.
_LOAN_PRODUCTS: list[dict[str, object]] = [
    {
        "slug": "personal-loan",
        "name": "Personal Loan",
        "interest_rate_min": "10.5",
        "interest_rate_max": "24",
        "tenure_min_months": 12,
        "tenure_max_months": 60,
        "amount_min": 50_000,
        "amount_max": 4_000_000,
        "documents_required": [
            "PAN card",
            "Aadhaar card",
            "Last 3 months' salary slips or 2 years' ITR for self-employed",
            "Last 6 months' bank statements",
        ],
    },
    {
        "slug": "home-loan",
        "name": "Home Loan",
        "interest_rate_min": "8.4",
        "interest_rate_max": "11.5",
        "tenure_min_months": 60,
        "tenure_max_months": 360,
        "amount_min": 500_000,
        "amount_max": 50_000_000,
        "documents_required": [
            "PAN and Aadhaar card",
            "Income proof (salary slips or ITR)",
            "Property documents and sale agreement",
            "Last 6 months' bank statements",
        ],
    },
    {
        "slug": "business-loan",
        "name": "Business Loan",
        "interest_rate_min": "11",
        "interest_rate_max": "22",
        "tenure_min_months": 12,
        "tenure_max_months": 84,
        "amount_min": 100_000,
        "amount_max": 20_000_000,
        "documents_required": [
            "PAN card of business and proprietor/partners/directors",
            "GST returns for the last 12 months",
            "Last 2 years' financial statements and ITR",
            "Last 12 months' bank statements",
        ],
    },
    {
        "slug": "loan-against-property",
        "name": "Loan Against Property",
        "interest_rate_min": "9",
        "interest_rate_max": "14",
        "tenure_min_months": 36,
        "tenure_max_months": 180,
        "amount_min": 500_000,
        "amount_max": 30_000_000,
        "documents_required": [
            "PAN and Aadhaar card",
            "Property title deed and encumbrance certificate",
            "Income proof (salary slips or ITR)",
            "Last 6 months' bank statements",
        ],
    },
    {
        "slug": "car-loan",
        "name": "Car Loan",
        "interest_rate_min": "8.5",
        "interest_rate_max": "13",
        "tenure_min_months": 12,
        "tenure_max_months": 84,
        "amount_min": 100_000,
        "amount_max": 5_000_000,
        "documents_required": [
            "PAN and Aadhaar card",
            "Income proof (salary slips or ITR)",
            "Proforma invoice from the dealer",
            "Last 3 months' bank statements",
        ],
    },
    {
        "slug": "education-loan",
        "name": "Education Loan",
        "interest_rate_min": "9.5",
        "interest_rate_max": "15",
        "tenure_min_months": 60,
        "tenure_max_months": 180,
        "amount_min": 100_000,
        "amount_max": 15_000_000,
        "documents_required": [
            "Admission letter and fee structure",
            "PAN and Aadhaar of applicant and co-applicant",
            "Co-applicant's income proof",
            "Academic records (10th, 12th, and prior degree)",
        ],
    },
    {
        "slug": "gold-loan",
        "name": "Gold Loan",
        "interest_rate_min": "7.5",
        "interest_rate_max": "16",
        "tenure_min_months": 3,
        "tenure_max_months": 36,
        "amount_min": 10_000,
        "amount_max": 2_500_000,
        "documents_required": [
            "PAN or Aadhaar card for KYC",
            "Proof of address",
            "Gold ownership (jewellery brought in-person for valuation)",
        ],
    },
]

# A frozen copy of apps/web/src/content/blog-posts.ts's 3 existing posts
# at the time this migration was written — migrating them into the
# database so the public blog keeps its content once the frontend
# switches to fetching from /api/v1/public/blog-posts (see
# docs/phase-9-architecture.md). Seeded already-published, at their
# original publish dates, to preserve current visibility/ordering.
_BLOG_POSTS: list[dict[str, object]] = [
    {
        "slug": "understanding-your-cibil-score",
        "title": "Understanding Your CIBIL Score (And How to Improve It)",
        "excerpt": (
            "Your CIBIL score is the single number lenders look at first. "
            "Here's what actually moves it, and what doesn't."
        ),
        "author": "Arutech Editorial Team",
        "published_at": "2026-05-12",
        "reading_minutes": 6,
        "tags": ["Credit Score", "Personal Finance"],
        "sections": [
            {
                "heading": None,
                "paragraphs": [
                    "A CIBIL score is a three-digit number between 300 and 900 that "
                    "summarizes your credit history — how much you've borrowed, how "
                    "reliably you've repaid it, and how you use credit day to day. "
                    "Most lenders in India treat 750 and above as a strong score, "
                    "700-750 as acceptable, and anything below 650 as high risk.",
                ],
            },
            {
                "heading": "What actually affects your score",
                "paragraphs": [
                    "Payment history carries the most weight — a single missed credit "
                    "card payment or EMI can knock 50-100 points off your score and "
                    "stays on your report for years. Credit utilization is next: using "
                    "more than 30% of your available credit card limit regularly "
                    "signals risk to lenders, even if you pay it off in full every "
                    "month.",
                    "The length of your credit history and the mix of credit types "
                    "(credit cards, personal loans, home loans) matter too, though "
                    "less than the first two. Applying for multiple loans or cards in "
                    "a short window also dings your score, since each hard inquiry is "
                    "recorded.",
                ],
            },
            {
                "heading": "What doesn't affect your score",
                "paragraphs": [
                    "Checking your own score doesn't hurt it — that's a 'soft inquiry' "
                    "and is treated differently from a lender's hard inquiry. Your "
                    "salary isn't part of the score calculation either, though "
                    "lenders do look at it separately when deciding how much to lend "
                    "you.",
                ],
            },
            {
                "heading": "Practical steps if your score needs work",
                "paragraphs": [
                    "Pay every EMI and credit card bill on or before the due date — "
                    "set up autopay if you tend to forget. Keep credit card usage "
                    "under 30% of your limit, and pay down existing balances before "
                    "applying for a new loan. Avoid applying to multiple lenders in a "
                    "short period; use a pre-qualification tool (like our Eligibility "
                    "Calculator) instead, which doesn't create a hard inquiry.",
                ],
            },
        ],
    },
    {
        "slug": "how-dsa-partners-speed-up-loan-approvals",
        "title": "How a DSA Partner Actually Speeds Up Your Loan Approval",
        "excerpt": (
            "A Direct Selling Agent isn't just a middleman — done well, it removes "
            "the friction that slows loan applications down."
        ),
        "author": "Arutech Editorial Team",
        "published_at": "2026-04-03",
        "reading_minutes": 5,
        "tags": ["DSA", "Loan Process"],
        "sections": [
            {
                "heading": None,
                "paragraphs": [
                    "If you've applied for a loan directly with a bank before, you "
                    "know the drill: a branch visit, a stack of physical documents, a "
                    "follow-up call two weeks later asking for one more form. A DSA "
                    "platform like Arutech exists to compress that timeline, not by "
                    "cutting corners, but by doing the preparation work upfront.",
                ],
            },
            {
                "heading": "Matching you to lenders who'll actually say yes",
                "paragraphs": [
                    "Every bank and NBFC has different underwriting appetite — one "
                    "might favor salaried applicants with a specific employer list, "
                    "another might be more flexible on self-employed income. A DSA "
                    "that works with many lenders can route your application to the "
                    "ones most likely to approve it quickly, instead of you guessing "
                    "and getting rejected (which itself can affect your credit "
                    "score).",
                ],
            },
            {
                "heading": "Getting your documentation right the first time",
                "paragraphs": [
                    "Most delays in loan processing come from incomplete or "
                    "inconsistent documentation — a bank statement that doesn't "
                    "match the income stated, a missing signature, an expired ID "
                    "proof. A DSA reviews your application before it reaches the "
                    "lender, catching these issues when they're a two-minute fix "
                    "instead of a two-week delay.",
                ],
            },
            {
                "heading": "One application, multiple offers",
                "paragraphs": [
                    "Rather than applying separately to three or four banks (and "
                    "taking three or four credit inquiries in the process), a DSA "
                    "platform can submit your application to multiple partners in "
                    "parallel, so you compare final offers side by side and choose "
                    "the best rate and terms.",
                ],
            },
        ],
    },
    {
        "slug": "5-tips-to-improve-loan-eligibility",
        "title": "5 Practical Ways to Improve Your Loan Eligibility",
        "excerpt": (
            "Small changes 2-3 months before you apply can meaningfully change "
            "what you qualify for."
        ),
        "author": "Arutech Editorial Team",
        "published_at": "2026-03-18",
        "reading_minutes": 4,
        "tags": ["Eligibility", "Personal Finance"],
        "sections": [
            {
                "heading": None,
                "paragraphs": [
                    "Loan eligibility isn't just your income — lenders weigh your "
                    "existing obligations, credit history, and stability just as "
                    "heavily. Here are five changes that move the needle, roughly in "
                    "order of impact.",
                ],
            },
            {
                "heading": "1. Pay down existing EMIs and credit card balances",
                "paragraphs": [
                    "Lenders calculate eligibility using your Fixed Obligation to "
                    "Income Ratio (FOIR) — the share of your monthly income already "
                    "committed to EMIs and credit card minimums. Closing a small "
                    "existing loan or paying off a credit card balance directly "
                    "increases how much new EMI you can qualify for.",
                ],
            },
            {
                "heading": "2. Add a co-applicant",
                "paragraphs": [
                    "For home loans and education loans especially, adding a "
                    "co-applicant with a stable income (a spouse or parent) combines "
                    "both incomes for eligibility purposes, which can substantially "
                    "raise your approved loan amount.",
                ],
            },
            {
                "heading": "3. Correct errors on your credit report",
                "paragraphs": [
                    "It's common for credit reports to show a loan as still open "
                    "after you've closed it, or to misreport a payment as late. "
                    "Request your report from CIBIL directly and raise a dispute for "
                    "any inaccuracies before you apply — this can take a few weeks, "
                    "so do it early.",
                ],
            },
            {
                "heading": "4. Choose a longer tenure",
                "paragraphs": [
                    "A longer tenure lowers your monthly EMI for the same loan "
                    "amount, which can bring your FOIR back within a lender's "
                    "guidelines. You'll pay more interest over the life of the loan, "
                    "but it can be the difference between approval and rejection — "
                    "and most lenders allow prepayment later once your finances "
                    "improve.",
                ],
            },
            {
                "heading": "5. Time your application around income stability",
                "paragraphs": [
                    "Lenders generally want to see at least 1 year in your current "
                    "job (salaried) or 2-3 years of business vintage (self-employed). "
                    "If you've just switched jobs or started a business, it's often "
                    "worth waiting a few months rather than applying immediately.",
                ],
            },
        ],
    },
]


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('blog_posts',
    sa.Column('slug', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('excerpt', sa.Text(), nullable=False),
    sa.Column('author', sa.String(length=255), nullable=False),
    sa.Column('reading_minutes', sa.Integer(), nullable=False),
    sa.Column('sections', sa.JSON(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blog_posts_slug'), 'blog_posts', ['slug'], unique=True)
    op.create_table('lenders',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('bank', 'nbfc', name='lender_type'), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('contact_email', sa.String(length=255), nullable=True),
    sa.Column('contact_phone', sa.String(length=20), nullable=True),
    sa.Column('commission_rate_percent', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lenders_code'), 'lenders', ['code'], unique=True)
    op.create_table('loan_products',
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('interest_rate_min', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('interest_rate_max', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('tenure_min_months', sa.Integer(), nullable=False),
    sa.Column('tenure_max_months', sa.Integer(), nullable=False),
    sa.Column('amount_min', sa.Integer(), nullable=False),
    sa.Column('amount_max', sa.Integer(), nullable=False),
    sa.Column('documents_required', sa.JSON(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_loan_products_slug'), 'loan_products', ['slug'], unique=True)
    op.create_table('notification_templates',
    sa.Column('code', sa.String(length=150), nullable=False),
    sa.Column('channel', sa.Enum('email', 'sms', 'whatsapp', name='notification_channel'), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_templates_code'), 'notification_templates', ['code'], unique=True)
    op.create_table('system_settings',
    sa.Column('key', sa.String(length=150), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('value_type', sa.Enum('string', 'boolean', 'number', name='setting_value_type'), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)
    # ### end Alembic commands ###

    _seed_phase9_permissions()
    _seed_loan_products()
    _seed_blog_posts()
    _seed_settings()


def _seed_phase9_permissions() -> None:
    bind = op.get_bind()

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("description", sa.String()),
    )
    roles_table = sa.table("roles", sa.column("id", sa.Uuid()), sa.column("name", sa.String()))
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )

    permission_ids = {code: uuid.uuid4() for code, _ in _NEW_PERMISSIONS}
    op.bulk_insert(
        permissions_table,
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in _NEW_PERMISSIONS
        ],
    )

    role_ids = {
        row.name: row.id
        for row in bind.execute(
            sa.select(roles_table.c.id, roles_table.c.name).where(
                roles_table.c.name.in_(_NEW_ROLE_PERMISSIONS)
            )
        ).fetchall()
    }

    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[code]}
            for role_name, codes in _NEW_ROLE_PERMISSIONS.items()
            for code in codes
            if role_name in role_ids
        ],
    )


def _seed_loan_products() -> None:
    loan_products_table = sa.table(
        "loan_products",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("interest_rate_min", sa.Numeric()),
        sa.column("interest_rate_max", sa.Numeric()),
        sa.column("tenure_min_months", sa.Integer()),
        sa.column("tenure_max_months", sa.Integer()),
        sa.column("amount_min", sa.Integer()),
        sa.column("amount_max", sa.Integer()),
        sa.column("documents_required", sa.JSON()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        loan_products_table,
        [{**product, "id": uuid.uuid4(), "is_active": True} for product in _LOAN_PRODUCTS],
    )


def _seed_blog_posts() -> None:
    blog_posts_table = sa.table(
        "blog_posts",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("title", sa.String()),
        sa.column("excerpt", sa.Text()),
        sa.column("author", sa.String()),
        sa.column("reading_minutes", sa.Integer()),
        sa.column("sections", sa.JSON()),
        sa.column("tags", sa.JSON()),
        sa.column("is_published", sa.Boolean()),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        blog_posts_table,
        [
            {
                "id": uuid.uuid4(),
                "slug": post["slug"],
                "title": post["title"],
                "excerpt": post["excerpt"],
                "author": post["author"],
                "reading_minutes": post["reading_minutes"],
                "sections": post["sections"],
                "tags": post["tags"],
                "is_published": True,
                "published_at": datetime.fromisoformat(
                    post["published_at"]  # type: ignore[arg-type]
                ).replace(tzinfo=timezone.utc),
            }
            for post in _BLOG_POSTS
        ],
    )


def _seed_settings() -> None:
    settings_table = sa.table(
        "system_settings",
        sa.column("id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("value", sa.Text()),
        sa.column("value_type", sa.Enum(name="setting_value_type")),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        settings_table,
        [
            {
                "id": uuid.uuid4(),
                "key": "leads.auto_assignment_enabled",
                "value": "true",
                "value_type": "boolean",
                "description": (
                    "Whether new leads are auto-assigned to the least-loaded employee."
                ),
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    permissions_table = sa.table(
        "permissions", sa.column("id", sa.Uuid()), sa.column("code", sa.String())
    )
    codes = [code for code, _ in _NEW_PERMISSIONS]
    op.execute(permissions_table.delete().where(permissions_table.c.code.in_(codes)))

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_system_settings_key'), table_name='system_settings')
    op.drop_table('system_settings')
    op.drop_index(op.f('ix_notification_templates_code'), table_name='notification_templates')
    op.drop_table('notification_templates')
    op.drop_index(op.f('ix_loan_products_slug'), table_name='loan_products')
    op.drop_table('loan_products')
    op.drop_index(op.f('ix_lenders_code'), table_name='lenders')
    op.drop_table('lenders')
    op.drop_index(op.f('ix_blog_posts_slug'), table_name='blog_posts')
    op.drop_table('blog_posts')
    # ### end Alembic commands ###
    # As in earlier migrations: dropping the tables doesn't drop the
    # native Postgres enum types they created.
    for enum_name in ("setting_value_type", "notification_channel", "lender_type"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
