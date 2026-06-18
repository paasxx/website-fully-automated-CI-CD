from django.db import migrations

DEFAULTS = [
    ("Alimentação", "#ef5350"),
    ("Transporte",  "#42a5f5"),
    ("Saúde",       "#66bb6a"),
    ("Lazer",       "#ab47bc"),
    ("Compras",     "#ffa726"),
    ("Moradia",     "#78909c"),
    ("Serviços",    "#26c6da"),
    ("Educação",    "#8d6e63"),
    ("Viagem",      "#5c6bc0"),
    ("Outros",      "#bdbdbd"),
]


def seed(apps, schema_editor):
    Category = apps.get_model("finances", "Category")
    for name, color in DEFAULTS:
        Category.objects.get_or_create(name=name, user=None, defaults={"color": color})


def unseed(apps, schema_editor):
    Category = apps.get_model("finances", "Category")
    names = [name for name, _ in DEFAULTS]
    Category.objects.filter(name__in=names, user=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
