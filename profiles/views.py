from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import F

from .models import Profile, Skill, Company
from .forms import (
    ProfileForm,
    ProjectForm,
    CertificationForm,
    CompanyForm,
    PositionForm,
)

# ---------------------------------
# Helpers
# ---------------------------------
def _normalize(v):
    """'None', 'null', 'undefined', '-' vb. stringleri gerçek None'a çevirir; trim yapar."""
    if v is None:
        return None
    v = str(v).strip()
    return None if v.lower() in {"none", "null", "undefined", "-"} else v

def _display(v):
    """Ekranda güvenli gösterim: normalize sonrası None ise boş string döndür."""
    nv = _normalize(v)
    return "" if nv is None else nv

def calculate_completion_percent(profile: Profile) -> int:
    percent = 0
    if getattr(profile, "bio", None):
        percent += 30
    if getattr(profile, "location", None):
        percent += 30
    if hasattr(profile, "skills") and profile.skills.exists():
        percent += 40
    return percent

def calculate_company_completion(company: Company) -> int:
    percent = 0
    if getattr(company, "about", None):
        percent += 30
    if getattr(company, "location", None):
        percent += 30
    if hasattr(company, "positions") and company.positions.exists():
        percent += 40
    return percent

def ensure_company_slug(company: Company) -> None:
    if not company.slug:
        base = slugify(company.name or f"company-{company.pk}") or f"company-{company.pk}"
        slug = base
        i = 2
        while Company.objects.filter(slug=slug).exclude(pk=company.pk).exists():
            slug = f"{base}-{i}"
            i += 1
        company.slug = slug
        company.save(update_fields=["slug"])

# ---------------------------------
# Redirect
# ---------------------------------
@login_required
def profile_redirect(request):
    try:
        if hasattr(request.user, "company") and request.user.company:
            ensure_company_slug(request.user.company)
            return redirect("company_profile", slug=request.user.company.slug)
    except Company.DoesNotExist:
        pass
    return redirect("profile_detail", username=request.user.username)

