import tempfile

from django.test import TestCase, override_settings


class MediaTestCase(TestCase):
    """Points MEDIA_ROOT at a scratch directory so uploads never touch the real media/ folder."""

    def setUp(self):
        super().setUp()
        tmp_media = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_media.cleanup)
        override = override_settings(MEDIA_ROOT=tmp_media.name)
        override.enable()
        self.addCleanup(override.disable)
