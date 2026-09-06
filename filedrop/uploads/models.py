import uuid

import markdown
import nh3
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.safestring import mark_safe


def upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    random_name = uuid.uuid4().hex
    if ext:
        random_name = f"{random_name}.{ext}"
    return f"folder_{instance.folder_id}/{random_name}"


class Folder(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        help_text="Shown to users under the folder name on the upload page. Supports Markdown.",
    )
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    max_file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Max size per file, in bytes. Blank = no limit.",
    )
    max_total_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Max total size of all files in this folder, in bytes. Blank = no limit.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Uncheck to stop accepting new uploads."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def current_total_size(self):
        return self.files.aggregate(total=models.Sum("size"))["total"] or 0

    def get_public_url(self):
        return reverse("uploads:upload", args=[self.public_token])

    def description_html(self):
        html = markdown.markdown(self.description)
        return mark_safe(nh3.clean(html))


class UploadedFile(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploader_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename


@receiver(post_delete, sender=UploadedFile)
def delete_file_from_disk(sender, instance, **kwargs):
    instance.file.delete(save=False)
