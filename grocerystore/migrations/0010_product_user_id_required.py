# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-12 02:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grocerystore', '0009_auto_20170111_1313'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='user_id_required',
            field=models.BooleanField(default=False),
        ),
    ]