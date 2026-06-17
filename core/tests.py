"""
Unit tests for the file-upload security pipeline.
"""

from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .validators import (
    MAX_IMAGE_BYTES,
    UUIDUploadTo,
    validate_image_extension,
    validate_image_filesize,
    validate_real_image,
)


def real_png(name="image.png"):
    buf = BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


class UploadValidatorTests(TestCase):
    def test_real_image_passes(self):
        validate_real_image(real_png())  # should not raise

    def test_forged_image_rejected(self):
        # A PHP payload renamed to .png — passes extension but fails content sniff.
        evil = SimpleUploadedFile("shell.png", b"<?php system($_GET[c]); ?>",
                                  content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_real_image(evil)

    def test_bad_extension_rejected(self):
        evil = SimpleUploadedFile("shell.php", b"data", content_type="application/x-php")
        with self.assertRaises(ValidationError):
            validate_image_extension(evil)

    def test_oversize_rejected(self):
        f = real_png()
        f.size = MAX_IMAGE_BYTES + 1
        with self.assertRaises(ValidationError):
            validate_image_filesize(f)

    def test_uuid_upload_renames_file(self):
        upload_to = UUIDUploadTo("avatars")
        path = upload_to(None, "My Original Photo.PNG")
        self.assertTrue(path.startswith("avatars/"))
        self.assertTrue(path.endswith(".png"))
        self.assertNotIn("My Original Photo", path)
