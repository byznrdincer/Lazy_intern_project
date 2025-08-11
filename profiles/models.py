# profiles/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    university = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    legacy_website = models.URLField(blank=True, null=True)

    internship_type = models.CharField(max_length=50, blank=True, null=True)
    preferred_locations = models.CharField(max_length=255, blank=True, null=True)
    open_to_relocate = models.BooleanField(default=False)

    skills = models.ManyToManyField(Skill, blank=True, related_name="profiles")

    # Görüntülenme sayacı
    profile_views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Project(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="projects"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    technologies = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.title} - {self.profile.user.username}"


class Certification(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    date_obtained = models.DateField()
    certificate_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-date_obtained", "name"]

    def __str__(self):
        return f"{self.name} - {self.profile.user.username}"


class Company(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="company"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    industry = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)

    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)

    # --- Email doğrulama alanları ---
    contact_email = models.EmailField(blank=True, null=True)  # maili buradan ya da user.email'den alacağız
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_expires_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    # Öğrenci bookmark ilişkisi (through ile)
    bookmarked_students = models.ManyToManyField(
        Profile,
        through="Bookmark",
        related_name="bookmarked_by_companies",
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name or (self.user.username if self.user else "company")) or "company"
            slug = base
            i = 2
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Position(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="positions"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.title} at {self.company.name}"


# Bookmark through modeli
class Bookmark(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="bookmarks"
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="bookmarks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("company", "profile")
        indexes = [models.Index(fields=["company", "profile"])]

    def __str__(self):
        return f"{self.company.name} ↔ {self.profile.user.username}"
