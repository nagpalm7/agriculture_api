# Generated by Django 2.2.4 on 2019-09-24 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_adoreport_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adoreport',
            name='action',
            field=models.CharField(choices=[('chalaan', 'Challan'), ('FIR', 'FIR')], max_length=50),
        ),
    ]
