"""
Bulk-generate synthetic transactions for scalability testing.

Thin CLI wrapper around finances.services.generate_sample_transactions (the same
core the demo endpoint uses). Bypasses the parsers — builds Transaction rows
directly and bulk-inserts them, so the DB / dashboard can be stressed with
millions of rows without recreating the original CSV/XLSX/PDF formats.

Usage:
    python manage.py seed_transactions --config finances/seed_config.yml

The target user must already exist (register it via the app first) — their
categories are seeded on registration, and generated transactions are
categorized against them.
"""

import random
import time

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from finances.services import generate_sample_transactions

User = get_user_model()


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
        credit_ratio = float(cfg.get("credit_ratio", 0.10))
        installment_ratio = float(cfg.get("installment_ratio", 0.15))
        unknown_ratio = float(cfg.get("unknown_ratio", 0.10))
        batch_size = int(cfg.get("batch_size", 5000))

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

        self.stdout.write(
            f"Generating {count:,} transactions for {email} "
            f"({years}y span, banks={banks})..."
        )

        t0 = time.time()

        def progress(created):
            self.stdout.write(f"  {created:,}/{count:,}", ending="\r")

        try:
            created = generate_sample_transactions(
                user,
                count,
                years=years,
                banks=banks,
                credit_ratio=credit_ratio,
                installment_ratio=installment_ratio,
                unknown_ratio=unknown_ratio,
                batch_size=batch_size,
                progress=progress,
            )
        except ValueError as exc:
            raise CommandError(str(exc))

        elapsed = time.time() - t0
        rate = created / elapsed if elapsed > 0 else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created:,} transactions for {email} "
                f"in {elapsed:.1f}s ({rate:,.0f}/s)."
            )
        )
