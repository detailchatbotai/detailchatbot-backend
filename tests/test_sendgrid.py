import ssl
import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings

# (only for local dev if you still see SSL errors)
ssl._create_default_https_context = ssl._create_unverified_context

async def send_test_email():
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    msg = Mail(
        from_email=settings.SENDGRID_SENDER,
        to_emails=settings.SENDGRID_SENDER,
        subject="SendGrid Test",
        plain_text_content="✅ Your SendGrid key is working!"
    )
    response = sg.send(msg)
    print("Status code:", response.status_code)  # Expect 202

if __name__ == "__main__":
    asyncio.run(send_test_email())
