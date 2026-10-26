from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_remove_historicalpost_image_remove_post_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalpost',
            name='gif',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='gif',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
