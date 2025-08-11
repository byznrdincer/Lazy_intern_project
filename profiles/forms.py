from django import forms
from .models import Profile, Project, Certification, Skill, Company, Position

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'university', 'major', 'graduation_year', 'location', 'bio',
            'github', 'linkedin', 'website', 'legacy_website',
            'internship_type', 'preferred_locations', 'open_to_relocate', 'skills'
        ]
        widgets = {
            'skills': forms.CheckboxSelectMultiple(),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'technologies', 'link']

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'organization', 'date_obtained', 'certificate_url']

# Şirket formu
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'industry', 'location', 'website', 'about', 'linkedin', 'twitter', 'facebook']
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4}),
        }

# Açık pozisyon formu
class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'description', 'link']
