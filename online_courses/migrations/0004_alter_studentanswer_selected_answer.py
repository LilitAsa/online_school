# Generated by Django 5.1.6 on 2025-03-07 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online_courses', '0003_quiz_course'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentanswer',
            name='selected_answer',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
