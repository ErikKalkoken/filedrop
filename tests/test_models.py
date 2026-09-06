import os

from django.core.files.uploadedfile import SimpleUploadedFile

from filedrop.uploads.models import Folder, UploadedFile

from .base import MediaTestCase


class FolderTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.folder = Folder.objects.create(name="Test Folder")

    def test_current_total_size_is_zero_for_empty_folder(self):
        self.assertEqual(self.folder.current_total_size(), 0)

    def test_current_total_size_sums_files(self):
        UploadedFile.objects.create(
            folder=self.folder,
            file=SimpleUploadedFile("a.txt", b"x" * 10),
            original_filename="a.txt",
            size=10,
        )
        UploadedFile.objects.create(
            folder=self.folder,
            file=SimpleUploadedFile("b.txt", b"x" * 20),
            original_filename="b.txt",
            size=20,
        )
        self.assertEqual(self.folder.current_total_size(), 30)

    def test_get_public_url_contains_token(self):
        self.assertEqual(
            self.folder.get_public_url(), f"/f/{self.folder.public_token}/"
        )

    def test_description_html_renders_markdown(self):
        self.folder.description = "**bold** and [a link](https://example.com)"
        self.assertEqual(
            self.folder.description_html(),
            "<p><strong>bold</strong> and "
            '<a href="https://example.com" rel="noopener noreferrer">a link</a></p>',
        )

    def test_description_html_empty_when_no_description(self):
        self.assertEqual(self.folder.description, "")
        self.assertEqual(self.folder.description_html(), "")

    def test_description_html_strips_script_tags(self):
        self.folder.description = "Hello <script>alert(document.cookie)</script> world"
        self.assertNotIn("<script", self.folder.description_html())

    def test_description_html_strips_event_handler_attributes(self):
        self.folder.description = '<img src=x onerror="alert(1)">'
        self.assertNotIn("onerror", self.folder.description_html())


class UploadedFileDeletionTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.folder = Folder.objects.create(name="Test Folder")
        self.uploaded_file = UploadedFile.objects.create(
            folder=self.folder,
            file=SimpleUploadedFile("a.txt", b"x" * 10),
            original_filename="a.txt",
            size=10,
        )
        self.file_path = self.uploaded_file.file.path

    def test_deleting_uploaded_file_removes_it_from_disk(self):
        self.assertTrue(os.path.exists(self.file_path))
        self.uploaded_file.delete()
        self.assertFalse(os.path.exists(self.file_path))

    def test_deleting_folder_removes_its_files_from_disk(self):
        self.assertTrue(os.path.exists(self.file_path))
        self.folder.delete()
        self.assertFalse(os.path.exists(self.file_path))
