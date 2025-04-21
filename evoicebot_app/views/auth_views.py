from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember', False)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)

            if not remember_me:
                request.session.set_expiry(0)

            return redirect('dashboard')
        else:
            messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')

    return render(request, 'auth/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        terms = request.POST.get('terms', False)

        # Validation
        if not (username and email and password and confirm_password):
            messages.error(request, 'Wszystkie pola są wymagane.')
            return render(request, 'auth/register.html')

        if password != confirm_password:
            messages.error(request, 'Hasła nie są zgodne.')
            return render(request, 'auth/register.html')

        if not terms:
            messages.error(request, 'Musisz zaakceptować regulamin.')
            return render(request, 'auth/register.html')

        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Rejestracja zakończona pomyślnie. Możesz się teraz zalogować.')
            return redirect('login')
        except IntegrityError:
            messages.error(request, 'Użytkownik o podanej nazwie już istnieje.')

    return render(request, 'auth/register.html')


def logout(request):
    auth_logout(request)
    return redirect('main')
