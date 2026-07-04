from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from acadeval.validators import validate_document_upload, validate_image_upload, validate_pdf_upload


class UploadValidatorTests(SimpleTestCase):
    def test_image_validator_rejects_non_image_content_type(self):
        upload = SimpleUploadedFile("avatar.png", b"not-image", content_type="text/html")
        with self.assertRaises(ValidationError):
            validate_image_upload(upload)

    def test_image_validator_rejects_unsupported_extension(self):
        upload = SimpleUploadedFile("avatar.svg", b"<svg></svg>", content_type="image/svg+xml")
        with self.assertRaises(ValidationError):
            validate_image_upload(upload)

    @override_settings(MAX_DOCUMENT_UPLOAD_SIZE=4)
    def test_document_validator_rejects_oversized_upload(self):
        upload = SimpleUploadedFile("notes.pdf", b"12345", content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_document_upload(upload)

    def test_document_validator_accepts_common_learning_file(self):
        upload = SimpleUploadedFile("assignment.docx", b"document", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        validate_document_upload(upload)

    def test_pdf_validator_rejects_non_pdf_certificate_file(self):
        upload = SimpleUploadedFile("certificate.docx", b"document", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with self.assertRaises(ValidationError):
            validate_pdf_upload(upload)
