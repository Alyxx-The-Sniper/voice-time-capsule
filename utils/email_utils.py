import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_SENDER")       # Your Gmail address
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail App Password

def send_confirmation_email(recipient_email: str, token: str, delivery_date: str):
    subject = "✅ Your Time Capsule Is Sealed"
    access_url = f"https://voice-time-capsule.onrender.com/view/{token}"  # Change to your real domain

    html = f"""
        <div style="font-family: Arial, sans-serif; background: #f6f8fa; padding: 18px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); max-width: 420px; margin: 24px auto;">
        <p>Your message has been delivered, but your future self can’t send messages to the past.</p> 
        <p>You’ll receive a response on <b>{delivery_date}</b>.</p>
        <p style="margin-top: 18px;">Can’t wait that long? Okay, I’ll time travel for you and retrieve the message instantly! 😄<br>
        Here you go—a voice time capsule sealed just for you:</p>
        <a href="{access_url}" style="color: #2366d1; text-decoration: underline;">View future response</a>

        <p style="margin-top: 18px;">Note: This is a demo only.The link is supposed to be available on your chosen future date.</p>

        </div>

    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"📧 Confirmation sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        

    
def send_delivery_email(recipient_email: str, token: str):
    subject = "📬 A message from your past self"
    access_url = f"https://voice-time-capsule.onrender.com/view/{token}"  # Replace with your domain

    html = f"""
    <html>
        <body>
            <h2>You've got a message from your past self 🎁</h2>
            <p>Open your sealed time capsule message:</p>
            <a href="{access_url}">{access_url}</a>
            <br><br>
            <small>This message was scheduled to be delivered today.</small>
        </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"📧 Delivery email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Delivery email failed: {e}")

