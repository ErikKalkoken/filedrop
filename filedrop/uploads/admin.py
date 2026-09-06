from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Folder, UploadedFile


class UploadedFileInline(admin.TabularInline):
    model = UploadedFile
    extra = 0
    fields = ("original_filename", "size", "uploaded_at", "download_link")
    readonly_fields = ("original_filename", "size", "uploaded_at", "download_link")
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return False

    def download_link(self, obj):
        if not obj.pk:
            return ""
        url = reverse("uploads:download", args=[obj.pk])
        return format_html('<a href="{}">Download</a>', url)

    download_link.short_description = "Download"


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "file_count",
        "current_total_size_display",
        "created_by",
        "created_at",
    )
    readonly_fields = (
        "public_url_display",
        "current_total_size_display",
        "created_by",
        "created_at",
    )
    fields = (
        "name",
        "description",
        "is_active",
        "max_file_size",
        "max_total_size",
        "public_url_display",
        "current_total_size_display",
        "created_by",
        "created_at",
    )
    inlines = [UploadedFileInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(file_count=Count("files"))

    def file_count(self, obj):
        return obj.file_count

    file_count.short_description = "Files"
    file_count.admin_order_field = "file_count"

    def public_url_display(self, obj):
        if not obj.pk:
            return "(save folder to generate link)"
        url = obj.get_public_url()
        return format_html('<a href="{0}">{0}</a>', url)

    public_url_display.short_description = "Public upload link"

    def current_total_size_display(self, obj):
        if not obj.pk:
            return "0"
        return obj.current_total_size()

    current_total_size_display.short_description = "Current total size (bytes)"


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "folder",
        "size",
        "uploaded_at",
        "download_link",
    )
    list_filter = ("folder",)
    search_fields = ("original_filename",)
    readonly_fields = (
        "folder",
        "download_link",
        "original_filename",
        "content_type",
        "size",
        "uploaded_at",
        "uploader_ip",
    )

    def has_add_permission(self, request):
        return False

    def download_link(self, obj):
        if not obj.pk:
            return ""
        url = reverse("uploads:download", args=[obj.pk])
        return format_html('<a href="{}">Download</a>', url)

    download_link.short_description = "Download"
