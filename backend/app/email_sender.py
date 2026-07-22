"""Sends the account-verification email for local mode over SMTP. Only used when SMTP_HOST is
configured; app/auth_providers/local_auth.py checks smtp_configured() itself before deciding
whether an account needs verifying at all, so a missing configuration never reaches send().
"""

import smtplib
import ssl
from email.message import EmailMessage

from . import config


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST)


def send_verification_email(to_email: str, verify_url: str):
    message = EmailMessage()
    message["Subject"] = "Verify your email address"
    message["From"] = config.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        "Confirm your email address to finish setting up your Application Tracker account.\n\n"
        f"Verify your email: {verify_url}\n\n"
        "This link expires in 48 hours. If you did not create this account, ignore this message."
    )
    message.add_alternative(_html_body(verify_url), subtype="html")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
        server.ehlo()
        if config.SMTP_USE_TLS:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD or "")
        server.send_message(message)


def _html_body(verify_url: str) -> str:
    return f"""\
<!doctype html>
<html>
  <body style="font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; background:#f4f5f7; padding:32px 0; margin:0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; padding:32px;">
            <tr>
              <td>
                <h1 style="font-size:18px; margin:0 0 16px; color:#111827;">Verify your email address</h1>
                <p style="font-size:14px; color:#374151; line-height:1.5; margin:0 0 24px;">
                  Confirm your email address to finish setting up your Application Tracker account.
                </p>
                <p style="text-align:center; margin:0 0 24px;">
                  <a href="{verify_url}" style="background:#4f46e5; color:#ffffff; text-decoration:none; padding:12px 24px; border-radius:6px; font-size:14px; display:inline-block;">Verify email</a>
                </p>
                <p style="font-size:12px; color:#6b7280; line-height:1.5; margin:0;">
                  This link expires in 48 hours. If you did not create this account, you can ignore this message.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
