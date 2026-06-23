from .models import Category
from .categorizer import default_categories


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
