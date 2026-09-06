from django import forms


def _human_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


class UploadForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, folder, **kwargs):
        self.folder = folder
        super().__init__(*args, **kwargs)

    def clean_file(self):
        uploaded = self.cleaned_data["file"]

        if self.folder.max_file_size and uploaded.size > self.folder.max_file_size:
            raise forms.ValidationError(
                f"File is too large. Maximum allowed size is {_human_size(self.folder.max_file_size)}."
            )

        if self.folder.max_total_size:
            total_after = self.folder.current_total_size() + uploaded.size
            if total_after > self.folder.max_total_size:
                raise forms.ValidationError(
                    "This folder has reached its total storage limit. "
                    "Contact the folder owner."
                )

        return uploaded
