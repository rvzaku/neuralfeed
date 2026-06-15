"""Transactional email via Resend's HTTP API.

Intentionally tiny: one send_email() that no-ops (returning False) when no API
key is configured, so dev and free-tier deploys without email still run. The
digest job logs the no-op rather than failing.
"""

import html as _html

import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger()

_RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send one HTML email. Returns True on success, False if email is disabled
    (no API key) or the send failed. Never raises to the caller."""
    if not settings.resend_api_key:
        log.info("email_disabled_noop", to=to, subject=subject)
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                _RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.digest_from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html_body,
                },
            )
        if resp.status_code >= 400:
            log.error("email_send_failed", to=to, status=resp.status_code, body=resp.text[:300])
            return False
        return True
    except Exception as e:  # network/timeout — never break the caller (the job)
        log.error("email_send_error", to=to, error=str(e))
        return False


def render_digest_email(digest: dict) -> str:
    """Render a digest dict (from services.digest.build_digest) into a simple,
    email-client-safe HTML body. Inline styles only — no external CSS."""
    base = settings.app_base_url.rstrip("/")
    rows = []
    for i, item in enumerate(digest.get("items", []), 1):
        title = _html.escape(item.get("title") or "Untitled")
        url = _html.escape(item.get("url") or base)
        source = _html.escape(item.get("source_name") or "")
        blurb = item.get("blurb")
        blurb_html = (
            f'<p style="margin:6px 0 0;color:#555;font-size:14px;line-height:1.5;">{_html.escape(blurb)}</p>'
            if blurb
            else ""
        )
        rows.append(
            f"""
            <tr><td style="padding:16px 0;border-bottom:1px solid #eee;">
              <div style="font-size:12px;color:#999;text-transform:uppercase;letter-spacing:.04em;">
                {i} · {source}
              </div>
              <a href="{url}" style="color:#111;font-size:17px;font-weight:600;text-decoration:none;line-height:1.35;">
                {title}
              </a>
              {blurb_html}
            </td></tr>
            """
        )
    items_html = "".join(rows) or "<tr><td>No stories today — check back tomorrow.</td></tr>"

    return f"""\
<!DOCTYPE html>
<html><body style="margin:0;background:#fafafa;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fafafa;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #eee;border-radius:14px;padding:28px 32px;">
        <tr><td>
          <div style="font-size:13px;color:#888;">Today in AI</div>
          <h1 style="margin:4px 0 2px;font-size:22px;color:#111;">Your daily digest</h1>
          <div style="font-size:13px;color:#999;">The {digest.get('count', 0)} stories worth your attention right now.</div>
        </td></tr>
        <tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{items_html}</table></td></tr>
        <tr><td style="padding-top:20px;">
          <a href="{base}" style="display:inline-block;background:#111;color:#fff;text-decoration:none;font-size:14px;font-weight:600;padding:10px 18px;border-radius:999px;">Open NeuralFeed</a>
        </td></tr>
        <tr><td style="padding-top:18px;color:#aaa;font-size:12px;line-height:1.5;">
          You're getting this because you turned on the daily digest in NeuralFeed. Turn it off anytime in Settings.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
