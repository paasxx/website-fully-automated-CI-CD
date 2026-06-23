import random
from datetime import date, timedelta
from decimal import Decimal

from .models import Category, Transaction
from .categorizer import categorize, default_categories, CATEGORY_RULES

# Flat pool of every keyword the categorizer knows — generated descriptions are
# drawn from it so synthetic data exercises every category like real data would.
_KEYWORD_POOL = [kw.strip() for _, _, kws in CATEGORY_RULES for kw in kws if kw.strip()]
_INSTALLMENT_TOTALS = [2, 3, 4, 6, 10, 12]


def seed_default_categories(user):
    """
    Create the default set of categories for a newly registered user.

    Called from the registration flow (identity) so every user starts with a full,
    fully-editable set of categories — there are no shared system categories.
    The names/colors come from categorizer.default_categories() (single source of truth).
    """
    Category.objects.bulk_create(
        [Category(user=user, name=name, color=color) for name, color in default_categories()]
    )


def generate_sample_transactions(
    user,
    count,
    *,
    years=3,
    banks=("nubank", "inter", "btg"),
    credit_ratio=0.10,
    installment_ratio=0.15,
    unknown_ratio=0.10,
    batch_size=5000,
    progress=None,
):
    """
    Generate `count` synthetic transactions for `user` and bulk-insert them.

    Shared core used by both the seed_transactions management command (scalability
    testing, large counts) and the demo endpoint (small, per-user sample data).
    Bypasses the parsers — builds Transaction rows directly.

    `progress`, if given, is called with the running created-count after each batch.
    Returns the number of transactions created. Raises ValueError if the user has
    no categories (they are seeded on registration).
    """
    categories = {c.name: c for c in Category.objects.filter(user=user)}
    if not categories:
        raise ValueError(
            f"User '{user}' has no categories — cannot categorize. "
            f"Categories are seeded on registration."
        )

    today = date.today()
    start = today - timedelta(days=365 * years)
    span_days = (today - start).days

    batch = []
    created = 0
    for _ in range(count):
        if random.random() < unknown_ratio:
            description = f"UNKNOWN MERCHANT {random.randint(1, 9999)}"
        else:
            kw = random.choice(_KEYWORD_POOL)
            description = f"{kw.upper()} {random.randint(1, 9999)}"

        tx_date = start + timedelta(days=random.randint(0, span_days))
        is_credit = random.random() < credit_ratio
        is_installment = (not is_credit) and (random.random() < installment_ratio)
        if is_installment:
            inst_total = random.choice(_INSTALLMENT_TOTALS)
            inst_num = random.randint(1, inst_total)
        else:
            inst_total = inst_num = None

        batch.append(
            Transaction(
                user=user,
                date=tx_date,
                description=description,
                amount=Decimal(f"{random.uniform(5, 2000):.2f}"),
                bank=random.choice(banks),
                is_credit=is_credit,
                is_installment=is_installment,
                installment_number=inst_num,
                installment_total=inst_total,
                category=categorize(description, categories),
            )
        )

        if len(batch) >= batch_size:
            Transaction.objects.bulk_create(batch)
            created += len(batch)
            batch = []
            if progress:
                progress(created)

    if batch:
        Transaction.objects.bulk_create(batch)
        created += len(batch)

    return created
