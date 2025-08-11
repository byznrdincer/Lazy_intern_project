# profiles/email_utils.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def build_company_verification_subject(company_name: str | None = None) -> str:
    base = "lazyIntern | Company email verification"
    return f"{base} - {company_name}" if company_name else base

def build_company_verification_bodies(code: str, company_name: str | None = None) -> tuple[str, str]:
    """
    Returns plain-text and HTML bodies for the verification email.
    """
    title = "Company Email Verification"
    sub = f"for {company_name} " if company_name else ""
    text_body = (
        f"{title}\n\n"
        f"Your verification code {sub}is: {code}\n"
        f"This code is valid for 10 minutes.\n\n"
        f"Thanks,\n"
        f"The lazyIntern Team"
    )
    html_body = f"""
    <div style="font-family:ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width:560px">
      <h2 style="margin:0 0 8px">Company Email Verification</h2>
      <p style="color:#475569;margin:0 0 16px">
        Your verification code {sub}is below. The code is valid for 10 minutes.
      </p>
      <div style="font-size:28px;font-weight:800;letter-spacing:4px;
                  padding:14px 16px;border:1px solid #e2e8f0;border-radius:12px;
                  text-align:center;background:#f8fafc;margin-bottom:12px;">
        {code}
      </div>
      <p style="color:#64748b">Thanks,<br/>The lazyIntern Team</p>
    </div>
    """
    return text_body, html_body

def send_company_verification_email(to_email: str, code: str, company_name: str | None = None) -> int:
    subject = build_company_verification_subject(company_name)
    text_body, html_body = build_company_verification_bodies(code, company_name)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@lazyintern.local")

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=False)
