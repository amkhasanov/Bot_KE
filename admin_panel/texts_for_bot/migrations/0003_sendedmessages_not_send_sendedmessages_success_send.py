# Generated by Django 4.1.1 on 2022-10-23 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('texts_for_bot', '0002_plannedmessages_sendedmessages_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sendedmessages',
            name='not_send',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='sendedmessages',
            name='success_send',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
