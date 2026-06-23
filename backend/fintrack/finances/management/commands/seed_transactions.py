"""
Bulk-generate synthetic transactions for scalability testing.

Bypasses the statement parsers entirely — builds Transaction rows directly and
bulk-inserts them, so we can stress the DB / dashboard with millions of rows
without recreating the original CSV/XLSX/PDF formats.

Usage:
    python manage.py seed_transactions --config finances/seed_config.yml

The target user must already exist (register it via the app first) — their
categories are seeded on registration, and generated transactions are
categorized against them using the real categorizer rules.
"""

import random
import time
from datetime import date, timedelta
from decimal import Decimal

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from finances.models import Transaction, Category
from finances.categorizer import categorize, CATEGORY_RULES

User = get_user_model()

# Flat pool of every keyword the categorizer knows — generated descriptions are
# drawn from it so the synthetic data exercises every category the same way real
# statements would.
_KEYWORD_POOL = [kw.strip() for _, _, kws in CATEGORY_RULES for kw in kws if kw.strip()]

_INSTALLMENT_TOTALS = [2, 3, 4, 6, 10, 12]


class Command(BaseCommand):
    help = "Bulk-generate synthetic transactions for a user (scalability testing)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            default="finances/seed_config.yml",
            help="Path to the YAML config (default: finances/seed_config.yml, relative to manage.py).",
        )

    def handle(self, *args, **options):
        with open(options["config"]) as f:
            cfg = yaml.safe_load(f)

        email = cfg["email"]
        count = int(cfg["count"])
        years = int(cfg.get("years", 3))
        banks = cfg.get("banks", ["nubank", "inter", "btg"])
        credit_ratio = float(cfg.get("credit_ratio", 0.1))
        installment_ratio = float(cfg.get("installment_ratio", 0.15))
        batch_size = int(cfg.get("batch_size", 5000))
        unknown_ratio = float(cfg.get("unknown_ratio", 0.1))  # share that falls to "Other"

        seed = cfg.get("seed")
        if seed is not None:
            random.seed(seed)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(
                f"User '{email}' not found. Register it through the app first "
                f"(registration seeds the user's categories)."
            )

        categories = {c.name: c for c in Category.objects.filter(user=user)}
        if not categories:
            raise CommandError(
                f"User '{email}' has no categories — cannot categorize. "
                f"Categories are seeded on registration."
            )

        today = date.today()
        start = today - timedelta(days=365 * years)
        span_days = (today - start).days

        self.stdout.write(
            f"Generating {count:,} transactions for {email} "
            f"({years}y span, banks={banks})..."
        )

        t0 = time.time()
        batch = []
        created = 0
        for _ in range(count):
            if random.random() < unknown_ratio:
                description = f"UNKNOWN MERCHANT {random.randint(1, 9999)}"
            else:
                kw = random.choice(_KEYWORD_POOL)
                description = f"{kw.upper()} {random.randint(1, 9999)}"

            tx_date = start + timedelta(days=random.randint(0, span_days))
            bank = random.choice(banks)
            is_credit = random.random() < credit_ratio
            amount = Decimal(f"{random.uniform(5, 2000):.2f}")

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
                    amount=amount,
                    bank=bank,
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
                self.stdout.write(f"  {created:,}/{count:,}", ending="\r")

        if batch:
            Transaction.objects.bulk_create(batch)
            created += len(batch)

        elapsed = time.time() - t0
        rate = created / elapsed if elapsed > 0 else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created:,} transactions for {email} "
                f"in {elapsed:.1f}s ({rate:,.0f}/s)."
            )
        )
