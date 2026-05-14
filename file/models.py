import uuid
from django.db import models
from django.conf import settings


class Document(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    organization = models.ForeignKey('authentication.Organization', on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_documents', blank=True)
    file = models.FileField(upload_to='uploads/',)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    is_shared = models.BooleanField(default=False)
    type = models.CharField(max_length=7, null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or "Unnamed Document"


class ChatMessage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_bot_response = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class Project(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey('authentication.Organization', on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared_projects', blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_sitemap = models.BooleanField(default=False)
    is_url = models.BooleanField(default=False)
    is_youtube = models.BooleanField(default=False)
    is_multiple = models.BooleanField(default=False)
    content = models.TextField(blank=True, null=True)
    scope = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
