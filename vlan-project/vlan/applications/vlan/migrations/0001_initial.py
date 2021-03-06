# Generated by Django 3.1.4 on 2020-12-19 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Interfaces',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='Interface Name')),
            ],
        ),
        migrations.CreateModel(
            name='Vlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='Vlan Name')),
                ('network', models.CharField(max_length=40, verbose_name='Network')),
                ('mask', models.CharField(max_length=40, verbose_name='Mask')),
                ('gateway', models.CharField(max_length=40, verbose_name='Gateway')),
                ('number', models.CharField(max_length=5, verbose_name='Gateway')),
                ('interfaces', models.ManyToManyField(blank=True, to='vlan.Interfaces')),
            ],
        ),
    ]
