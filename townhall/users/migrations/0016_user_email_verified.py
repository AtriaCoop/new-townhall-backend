from django.db import migrations, models


def set_existing_users_verified(apps, schema_editor):
    """Mark all existing users as email-verified so they aren't locked out."""
    User = apps.get_model("users", "User")
    User.objects.all().update(email_verified=True)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0015_historicaluser_failed_login_attempts_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="historicaluser",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            set_existing_users_verified,
            migrations.RunPython.noop,
        ),
    ]
