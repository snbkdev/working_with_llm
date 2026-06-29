"""Email sending via stdlib smtplib.

`send_email` is synchronous and blocking; call it from a FastAPI
BackgroundTask so the HTTP response is not delayed. Emails are silently
skipped (logged) when SMTP is not configured.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from . import config

logger = logging.getLogger("duckie.mailer")


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Send one email. Returns True on success, False otherwise.

    Designed to never raise to the caller (logs and returns False), so a mail
    failure can't break registration / reset flows.
    """
    if not config.EMAIL_ENABLED:
        logger.warning("SMTP не настроен — письмо для %s не отправлено: %s", to, subject)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((config.SMTP_FROM_NAME, config.SMTP_FROM))
    msg["To"] = to
    msg.set_content(text or _strip_html(html))
    msg.add_alternative(html, subtype="html")

    try:
        if config.SMTP_TLS_POLICY == "ssl":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT, context=ctx
            ) as server:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT
            ) as server:
                if config.SMTP_TLS_POLICY == "starttls":
                    server.starttls(context=ssl.create_default_context())
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
        logger.info("Письмо отправлено: %s -> %s", subject, to)
        return True
    except Exception:  # noqa: BLE001 — never propagate mail errors
        logger.exception("Не удалось отправить письмо на %s", to)
        return False


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# --- Branded email templates ---

def _wrap(title: str, body_html: str) -> str:
    return f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1b2733">
  <div style="font-size:22px;font-weight:700">🦆 {config.APP_NAME}</div>
  <h2 style="font-size:18px;margin:20px 0 12px">{title}</h2>
  {body_html}
  <hr style="border:none;border-top:1px solid #e6e8ef;margin:24px 0">
  <div style="font-size:12px;color:#6b7785">Письмо отправлено автоматически, отвечать на него не нужно.</div>
</div>"""


def send_welcome_email(to: str, name: str) -> bool:
    html = _wrap(
        f"Привет, {name}! 👋",
        "<p>Спасибо за регистрацию на платформе. Выбирай направление, проходи "
        "уроки, решай тесты и код-челленджи — и копи XP по пути к новой профессии.</p>"
        f'<p><a href="{config.APP_BASE_URL}/app" '
        'style="display:inline-block;background:#6d4ae0;color:#fff;text-decoration:none;'
        'padding:12px 22px;border-radius:10px;font-weight:600">Перейти к обучению</a></p>',
    )
    return send_email(to, f"Добро пожаловать в {config.APP_NAME}!", html)


def send_password_reset_email(to: str, name: str, reset_url: str) -> bool:
    html = _wrap(
        "Сброс пароля",
        f"<p>{name}, вы запросили сброс пароля. Нажмите кнопку ниже, чтобы задать "
        "новый пароль. Ссылка действует ограниченное время.</p>"
        f'<p><a href="{reset_url}" '
        'style="display:inline-block;background:#6d4ae0;color:#fff;text-decoration:none;'
        'padding:12px 22px;border-radius:10px;font-weight:600">Сбросить пароль</a></p>'
        "<p style=\"font-size:13px;color:#6b7785\">Если вы не запрашивали сброс — "
        "просто проигнорируйте это письмо.</p>",
    )
    return send_email(to, "Сброс пароля", html)


def send_notification_email(to: str, subject: str, message_html: str) -> bool:
    """Generic notification email (security alerts, course updates, etc.)."""
    return send_email(to, subject, _wrap(subject, message_html))
