# Generated by Django 5.2 on 2025-05-12 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_bloodevent_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodevent',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=10),
        ),
    ]
