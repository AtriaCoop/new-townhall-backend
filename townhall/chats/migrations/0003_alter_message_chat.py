# Generated by Django 5.0.6 on 2025-05-30 11:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_rename_chat_id_message_chat_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='chat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chats.chat'),
        ),
    ]
