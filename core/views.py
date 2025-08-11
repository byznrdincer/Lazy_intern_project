from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

def how_it_works(request):
    return render(request, 'core/how_it_works.html')

def for_students(request):
    return render(request, 'core/for_students.html')

def for_companies(request):
    return render(request, 'core/for_companies.html')

def about(request):
    return render(request, 'core/about.html')

