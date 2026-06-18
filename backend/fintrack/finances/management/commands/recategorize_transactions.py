from django.core.management.base import BaseCommand
from finances.models import Transaction, Category
from finances.categorizer import categorize


class Command(BaseCommand):
    help = 'Re-categorize existing transactions using keyword matching rules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Re-categorize even transactions that already have a category',
        )

    def handle(self, *args, **options):
        categories = {c.name: c for c in Category.objects.filter(user=None)}
        qs = Transaction.objects.all() if options['overwrite'] else Transaction.objects.filter(category=None)
        count = 0
        for tx in qs.iterator():
            cat = categorize(tx.description, categories)
            if cat != tx.category:
                tx.category = cat
                tx.save(update_fields=['category'])
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Categorized {count} transactions.'))