# ---------------------------------
# Student profile
# ---------------------------------
@login_required
def profile_detail(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    years = list(range(2020, 2036))

    profile_form = ProfileForm(instance=profile)
    project_form = ProjectForm()
    certification_form = CertificationForm()
    errors = []

    if request.method == "POST":
        # ---------- Personal Information ----------
        if "profile_submit" in request.POST:
            # ham değerleri al + normalize et
            full_name       = _normalize(request.POST.get("full_name"))
            email           = _normalize(request.POST.get("email"))
            university      = _normalize(request.POST.get("university"))
            major           = _normalize(request.POST.get("major"))
            graduation_year = (request.POST.get("graduation_year") or "").strip()
            location        = _normalize(request.POST.get("location"))
            bio             = _normalize(request.POST.get("bio"))

            # zorunlu alanlar
            if not full_name:       errors.append("Full Name is required.")
            if not email:           errors.append("Email Address is required.")
            if not university:      errors.append("University is required.")
            if not major:           errors.append("Major/Field of Study is required.")
            if not graduation_year: errors.append("Graduation Year is required.")
            if not location:        errors.append("Current Location is required.")
            if not bio:             errors.append("Bio/About Me is required.")

            if not errors:
                # User
                parts = full_name.split()
                user.first_name = parts[0]
                user.last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""
                user.email = email
                user.save()

                # Profile
                profile.university      = university
                profile.major           = major
                profile.graduation_year = int(graduation_year) if graduation_year else None
                profile.location        = location
                profile.bio             = bio
                profile.save()

                return redirect("profile_detail", username=username)

        # ---------- Project Form ----------
        elif "project_submit" in request.POST:
            project_form = ProjectForm(request.POST)
            if project_form.is_valid():
                p = project_form.save(commit=False)
                p.profile = profile
                p.save()
                return redirect("profile_detail", username=username)

        # ---------- Certification Form ----------
        elif "certification_submit" in request.POST:
            certification_form = CertificationForm(request.POST)
            if certification_form.is_valid():
                c = certification_form.save(commit=False)
                c.profile = profile
                c.save()
                return redirect("profile_detail", username=username)

        # ---------- Social Links ----------
        elif "social_submit" in request.POST:
            profile.github = _normalize(request.POST.get("github"))
            profile.linkedin = _normalize(request.POST.get("linkedin"))
            profile.website = _normalize(request.POST.get("website"))
            profile.legacy_website = _normalize(request.POST.get("legacy_website"))
            profile.save()
            return redirect("profile_detail", username=username)

        # ---------- Internship ----------
        elif "internship_submit" in request.POST:
            profile.internship_type = _normalize(request.POST.get("internship_type"))
            profile.preferred_locations = _normalize(request.POST.get("preferred_locations"))
            profile.open_to_relocate = "open_to_relocate" in request.POST
            profile.save()
            return redirect("profile_detail", username=username)

        # ---------- Skills ----------
        elif "skills_submit" in request.POST:
            skills_ids = request.POST.getlist("skills")
            profile.skills.set(skills_ids)
            return redirect("profile_detail", username=username)

    context = {
        "profile_user": user,
        "profile": profile,
        "full_name": user.get_full_name(),
        "form": profile_form,
        "project_form": project_form,
        "certification_form": certification_form,
        "years": years,
        "projects": profile.projects.all() if hasattr(profile, "projects") else [],
        "certifications": profile.certifications.all() if hasattr(profile, "certifications") else [],
        "skills_count": profile.skills.count(),
        "projects_count": profile.projects.count() if hasattr(profile, "projects") else 0,
        "certifications_count": profile.certifications.count() if hasattr(profile, "certifications") else 0,
        "profile_views": getattr(profile, "profile_views", 0),
        "completion_percent": calculate_completion_percent(profile),
        "all_skills": Skill.objects.all(),
        "skills": profile.skills.all(),
        "errors": errors,

        # UI-safe alanlar (None & 'None' görünmesin)
        "ui_university": _display(profile.university),
        "ui_major": _display(profile.major),
        "ui_location": _display(profile.location),
        "ui_bio": _display(profile.bio),
    }
    return render(request, "profiles/profile_detail.html", context)

# ---------------------------------
# Company profile (unchanged except helpers used above)
# ---------------------------------
@login_required
def company_profile(request, slug):
    company = get_object_or_404(Company, slug=slug)
    ensure_company_slug(company)

    company_form = CompanyForm(instance=company)
    position_form = PositionForm()

    if request.method == "POST":
        if "company_info_submit" in request.POST:
            company_form = CompanyForm(request.POST, instance=company)
            if company_form.is_valid():
                company_form.save()
                return redirect("company_profile", slug=slug)

        elif "position_submit" in request.POST:
            position_form = PositionForm(request.POST)
            if position_form.is_valid():
                pos = position_form.save(commit=False)
                pos.company = company
                pos.save()
                return redirect("company_profile", slug=slug)

        elif "social_submit" in request.POST:
            company.linkedin = _normalize(request.POST.get("linkedin"))
            company.twitter = _normalize(request.POST.get("twitter"))
            company.facebook = _normalize(request.POST.get("facebook"))
            company.save()
            return redirect("company_profile", slug=slug)

    tab = request.GET.get("tab", "all")
    major = (request.GET.get("major") or "").strip()
    skill = (request.GET.get("skill") or "").strip()
    project_skill = (request.GET.get("project_skill") or "").strip()
    location = (request.GET.get("location") or "").strip()
    graduation_year = (request.GET.get("graduation_year") or "").strip()
    internship_type = (request.GET.get("internship_type") or "").strip()

    base_students = (
        Profile.objects.select_related("user")
        .prefetch_related("skills", "projects")
        .filter(user__company__isnull=True)
        .exclude(user=getattr(company, "user", None))
    )

    students_qs = base_students
    if major:
        students_qs = students_qs.filter(major__icontains=major)
    if location:
        students_qs = students_qs.filter(location__icontains=location)
    if graduation_year:
        students_qs = students_qs.filter(graduation_year=graduation_year)
    if internship_type:
        students_qs = students_qs.filter(internship_type__iexact=internship_type)
    if skill:
        students_qs = students_qs.filter(skills__name__icontains=skill).distinct()
    if project_skill:
        students_qs = students_qs.filter(projects__technologies__icontains=project_skill).distinct()

    filtered_students = students_qs
    filtered_count = filtered_students.count()
    total_count = base_students.count()

    bookmarked_students = company.bookmarked_students.select_related("user").prefetch_related("skills").all()
    bookmarked_ids = set(bookmarked_students.values_list("id", flat=True))

    context = {
        "company": company,
        "profile_views": 0,
        "open_positions_count": company.positions.count(),
        "applicants_count": 0,
        "completion_percent": calculate_company_completion(company),
        "company_form": company_form,
        "position_form": position_form,
        "students": filtered_students,
        "filtered_students": filtered_students,
        "bookmarked_students": bookmarked_students,
        "bookmarked_ids": bookmarked_ids,
        "active_tab": tab,
        "filtered_count": filtered_count,
        "total_count": total_count,
    }
    return render(request, "profiles/company_profile.html", context)

# ---------------------------------
# Bookmark toggle
# ---------------------------------
@login_required
@require_POST
def toggle_bookmark(request, student_id: int):
    company = getattr(request.user, "company", None)
    if not company:
        return redirect("profile_redirect")

    student = get_object_or_404(Profile, id=student_id)

    if company.bookmarked_students.filter(id=student.id).exists():
        company.bookmarked_students.remove(student)
    else:
        company.bookmarked_students.add(student)

    next_url = (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse("company_profile", kwargs={"slug": company.slug})
    )
    return redirect(next_url)

# ---------------------------------
# Profile view counter
# ---------------------------------
@login_required
@require_POST
def increment_profile_views(request, user_id: int):
    profile = get_object_or_404(Profile, user_id=user_id)
    Profile.objects.filter(pk=profile.pk).update(profile_views=F("profile_views") + 1)

    next_url = request.POST.get("next") or reverse(
        "student_profile_view", kwargs={"user_id": user_id}
    )
    return redirect(next_url)

# ---------------------------------
# Public student profile
# ---------------------------------
@login_required
def student_profile_view(request, user_id: int):
    profile = get_object_or_404(
        Profile.objects.select_related("user").prefetch_related(
            "skills", "projects", "certifications"
        ),
        user_id=user_id,
    )
    return render(
        request,
        "profiles/student_public_profile.html",
        {
            "profile": profile,
            "profile_user": profile.user,
            "skills": profile.skills.all(),
            "projects": profile.projects.all() if hasattr(profile, "projects") else [],
            "certifications": profile.certifications.all()
            if hasattr(profile, "certifications")
            else [],
        },
    )

@login_required
def profile_edit(request, username):
    return redirect("profile_detail", username=username)
