from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from ..forms import DocumentForm
from ..models import Document, UserProfile, Project, Team


@login_required
def document_list(request):
    """Widok listy dokumentów"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Pobierz dokumenty: osobiste + zespołowe + projektowe
    user_documents = Document.objects.filter(users=user_profile)
    team_documents = Document.objects.filter(team__in=user_profile.get_teams())
    project_documents = Document.objects.filter(project__in=Project.objects.filter(teams__in=user_profile.get_teams()))

    # Połącz wszystkie dokumenty i usuń duplikaty
    all_documents = user_documents.union(team_documents, project_documents)

    context = {
        'documents': all_documents,
    }

    return render(request, 'dashboard/document_list.html', context)


@login_required
def document_detail(request, uuid):
    """Widok szczegółów dokumentu"""
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Sprawdź czy użytkownik ma dostęp do dokumentu
    has_access = (
            document.users.filter(id=user_profile.id).exists() or
            (document.team and document.team in user_profile.get_teams()) or
            (document.project and document.project in Project.objects.filter(teams__in=user_profile.get_teams()))
    )

    if not has_access and user_profile.role != 'admin':
        messages.error(request, 'Nie masz dostępu do tego dokumentu.')
        return redirect('document_list')

    context = {
        'document': document,
    }

    return render(request, 'dashboard/document_detail.html', context)


@login_required
def create_document(request):
    """Widok tworzenia nowego dokumentu"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            document.users.add(user_profile)  # Dodaj aktualnego użytkownika do dokumentu
            messages.success(request, f'Dokument "{document.title}" został pomyślnie utworzony.')
            return redirect('document_detail', uuid=document.uuid)
    else:
        # Sprawdź czy projekt lub zespół jest predefiniowany
        project_id = request.GET.get('project')
        team_id = request.GET.get('team')
        initial = {}

        if project_id:
            try:
                initial['project'] = Project.objects.get(uuid=project_id)
            except Project.DoesNotExist:
                pass

        if team_id:
            try:
                initial['team'] = Team.objects.get(uuid=team_id)
            except Team.DoesNotExist:
                pass

        form = DocumentForm(initial=initial)

    # Filtruj dostępne projekty i zespoły tylko do tych, do których użytkownik ma dostęp
    form.fields['project'].queryset = Project.objects.filter(teams__in=user_profile.get_teams()).distinct()
    form.fields['team'].queryset = user_profile.get_teams()

    context = {
        'form': form,
    }

    return render(request, 'dashboard/document_form.html', context)


@login_required
def edit_document(request, uuid):
    """Widok edycji dokumentu"""
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Sprawdź czy użytkownik ma uprawnienia do edycji
    is_creator = document.users.filter(id=user_profile.id).exists()
    is_admin = user_profile.role == 'admin'

    if not (is_creator or is_admin):
        messages.error(request, 'Nie masz uprawnień do edycji tego dokumentu.')
        return redirect('document_detail', uuid=document.uuid)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dokument "{document.title}" został zaktualizowany.')
            return redirect('document_detail', uuid=document.uuid)
    else:
        form = DocumentForm(instance=document)

    # Filtruj dostępne projekty i zespoły tylko do tych, do których użytkownik ma dostęp
    form.fields['project'].queryset = Project.objects.filter(teams__in=user_profile.get_teams()).distinct()
    form.fields['team'].queryset = user_profile.get_teams()

    context = {
        'form': form,
        'document': document,
    }

    return render(request, 'dashboard/document_form.html', context)


@login_required
def delete_document(request, uuid):
    """Widok usuwania dokumentu"""
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Sprawdź czy użytkownik ma uprawnienia do usunięcia
    is_creator = document.users.filter(id=user_profile.id).exists()
    is_admin = user_profile.role == 'admin'

    if not (is_creator or is_admin):
        messages.error(request, 'Nie masz uprawnień do usunięcia tego dokumentu.')
        return redirect('document_detail', uuid=document.uuid)

    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f'Dokument "{document_title}" został usunięty.')
        return redirect('document_list')

    context = {
        'document': document,
    }

    return render(request, 'dashboard/document_delete_confirm.html', context)
