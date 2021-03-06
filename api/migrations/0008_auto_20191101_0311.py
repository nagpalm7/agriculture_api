# Generated by Django 2.2.4 on 2019-10-31 21:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20191031_1317'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=200)),
            ],
            options={
                'get_latest_by': 'version',
            },
        ),
        migrations.AddField(
            model_name='adoreport',
            name='fire',
            field=models.CharField(blank=True, choices=[('fire', 'Fire'), ('nofire', 'No Fire')], max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='adoreport',
            name='report_latitude',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='adoreport',
            name='report_longitude',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='ado',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True, validators=[django.core.validators.RegexValidator(message='Email not valid', regex='^\\w+([\\.-]?\\w+)*@\\w+([\\.-]?\\w+)*(\\.\\w{2,3})+$')]),
        ),
        migrations.AlterField(
            model_name='ado',
            name='number',
            field=models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.RegexValidator(message='Phone number not valid', regex='^(0/91)?[6-9][0-9]{9}')]),
        ),
        migrations.AlterField(
            model_name='dc',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True, validators=[django.core.validators.RegexValidator(message='Email not valid', regex='^\\w+([\\.-]?\\w+)*@\\w+([\\.-]?\\w+)*(\\.\\w{2,3})+$')]),
        ),
        migrations.AlterField(
            model_name='dda',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True, validators=[django.core.validators.RegexValidator(message='Email not valid', regex='^\\w+([\\.-]?\\w+)*@\\w+([\\.-]?\\w+)*(\\.\\w{2,3})+$')]),
        ),
        migrations.AlterField(
            model_name='dda',
            name='number',
            field=models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.RegexValidator(message='Phone number not valid', regex='^(0/91)?[6-9][0-9]{9}')]),
        ),
        migrations.AlterField(
            model_name='sp',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True, validators=[django.core.validators.RegexValidator(message='Email not valid', regex='^\\w+([\\.-]?\\w+)*@\\w+([\\.-]?\\w+)*(\\.\\w{2,3})+$')]),
        ),
    ]
