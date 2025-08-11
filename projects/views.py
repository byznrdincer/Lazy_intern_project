from django.shortcuts import render

def project_list(request):
    # Projeleri listele
    return render(request, 'projects/project_list.html')

def project_create(request):
    # Proje oluşturma formu
    return render(request, 'projects/project_form.html')

def project_detail(request, pk):
    # Belirli bir projenin detayını göster
    return render(request, 'projects/project_detail.html', {'pk': pk})

