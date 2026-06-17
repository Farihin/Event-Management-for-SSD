"""
Shared, reusable file-upload security pipeline for image uploads
(event banners and user avatars).

Defense-in-depth — each layer is individually bypassable, but together they
are strong (File Upload Security requirement):
    1. extension allowlist          (FileExtensionValidator)
    2. size cap                     (validate_image_filesize)
    3. declared content-type check  (validate_image_content_type)  -- not trusted alone
    4. authoritative content sniff  (validate_real_image, via Pillow)
    5. UUID rename on storage       (UUIDUploadTo)

Pillow is used for content sniffing rather than python-magic, because libmagic
is unreliable to install on Windows and Pillow is already a Django ImageField
dependency.
"""

import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from PIL import Image

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB

# Layer 1: extension allowlist (whitelist, never a blocklist).
validate_image_extension = FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)


def validate_image_filesize(f):
    """Layer 2: restrict upload size."""
    if f.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            f"Image too large ({f.size // 1024} KB). Maximum is "
            f"{MAX_IMAGE_BYTES // 1024 // 1024} MB."
        )


def validate_image_content_type(f):
    """Layer 3: reject obviously-wrong declared content types.

    content_type is client-supplied, so this is a cheap pre-filter only; the real
    check is validate_real_image below.
    """
    content_type = getattr(f, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("Unsupported file type.")


def validate_real_image(f):
    """Layer 4 (authoritative): the bytes must actually parse as an allowed image.

    Catches renamed/forged files (e.g. a .php or .exe renamed to .jpg) and
    truncated/corrupt uploads. Image.verify() consumes the file object, so we
    rewind it afterwards for Django to save it.
    """
    try:
        f.seek(0)
        image = Image.open(f)
        image.verify()
        if image.format not in ALLOWED_PIL_FORMATS:
            raise ValidationError("Image format not allowed.")
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("File is not a valid image.")
    finally:
        f.seek(0)


# Convenience: the full validator list to attach to an ImageField.
IMAGE_UPLOAD_VALIDATORS = [
    validate_image_extension,
    validate_image_filesize,
    validate_image_content_type,
    validate_real_image,
]


@deconstructible
class UUIDUploadTo:
    """Layer 5: store uploads as ``<subdir>/<uuid4>.<ext>``.

    A random UUID filename defeats path traversal in the original filename,
    prevents overwrite collisions, and stops an attacker from controlling the
    stored name/extension. ``@deconstructible`` lets Django serialize this into
    migrations.
    """

    def __init__(self, subdir):
        self.subdir = subdir.strip("/")

    def __call__(self, instance, filename):
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            ext = "jpg"  # belt-and-suspenders; real extension already validated
        return f"{self.subdir}/{uuid.uuid4().hex}.{ext}"
