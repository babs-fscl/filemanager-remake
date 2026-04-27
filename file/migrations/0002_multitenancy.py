from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_multitenancy'),
        ('file', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='authentication.organization'),
        ),
        migrations.AddField(
            model_name='document',
            name='shared_with',
            field=models.ManyToManyField(blank=True, related_name='shared_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='authentication.organization'),
        ),
        migrations.AddField(
            model_name='project',
            name='shared_with',
            field=models.ManyToManyField(blank=True, related_name='shared_projects', to=settings.AUTH_USER_MODEL),
        ),
    ]
