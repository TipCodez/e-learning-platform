from io import BytesIO

import qrcode
from django.core.files.base import ContentFile
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def build_absolute_verification_url(request, certificate):
    path = reverse("certificates:verify", kwargs={"certificate_id": certificate.certificate_id})
    return request.build_absolute_uri(path)


def generate_qr_code(certificate, verification_url):
    image = qrcode.make(verification_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    certificate.qr_code.save(
        f"certificate-{certificate.certificate_id}.png",
        ContentFile(buffer.getvalue()),
        save=False,
    )


def generate_certificate_pdf(certificate, verification_url):
    buffer = BytesIO()
    page_size = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    pdf.setFillColor(colors.HexColor("#0b1f3a"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    margin = 0.55 * inch
    pdf.setStrokeColor(colors.HexColor("#f5b942"))
    pdf.setLineWidth(4)
    pdf.rect(margin, margin, width - margin * 2, height - margin * 2, fill=0, stroke=1)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 1.35 * inch, "Acadeval")
    pdf.setFillColor(colors.HexColor("#f5b942"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 2.0 * inch, "Certificate of Completion")

    student_name = certificate.student.get_full_name() or certificate.student.username
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 2.55 * inch, "This certifies that")
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 3.15 * inch, student_name)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 3.65 * inch, "has successfully completed")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 4.22 * inch, certificate.course.title)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 4.82 * inch, f"Instructor: {certificate.instructor_name}")
    pdf.drawCentredString(width / 2, height - 5.18 * inch, f"Issue date: {certificate.issue_date:%B %d, %Y}")

    pdf.setFillColor(colors.HexColor("#d1d5db"))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(1.1 * inch, 0.95 * inch, f"Certificate ID: {certificate.certificate_id}")
    pdf.drawString(1.1 * inch, 0.72 * inch, f"Verify: {verification_url}")
    if certificate.qr_code:
        pdf.drawImage(certificate.qr_code.path, width - 1.85 * inch, 0.72 * inch, width=1.0 * inch, height=1.0 * inch)

    pdf.showPage()
    pdf.save()
    certificate.pdf_file.save(
        f"certificate-{certificate.certificate_id}.pdf",
        ContentFile(buffer.getvalue()),
        save=False,
    )


def ensure_certificate_assets(request, certificate):
    verification_url = build_absolute_verification_url(request, certificate)
    if not certificate.qr_code:
        generate_qr_code(certificate, verification_url)
    if not certificate.pdf_file:
        generate_certificate_pdf(certificate, verification_url)
    certificate.save(update_fields=["qr_code", "pdf_file"])
    return certificate
