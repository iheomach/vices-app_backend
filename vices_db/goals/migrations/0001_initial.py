# Generated by Django 4.2 on 2025-06-23 02:26

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('type', models.CharField(choices=[('cannabis', 'Cannabis'), ('alcohol', 'Alcohol'), ('wellness', 'Wellness'), ('both', 'Both'), ('none', 'None')], max_length=20)),
                ('duration', models.CharField(max_length=20)),
                ('progress', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed'), ('abandoned', 'Abandoned')], default='active', max_length=20)),
                ('benefits', models.JSONField(default=list)),
                ('challenge', models.CharField(max_length=100)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AIInsight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('pattern', 'Pattern'), ('health', 'Health'), ('achievement', 'Achievement'), ('optimization', 'Optimization'), ('trend', 'Trend')], max_length=20)),
                ('title', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('severity', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('success', 'Success'), ('tip', 'Tip')], max_length=20)),
                ('actionable', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_insights', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
