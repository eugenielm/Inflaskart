# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-11 19:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grocerystore', '0004_auto_20170111_1101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productsubcategory',
            options={'ordering': ['top_category', 'sub_category_1']},
        ),
    ]