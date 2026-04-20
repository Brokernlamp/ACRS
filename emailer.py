import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def send_report(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    client_name: str,
    pdf_bytes: bytes,
) -> tuple[bool, str]:
    if not all([sender_email, sender_password, recipient_email]):
        return False, "Sender email, password, and recipient email are required."
    if not _EMAIL_RE.match(sender_email):
        return False, "Invalid sender email address."
    if not _EMAIL_RE.match(recipient_email):
        return False, "Invalid recipient email address."
    if not pdf_bytes:
        return False, "No PDF content to attach."

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Campaign Performance Report — {client_name or 'Client'}"

    msg.attach(MIMEText(
        f"Hi,\n\nPlease find attached the campaign performance report for {client_name or 'your account'}.\n\nBest regards,\nMarketing Analytics Team",
        "plain"
    ))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="campaign_report.pdf"')
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True, f"Report sent successfully to {recipient_email}."
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Use a Gmail App Password (not your account password)."
    except smtplib.SMTPRecipientsRefused:
        return False, f"Recipient address '{recipient_email}' was refused by the server."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except OSError as e:
        return False, f"Network error sending email: {str(e)}"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"
