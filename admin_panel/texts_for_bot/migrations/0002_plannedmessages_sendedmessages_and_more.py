# Generated by Django 4.1.1 on 2022-10-23 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('texts_for_bot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlannedMessages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('planned_date', models.DateTimeField()),
                ('planned_msg_text', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='SendedMessages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('send_date', models.DateTimeField()),
            ],
        ),
        migrations.AlterField(
            model_name='botmessage',
            name='description',
            field=models.TextField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='buttontext',
            name='message_after_click',
            field=models.TextField(max_length=1000),
        ),
    ]
