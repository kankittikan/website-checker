import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config

async def send_notification_email(website_url: str, status: bool) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USERNAME
        msg['To'] = config.NOTIFICATION_EMAIL
        msg['Subject'] = f"Website Status Alert - {website_url}"

        status_text = "DOWN" if not status else "UP"
        body = f"""
        Website Status Alert

        URL: {website_url}
        Status: {status_text}
        Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

        This is an automated notification from your Website Checker application.
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        return False 