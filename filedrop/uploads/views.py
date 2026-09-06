from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import UploadForm
from .models import Folder, UploadedFile


def upload_view(request, token):
    folder = get_object_or_404(Folder, public_token=token, is_active=True)

    if request.method == "POST":
        # Locks the folder row for the duration of the check-then-create so
        # concurrent uploads to the same folder can't both pass the
        # max_total_size check against the same stale total (on backends
        # that support SELECT ... FOR UPDATE; SQLite ignores it).
        with transaction.atomic():
            locked_folder = Folder.objects.select_for_update().get(pk=folder.pk)
            form = UploadForm(request.POST, request.FILES, folder=locked_folder)
            if form.is_valid():
                uploaded_file = form.cleaned_data["file"]
                UploadedFile.objects.create(
                    folder=locked_folder,
                    file=uploaded_file,
                    original_filename=uploaded_file.name,
                    content_type=uploaded_file.content_type or "",
                    size=uploaded_file.size,
                    uploader_ip=request.META.get("REMOTE_ADDR"),
                )
                success_url = reverse(
                    "uploads:upload_success", args=[folder.public_token]
                )
                return redirect(
                    f"{success_url}?{urlencode({'file': uploaded_file.name})}"
                )
    else:
        form = UploadForm(folder=folder)

    return render(
        request,
        "uploads/upload_form.html",
        {"folder": folder, "form": form},
    )


def upload_success_view(request, token):
    folder = get_object_or_404(Folder, public_token=token)
    filename = request.GET.get("file", "")
    return render(
        request,
        "uploads/upload_success.html",
        {"folder": folder, "filename": filename},
    )


@staff_member_required
def download_view(request, pk):
    uploaded_file = get_object_or_404(UploadedFile, pk=pk)
    return FileResponse(
        uploaded_file.file.open("rb"),
        as_attachment=True,
        filename=uploaded_file.original_filename,
    )
