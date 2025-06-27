import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, UTC
import config
from typing import Optional, Literal

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
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC

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

async def send_resource_alert(
    website_url: str,
    host: str,
    resource_type: Literal["CPU", "RAM", "Disk"],
    usage: float,
    threshold: float = 90.0
) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USERNAME
        msg['To'] = config.NOTIFICATION_EMAIL
        msg['Subject'] = f"Server Resource Alert - {host}"

        body = f"""
        Server Resource Alert

        Website: {website_url}
        Server: {host}
        Alert: {resource_type} usage has exceeded {threshold}%
        Current Usage: {usage:.1f}%
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC

        This is an automated notification from your Website Checker application.
        Please check your server resources to prevent potential issues.
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send resource alert: {str(e)}")
        return False 