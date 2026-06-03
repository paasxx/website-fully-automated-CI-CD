from django.db import models
from django.conf import settings


class Statement(models.Model):
    BANK_CHOICES = [
        ("nubank", "Nubank"),
        ("inter", "Inter"),
        ("btg", "BTG"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processed", "Processed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="statements",
    )
    bank = models.CharField(max_length=20, choices=BANK_CHOICES)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    transaction_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "import_statement"
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "filename"],
                name="unique_statement_per_user"
            )
        ]

    def __str__(self):
        return f"{self.bank} | {self.filename} | {self.uploaded_at:%Y-%m-%d}"
