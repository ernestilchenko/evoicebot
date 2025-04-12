from django.shortcuts import render


# Create your views here.
def main(request):
    return render(request, 'base.html')


def login(request):
    return render(request, 'login.html')
