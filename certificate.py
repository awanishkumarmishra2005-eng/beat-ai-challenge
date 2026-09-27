import os
import io
import qrcode
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

from flask import current_app, url_for
from extensions import db
from models import Certificate, Attempt

TITLES = {
    "champion": "BEAT AI CHAMPION",
    "survivor": "BEAT AI SURVIVOR",
    "draw": "BEAT AI CHALLENGE PARTICIPANT",
}


def generate_certificate(attempt: Attempt):
    """
    Creates the certificate DATABASE ROW instantly after a result is computed.
    Idempotent. Deliberately does NOT write a PDF to disk - Vercel's serverless
    filesystem is ephemeral, so any file written here would vanish before a user
    could download it. The PDF itself is rendered on-demand at download time by
    render_certificate_pdf() below, straight from these stored fields, and is
    byte-for-byte reproducible - nothing is lost by not caching it as a file.
    """
    if attempt.certificate:
        return attempt.certificate

    participant = attempt.participant
    # Tier decides certificate design: Advanced (₹30) = premium, Intermediate (₹20) = normal.
    certificate_type = "premium" if attempt.challenge_type == "advanced" else "normal"
    cert = Certificate(
        attempt_id=attempt.id,
        participant_name=participant.name,
        institution=participant.institution,
        challenge_type=attempt.challenge_type,
        certificate_type=certificate_type,
        human_score_pct=attempt.human_score_pct,
        ai_score_pct=attempt.ai_score_pct,
        result_category=attempt.result_category,
    )
    db.session.add(cert)
    db.session.commit()
    return cert


def render_certificate_pdf(cert: Certificate) -> io.BytesIO:
    """Renders the certificate PDF into memory and returns the buffer, ready to send_file()."""
    buf = io.BytesIO()
    _render_pdf(cert, buf)
    buf.seek(0)
    return buf


def _render_pdf(cert: Certificate, file_path_or_buffer):
    verify_url = url_for("public.verify_certificate", code=cert.certificate_code, _external=True)
    qr_img = qrcode.make(verify_url)
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    page_size = landscape(A4)
    c = canvas.Canvas(file_path_or_buffer, pagesize=page_size)
    w, h = page_size

    is_premium = cert.certificate_type == "premium"

    navy = HexColor("#101828")
    gold = HexColor("#D4AF37") if is_premium else HexColor("#8a6d1f")
    accent = HexColor("#FFFFFF")

    c.setFillColor(navy)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    if is_premium:
        # Premium: double gold border + corner badge, richer feel
        c.setStrokeColor(gold)
        c.setLineWidth(4)
        c.rect(0.8 * cm, 0.8 * cm, w - 1.6 * cm, h - 1.6 * cm, fill=0, stroke=1)
        c.setLineWidth(1)
        c.rect(1.1 * cm, 1.1 * cm, w - 2.2 * cm, h - 2.2 * cm, fill=0, stroke=1)
        c.setFillColor(gold)
        c.circle(w - 2.2 * cm, h - 2.2 * cm, 1.0 * cm, fill=1, stroke=0)
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w - 2.2 * cm, h - 2.35 * cm, "PREMIUM")
    else:
        c.setStrokeColor(gold)
        c.setLineWidth(2)
        c.rect(1 * cm, 1 * cm, w - 2 * cm, h - 2 * cm, fill=0, stroke=1)

    c.setFillColor(gold)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 2.3 * cm, "BEAT AI CHALLENGE")

    title = TITLES.get(cert.result_category, "BEAT AI CHALLENGE PARTICIPANT")
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(w / 2, h - 4 * cm, title)

    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 5.5 * cm, "This certifies that")

    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(gold)
    c.drawCentredString(w / 2, h - 7 * cm, cert.participant_name)

    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica", 13)
    subtitle = f"completed the {cert.challenge_type.upper()} challenge"
    if cert.institution:
        subtitle += f"  ·  {cert.institution}"
    c.drawCentredString(w / 2, h - 8.2 * cm, subtitle)

    c.setFont("Helvetica-Bold", 16)
    diff = cert.human_score_pct - cert.ai_score_pct
    stats = f"Human {cert.human_score_pct:.0f}%   ·   AI {cert.ai_score_pct:.0f}%   ·   Difference {diff:+.0f}%"
    c.drawCentredString(w / 2, h - 9.6 * cm, stats)

    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, 2.6 * cm, f"Certificate ID: {cert.certificate_code}")
    c.drawCentredString(w / 2, 2.1 * cm, cert.issued_at.strftime("%d %B %Y"))

    from reportlab.lib.utils import ImageReader
    qr_reader = ImageReader(qr_buf)
    qr_size = 2.4 * cm
    c.drawImage(qr_reader, w - 3.2 * cm, 1.4 * cm, qr_size, qr_size, mask="auto")

    c.save()
