import os
import logging
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
from core.open_api import model

logger = logging.getLogger(__name__)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    logger.info("📧 send_email tool called")
    logger.info(f"   Subject : {subject}")
    logger.info(f"   Body length: {len(html_body)} chars")

    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        logger.error("❌ SENDGRID_API_KEY is missing from environment variables")
        return "error: SENDGRID_API_KEY not set"

    logger.info("   SENDGRID_API_KEY found, sending...")

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email("katheriyaankush@gmail.com")
        to_email = To("ankushkatharia@gmail.com")
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        logger.info(f"✅ Email sent — status code: {response.status_code}")
        if response.status_code not in (200, 202):
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            logger.error(f"   Response body: {response.body}")
        return "success"
    except Exception as e:
        logger.exception(f"❌ Exception while sending email: {e}")
        return f"error: {str(e)}"


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=model,
)
