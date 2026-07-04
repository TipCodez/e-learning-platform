from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".zip", ".jpg", ".jpeg", ".png", ".webp"}
DOCUMENT_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "application/zip",
    "application/x-zip-compressed",
    "image/jpeg",
    "image/png",
    "image/webp",
}
PDF_CONTENT_TYPES = {"application/pdf"}


def _max_size(name, default_mb):
    return int(getattr(settings, name, default_mb * 1024 * 1024))


def _extension(upload):
    return Path(upload.name or "").suffix.lower()


def _content_type(upload):
    return getattr(upload, "content_type", "") or ""


def _validate_upload(upload, *, extensions, content_types, max_size, label):
    if upload.size and upload.size > max_size:
        raise ValidationError(f"{label} must be {max_size // (1024 * 1024)}MB or smaller.", code="file_too_large")
    if _extension(upload) not in extensions:
        allowed = ", ".join(sorted(ext.lstrip(".") for ext in extensions))
        raise ValidationError(f"Unsupported {label.lower()} type. Allowed: {allowed}.", code="unsupported_file_type")
    content_type = _content_type(upload)
    if content_type and content_type not in content_types:
        raise ValidationError(f"Unsupported {label.lower()} content type.", code="unsupported_content_type")


def validate_image_upload(upload):
    _validate_upload(
        upload,
        extensions=IMAGE_EXTENSIONS,
        content_types=IMAGE_CONTENT_TYPES,
        max_size=_max_size("MAX_IMAGE_UPLOAD_SIZE", 5),
        label="Image upload",
    )


def validate_document_upload(upload):
    _validate_upload(
        upload,
        extensions=DOCUMENT_EXTENSIONS,
        content_types=DOCUMENT_CONTENT_TYPES,
        max_size=_max_size("MAX_DOCUMENT_UPLOAD_SIZE", 20),
        label="Document upload",
    )


def validate_pdf_upload(upload):
    _validate_upload(
        upload,
        extensions={".pdf"},
        content_types=PDF_CONTENT_TYPES,
        max_size=_max_size("MAX_DOCUMENT_UPLOAD_SIZE", 20),
        label="PDF upload",
    )
