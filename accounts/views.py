# accounts/views.py
from urllib.parse import urlencode
from datetime import timedelta
import secrets

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from profiles.models import Profile, Company
from .email_utils import send_company_verification_email


# -------------------------------
# Company yardımcıları
# -------------------------------
def _unique_company_slug_for_user(user) -> str:
    base = slugify(user.username or (user.email.split("@")[0] if user.email else "")) or f"company-{user.id}"
    slug = base
    i = 2
    while Company.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _get_or_prepare_company_for_user(user) -> Company:
    company = Company.objects.filter(user_id=user.id).first()
    if not company:
        company = Company.objects.create(
            user=user,
            name=user.username or "Company",
            slug=_unique_company_slug_for_user(user),
        )
    elif not getattr(company, "slug", None):
        company.slug = _unique_company_slug_for_user(user)
        company.save(update_fields=["slug"])
    return company


def _company_email(company: Company) -> str | None:
    # Önce company.contact_email, yoksa company.user.email
    if getattr(company, "contact_email", None):
        return company.contact_email
    if company.user and company.user.email:
        return company.user.email
    return None


# -------------------------------
# Register / Login / Logout
# -------------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = request.POST.get('user_type')

            if user_type == 'student':
                # Öğrenci: profil oluştur, login yapma; login sayfasına yönlendir
                Profile.objects.get_or_create(user=user)
                messages.success(request, 'Registration successful. Please log in.')
                return redirect('login')

            elif user_type in ['company', 'recruiter']:
                # Şirket/recruiter: company hazırla, login yap, verify sayfasına gönder
                _get_or_prepare_company_for_user(user)
                login(request, user)
                params = {'next': reverse('login'), 'just_registered': '1'}
                return redirect(f"{reverse('company_verify_email')}?{urlencode(params)}")

            # Belirsiz durum: güvenli varsayılan
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            email_or_username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Email ile giriş desteği
            try:
                user_obj = User.objects.get(email=email_or_username)
                username = user_obj.username
            except User.DoesNotExist:
                username = email_or_username

            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, "Authentication failed.")
                return render(request, 'accounts/login.html', {'form': form})

            # Hesabın gerçek tipi
            has_company = Company.objects.filter(user=user).exists()

            if user_type == 'student':
                if has_company:
                    messages.error(request, "This is a company account; cannot log in as 'Student'.")
                    return redirect('login')
             
                login(request, user)
                Profile.objects.get_or_create(user=user)
                return redirect('profile_detail', username=user.username)

            elif user_type in ['company', 'recruiter']:
                if not has_company:
                    messages.error(request, "This is a student account; cannot log in as 'Company'.")
                    return redirect('login')
                # Company -> login + şirket dashboard (MESAJ YOK)
                login(request, user)
                company = _get_or_prepare_company_for_user(user)
                return redirect('company_profile', slug=company.slug)

            else:
                messages.error(request, "Please select a user type.")
                return redirect('login')

        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'accounts/login.html', {'form': form})

    # GET
    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# -------------------------------
# Verify entry -> slug'lı verify'e redirect
# -------------------------------
@login_required
def company_verify_entry(request):
    """
    /accounts/company/verify-email/ -> kullanıcıya ait şirketin
    /accounts/company/<slug>/verify/ sayfasına yönlendirir.
    """
    company = _get_or_prepare_company_for_user(request.user)

    params = {}
    nxt = request.GET.get("next")
    if nxt:
        params["next"] = nxt
    jr = request.GET.get("just_registered")
    if jr:
        params["just_registered"] = jr

    url = reverse("company_email_verify", kwargs={"slug": company.slug})
    if params:
        url = f"{url}?{urlencode(params)}"
    return redirect(url)


# -------------------------------
# Şirket e-posta doğrulaması: kod gönder (POST)
# -------------------------------
@login_required
@require_POST
def company_send_verification_code(request, slug):
    company = Company.objects.filter(slug=slug, user=request.user).first()
    if not company:
        return redirect("home")

    # Formdan e-posta geldiyse kaydet
    email_from_form = (request.POST.get("verification_email") or "").strip()
    if email_from_form and getattr(company, "contact_email", None) != email_from_form:
        company.contact_email = email_from_form
        company.save(update_fields=["contact_email"])

    # 6 haneli kod üret
    code = "".join(secrets.choice("0123456789") for _ in range(6))
    company.verification_code = code
    company.verification_expires_at = timezone.now() + timedelta(minutes=10)
    company.is_verified = False
    company.save(update_fields=["verification_code", "verification_expires_at", "is_verified"])

    to_email = email_from_form or _company_email(company)
    if not to_email:
        return redirect(f"{reverse('company_profile', kwargs={'slug': slug})}?msg=no_email")

    next_qs = request.GET.get("next") or request.POST.get("next")
    try:
        send_company_verification_email(to_email, code, company.name)
        url = f"{reverse('company_email_verify', kwargs={'slug': slug})}?sent=1"
    except Exception:
        url = f"{reverse('company_email_verify', kwargs={'slug': slug})}?error=send_failed"

    if next_qs:
        url += f"&next={next_qs}"
    return redirect(url)


# -------------------------------
# Şirket e-posta doğrulaması: kodu gir & doğrula
# -------------------------------
@login_required
def company_email_verify(request, slug):
    company = Company.objects.filter(slug=slug, user=request.user).first()
    if not company:
        return redirect("home")

    ctx = {"company": company, "ttl_minutes": 10}

    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        now = timezone.now()

        if not company.verification_code or not company.verification_expires_at:
            ctx["error"] = "No active code. Please request a new verification code."
        elif now > company.verification_expires_at:
            ctx["error"] = "Code expired. Please request a new verification code."
        elif code != company.verification_code:
            ctx["error"] = "Invalid code. Please try again."
        else:
            company.is_verified = True
            company.verified_at = now
            company.verification_code = None
            company.verification_expires_at = None
            company.save(update_fields=[
                "is_verified", "verified_at", "verification_code", "verification_expires_at"
            ])

            messages.success(request, "Email verified. You can now log in.")
            next_url = request.GET.get("next") or request.POST.get("next") or reverse("login")
            return redirect(next_url)

    return render(request, "accounts/company_verify_email.html", ctx)
