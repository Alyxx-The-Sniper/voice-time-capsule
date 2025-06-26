from email.mime.base import MIMEBase
from email import encoders
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_SENDER")       # Your Gmail address
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail App Password

def send_audio_email(recipient_email: str, audio_url: str):
    subject = "🔊 Your Voice Time Capsule Audio Copy"
    html = """
        <div style="font-family: Arial, sans-serif;">
            <h3>Here's your copy as requested!</h3>
            <p>Your future self voice message is attached as an audio file. Thank you for using Voice Time Capsule!</p>
            <p><small>If you have trouble playing the file, reply to this email for help.</small></p>
        </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg.attach(MIMEText(html, "html"))

    # Download the audio file from S3 or your storage URL
    audio_response = requests.get(audio_url)
    if audio_response.status_code == 200:
        part = MIMEBase('audio', 'mp3')
        part.set_payload(audio_response.content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="your_voice_capsule.mp3"'
        )
        msg.attach(part)
    else:
        print("❌ Could not download audio file to attach.")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"📧 Audio sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send audio email: {e}")
