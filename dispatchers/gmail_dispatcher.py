"""
Gmail Dispatcher for Daily Current Affairs Agent.
Sends styled HTML email digests via Gmail SMTP (App Password).
"""

import logging
import smtplib
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GMAIL_APP_PASSWORD, GMAIL_TO, GMAIL_USER

logger = logging.getLogger(__name__)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def test_gmail_connection(user: Optional[str] = None, app_password: Optional[str] = None) -> bool:
    """Tests SMTP connection and authentication to Gmail."""
    username = (user or GMAIL_USER).strip()
    password = (app_password or GMAIL_APP_PASSWORD).strip().replace(" ", "")

    if not username or not password:
        logger.error("Missing GMAIL_USER or GMAIL_APP_PASSWORD.")
        return False

    try:
        logger.info(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        logger.info(f"Authenticating as {username}...")
        server.login(username, password)
        server.quit()
        logger.info("Gmail SMTP authentication successful!")
        return True
    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(
            f"Gmail Authentication Failed: {auth_err}. "
            "Please ensure you are using a 16-character Google 'App Password' "
            "(Google Account > Security > 2-Step Verification > App Passwords) rather than your standard password."
        )
        return False
    except Exception as e:
        logger.error(f"Error connecting to Gmail SMTP: {e}")
        return False


def dispatch_gmail(
    html_content: str,
    plain_text: str,
    subject: str,
    to_emails: Optional[List[str]] = None,
    user: Optional[str] = None,
    app_password: Optional[str] = None,
    attachments: Optional[List[Tuple[str, bytes]]] = None,
) -> bool:
    """
    Sends the HTML current affairs digest with plain text alternative to configured recipients.
    attachments: optional list of (filename, file_bytes) tuples, e.g. PDF attachments.
    """
    username = (user or GMAIL_USER).strip()
    password = (app_password or GMAIL_APP_PASSWORD).strip().replace(" ", "")
    recipients = to_emails or GMAIL_TO

    if not username or not password:
        logger.error("Cannot dispatch email: GMAIL_USER or GMAIL_APP_PASSWORD not configured in .env")
        return False

    if not recipients:
        logger.error("Cannot dispatch email: No recipients specified in GMAIL_TO.")
        return False

    try:
        # If there are file attachments, the message needs a "mixed" outer container
        # holding an "alternative" part (plain+html) plus each attachment as a sibling.
        # Without attachments, keep the original simple "alternative" structure.
        if attachments:
            msg = MIMEMultipart("mixed")
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
            alt_part.attach(MIMEText(html_content, "html", "utf-8"))
            msg.attach(alt_part)

            for filename, file_bytes in attachments:
                if not file_bytes:
                    continue
                part = MIMEApplication(file_bytes, _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)
        else:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        msg["Subject"] = subject
        msg["From"] = formataddr(("Daily Current Affairs Agent", username))
        msg["To"] = ", ".join(recipients)

        logger.info(f"Sending email to {len(recipients)} recipient(s): {', '.join(recipients)}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.sendmail(username, recipients, msg.as_string())
        server.quit()

        logger.info("Email digest dispatched successfully via Gmail SMTP!")
        return True

    except Exception as e:
        logger.error(f"Failed to dispatch Gmail digest: {e}")
        return False


if __name__ == "__main__":
    print("Testing Gmail credentials...")
    test_gmail_connection()
