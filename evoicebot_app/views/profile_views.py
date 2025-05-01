from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelform_factory

from ..models import UserProfile


@login_required
def profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    teams = user_profile.get_teams()

    documents_count = user_profile.documents.count()

    statistics = {
        'teams_count': teams.count(),
        'documents_count': documents_count,
        'projects_count': teams.values('project').distinct().count(),
        'join_date': user.date_joined
    }

    context = {
        'user_profile': user_profile,
        'statistics': statistics,
        'teams': teams[:5],
    }

    return render(request, 'dashboard/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email'])
    ProfileForm = modelform_factory(UserProfile, fields=['phone', 'description'])

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profil został zaktualizowany.')
            return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=user_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile
    }

    return render(request, 'dashboard/profile_edit.html', context)


@login_required
def change_password(request):
    user = request.user

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not user.check_password(current_password):
            messages.error(request, 'Aktualne hasło jest nieprawidłowe.')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, 'Nowe hasła nie są identyczne.')
            return redirect('change_password')

        if len(new_password) < 8:
            messages.error(request, 'Hasło musi mieć co najmniej 8 znaków.')
            return redirect('change_password')

        user.set_password(new_password)
        user.save()
        messages.success(request, 'Hasło zostało zmienione. Zaloguj się ponownie.')
        return redirect('login')

    return render(request, 'dashboard/change_password.html')