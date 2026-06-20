import os
import logging
import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
if not FROM_EMAIL:
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    if is_dev:
        FROM_EMAIL = "HireIQ <onboarding@resend.dev>"
        logger.warning("FROM_EMAIL not configured. Falling back to sandbox domain for development.")
    else:
        FROM_EMAIL = "HireIQ <notifications@yourdomain.com>"
        logger.error("CRITICAL: FROM_EMAIL environment variable is not configured in a non-development environment! Defaulting to notifications@yourdomain.com which will fail if domain is not verified in Resend.")

# HTML Templates for product and transactional emails
TEMPLATES = {
    "welcome": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #6366f1;">Welcome to HireIQ!</h2>
            <p>Hello,</p>
            <p>Thank you for choosing HireIQ. Your organization workspace has been created successfully with a Free subscription plan.</p>
            <p>You can now start uploading candidate resumes, generating blind candidate profiles, and evaluating talents with advanced AI matching signals.</p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """,
    "verify": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #6366f1;">Verify Your Email Address</h2>
            <p>Hello,</p>
            <p>Please click the button below to verify your email address and activate your HireIQ account:</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Verify Email</a>
            </p>
            <p>Or copy and paste this link in your browser: <br/> {link}</p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """,
    "password_reset": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #6366f1;">Reset Your Password</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password. Click the button below to set a new password:</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
            </p>
            <p>If you did not request this reset, you can safely ignore this email.</p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """,
    "invitation": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #6366f1;">Join Organization on HireIQ</h2>
            <p>Hello,</p>
            <p>You have been invited to join the organization <strong>{org_name}</strong> as a <strong>{role}</strong> on HireIQ.</p>
            <p>Click the link below to accept the invitation and set up your member account:</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Accept Invitation</a>
            </p>
            <p>This invitation link will expire soon.</p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """,
    "usage_warning": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #f59e0b;">Quota Limit Warning</h2>
            <p>Hello,</p>
            <p>Your organization has used <strong>{used}</strong> out of <strong>{limit}</strong> resume parses allowed on your current <strong>{plan}</strong> plan.</p>
            <p>To ensure your recruitment workflow is not interrupted, please consider upgrading your plan in Settings.</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Upgrade Subscription</a>
            </p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """,
    "upgrade_prompt": """
        <div style="font-family: sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #ef4444;">Quota Exhausted!</h2>
            <p>Hello,</p>
            <p>Your organization has exhausted all <strong>{limit}</strong> resume parses on your <strong>{plan}</strong> subscription plan.</p>
            <p>Further uploads will be blocked until your billing cycle resets or you upgrade your plan.</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Upgrade Now</a>
            </p>
            <br/>
            <p>Best regards,</p>
            <p>The HireIQ Team</p>
        </div>
    """
}

async def send_html_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email using Resend's REST API endpoint."""
    if not RESEND_API_KEY:
        logger.warning("⚠️  RESEND_API_KEY is missing. Simulating email send to %s: Subject: '%s'", to_email, subject)
        return True

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=headers, timeout=10.0)
            if resp.status_code in [200, 201]:
                logger.info("Email sent successfully to %s", to_email)
                return True
            else:
                logger.error("Failed to send email via Resend: %d - %s", resp.status_code, resp.text)
                return False
    except Exception as e:
        logger.error("Error connecting to Resend email server: %s", e)
        return False


async def send_welcome_email(to_email: str):
    return await send_html_email(
        to_email=to_email,
        subject="Welcome to HireIQ!",
        html_content=TEMPLATES["welcome"]
    )


async def send_verification_email(to_email: str, verification_link: str):
    content = TEMPLATES["verify"].format(link=verification_link)
    return await send_html_email(
        to_email=to_email,
        subject="Verify Your HireIQ Account",
        html_content=content
    )


async def send_password_reset_email(to_email: str, reset_link: str):
    content = TEMPLATES["password_reset"].format(link=reset_link)
    return await send_html_email(
        to_email=to_email,
        subject="Reset Your HireIQ Password",
        html_content=content
    )


async def send_org_invitation_email(to_email: str, org_name: str, role: str, invitation_link: str):
    content = TEMPLATES["invitation"].format(org_name=org_name, role=role, link=invitation_link)
    return await send_html_email(
        to_email=to_email,
        subject=f"Invitation to join {org_name} on HireIQ",
        html_content=content
    )


async def send_usage_warning_email(to_email: str, used: int, limit: int, plan: str, upgrade_link: str):
    content = TEMPLATES["usage_warning"].format(used=used, limit=limit, plan=plan, link=upgrade_link)
    return await send_html_email(
        to_email=to_email,
        subject="HireIQ Usage Quota Limit Notice",
        html_content=content
    )


async def send_upgrade_prompt_email(to_email: str, limit: int, plan: str, upgrade_link: str):
    content = TEMPLATES["upgrade_prompt"].format(limit=limit, plan=plan, link=upgrade_link)
    return await send_html_email(
        to_email=to_email,
        subject="ACTION REQUIRED: HireIQ Quota Exhausted",
        html_content=content
    )
