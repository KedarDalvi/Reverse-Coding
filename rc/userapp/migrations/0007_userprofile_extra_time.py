# Generated by Django 3.1.1 on 2020-10-19 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userapp', '0006_userprofile_hot_or_cold'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='extra_time',
            field=models.IntegerField(default=0),
        ),
    ]