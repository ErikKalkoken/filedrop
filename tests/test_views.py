from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from filedrop.uploads.models import Folder, UploadedFile

from .base import MediaTestCase


class UploadViewTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.folder = Folder.objects.create(
            name="Test Folder", max_file_size=1024, max_total_size=2048
        )

    def test_upload_form_renders(self):
        response = self.client.get(self.folder.get_public_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Folder", response.content)

    def test_upload_form_shows_description_as_html(self):
        self.folder.description = "**important**"
        self.folder.save()
        response = self.client.get(self.folder.get_public_url())
        self.assertIn(b"<strong>important</strong>", response.content)

    def test_valid_upload_creates_file_and_redirects_to_success_page(self):
        upload = SimpleUploadedFile("hello.txt", b"hello world")
        response = self.client.post(self.folder.get_public_url(), {"file": upload})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("uploads:upload_success", args=[self.folder.public_token])
            + "?file=hello.txt",
        )
        uploaded = UploadedFile.objects.get(folder=self.folder)
        self.assertEqual(uploaded.original_filename, "hello.txt")
        self.assertEqual(uploaded.size, len(b"hello world"))

    def test_success_page_shows_filename(self):
        upload = SimpleUploadedFile("hello.txt", b"hello world")
        response = self.client.post(
            self.folder.get_public_url(), {"file": upload}, follow=True
        )

        self.assertIn(b"hello.txt", response.content)
        self.assertIn(b"uploaded successfully", response.content)

    def test_upload_rejects_file_over_max_file_size(self):
        too_big = SimpleUploadedFile("big.bin", b"x" * 2000)
        response = self.client.post(self.folder.get_public_url(), {"file": too_big})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"too large", response.content)
        self.assertFalse(UploadedFile.objects.filter(folder=self.folder).exists())

    def test_upload_rejects_when_total_size_would_be_exceeded(self):
        self.client.post(
            self.folder.get_public_url(),
            {"file": SimpleUploadedFile("a.bin", b"x" * 1000)},
        )
        self.client.post(
            self.folder.get_public_url(),
            {"file": SimpleUploadedFile("b.bin", b"x" * 1000)},
        )

        response = self.client.post(
            self.folder.get_public_url(),
            {"file": SimpleUploadedFile("c.bin", b"x" * 1000)},
        )

        self.assertIn(b"total storage limit", response.content)
        self.assertEqual(UploadedFile.objects.filter(folder=self.folder).count(), 2)

    def test_inactive_folder_returns_404(self):
        inactive = Folder.objects.create(name="Inactive", is_active=False)
        response = self.client.get(inactive.get_public_url())
        self.assertEqual(response.status_code, 404)

    def test_unknown_token_returns_404(self):
        response = self.client.get(
            reverse("uploads:upload", args=["00000000-0000-0000-0000-000000000000"])
        )
        self.assertEqual(response.status_code, 404)


class DownloadViewTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.folder = Folder.objects.create(name="Test Folder")
        upload = SimpleUploadedFile("secret.txt", b"data")
        self.client.post(self.folder.get_public_url(), {"file": upload})
        self.uploaded_file = UploadedFile.objects.get(folder=self.folder)

    def test_download_redirects_anonymous_to_admin_login(self):
        response = self.client.get(
            reverse("uploads:download", args=[self.uploaded_file.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))

    def test_download_allowed_for_staff(self):
        staff_user = get_user_model().objects.create_user(
            username="staff", password="pw", is_staff=True
        )
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse("uploads:download", args=[self.uploaded_file.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("secret.txt", response["Content-Disposition"])
