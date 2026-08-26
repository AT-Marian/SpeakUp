import smtplib
import os
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv
from utils.helpers import Logger

# Ensure environment variables from .env are loaded
load_dotenv()


def send_password_reset_email(to_email: str, reset_url: str, user_name: Optional[str] = None) -> bool:
    """
    Send password reset email via Gmail SMTP.
    Requires MAIL_USERNAME and MAIL_PASSWORD in .env
    """
    smtp_host = os.getenv('MAIL_HOST', 'smtp.gmail.com')
    
    port_env = str(os.getenv('MAIL_PORT', '587')).strip()
    try:
        smtp_port = int(port_env) if port_env else 587
    except ValueError:
        smtp_port = 587

    sender_email = os.getenv('MAIL_USERNAME', '').strip()
    # Strip any spaces in Gmail App Password (e.g., 'xxxx yyyy zzzz wwww' -> 'xxxxyyyyzzzzwwww')
    sender_password = os.getenv('MAIL_PASSWORD', '').replace(' ', '').strip()
    sender_name = os.getenv('MAIL_SENDER_NAME', 'SpeakUp').strip()

    if not sender_email or not sender_password:
        Logger.error("Email credentials not configured. Set MAIL_USERNAME and MAIL_PASSWORD in .env")
        return False

    display_name = user_name or to_email.split('@')[0]

    # --- HTML Email Body ---
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reset Your SpeakUp Password</title>
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#f4f7fb;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563EB 100%);padding:36px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;letter-spacing:-0.5px;">SpeakUp</h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">AI-Powered Speech Coach</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h2 style="margin:0 0 12px;color:#1e3a5f;font-size:22px;font-weight:600;">Password Reset Request</h2>
              <p style="margin:0 0 20px;color:#4b5563;font-size:15px;line-height:1.6;">
                Hi <strong>{display_name}</strong>,
              </p>
              <p style="margin:0 0 28px;color:#4b5563;font-size:15px;line-height:1.6;">
                We received a request to reset your SpeakUp password. Click the button below to set a new password. This link will expire in <strong>1 hour</strong>.
              </p>

              <!-- Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
                <tr>
                  <td style="border-radius:8px;background:#2563EB;">
                    <a href="{reset_url}"
                       style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;border-radius:8px;letter-spacing:0.3px;">
                      Reset My Password
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 8px;color:#6b7280;font-size:13px;line-height:1.6;">
                If the button doesn't work, copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 28px;word-break:break-all;">
                <a href="{reset_url}" style="color:#2563EB;font-size:13px;">{reset_url}</a>
              </p>

              <hr style="border:none;border-top:1px solid #e5e7eb;margin:0 0 24px;" />

              <p style="margin:0;color:#9ca3af;font-size:13px;line-height:1.6;">
                If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="margin:0;color:#9ca3af;font-size:12px;">
                &copy; 2026 SpeakUp &mdash; AI-Powered Speech Coach
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

    # Plaintext fallback
    text_body = f"""Hi {display_name},

We received a request to reset your SpeakUp password.

Click the link below to reset your password (expires in 1 hour):
{reset_url}

If you didn't request this, you can safely ignore this email.

— The SpeakUp Team
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🔑 Reset Your SpeakUp Password'
        msg['From'] = f'{sender_name} <{sender_email}>'
        msg['To'] = to_email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

        with server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        Logger.info(f"Password reset email sent to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        Logger.error("SMTP authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD in .env")
        return False
    except (smtplib.SMTPConnectError, socket.timeout) as e:
        Logger.error(f"SMTP connection error ({smtp_host}:{smtp_port}): {str(e)}")
        return False
    except smtplib.SMTPException as e:
        Logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        Logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
        return False

