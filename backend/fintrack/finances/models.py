from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    # null user = system default category; set user = custom category
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    color = models.CharField(max_length=7, default="#4caf50")

    class Meta:
        db_table = "finances_category"
        verbose_name_plural = "categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "user"], name="unique_category_per_user")
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    BANK_CHOICES = [
        ("nubank", "Nubank"),
        ("inter", "Inter"),
        ("btg", "BTG"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    statement = models.ForeignKey(
        "statements.Statement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )

    # ── Common fields — every bank has these ──────────────────────
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank = models.CharField(max_length=20, choices=BANK_CHOICES)
    is_credit = models.BooleanField(default=False)  # True = payment received / refund

    # ── Installment info — parsed from description (Nubank, Inter) ─
    is_installment = models.BooleanField(default=False)
    installment_number = models.IntegerField(null=True, blank=True)
    installment_total = models.IntegerField(null=True, blank=True)

    # ── Bank-specific nullable fields ─────────────────────────────
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Inter, BTG
    bank_category = models.CharField(max_length=100, null=True, blank=True)  # BTG native category
    transaction_type = models.CharField(max_length=50, null=True, blank=True)  # Inter: PIX, TED, etc.

    class Meta:
        db_table = "finances_transaction"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user", "-date"], name="idx_transaction_user_date"),
            models.Index(fields=["user", "bank"], name="idx_transaction_user_bank"),
            models.Index(fields=["user", "category"], name="idx_transaction_user_category"),
        ]

    def __str__(self):
        return f"{self.date} | {self.description} | {self.amount}"
