import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Send an email using SMTP. Returns True if successful, False otherwise.
    """
    try:
        # Create the message
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        # Print to terminal as well
        print(f"\n[EMAIL SENT] To: {recipient}\nSubject: {subject}\nBody:\n{body}\n")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
