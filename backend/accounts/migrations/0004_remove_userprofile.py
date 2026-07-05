from django.db import migrations


class Migration(migrations.Migration):
    """Drop the accounts_userprofile table — roles are now managed in PRomop."""

    dependencies = [
        ("accounts", "0003_organization"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
