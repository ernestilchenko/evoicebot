import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404

from ..api.openai import *
from ..forms import DocumentForm
from ..models import Document, UserProfile, Project, Team


@login_required
def document_list(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    user_documents = Document.objects.filter(users=user_profile)
    team_documents = Document.objects.filter(team__in=user_profile.get_teams())
    project_documents = Document.objects.filter(project__in=Project.objects.filter(teams__in=user_profile.get_teams()))

    all_documents = user_documents.union(team_documents, project_documents)

    context = {
        'documents': all_documents,
    }

    return render(request, 'dashboard/document_list.html', context)


@login_required
def document_detail(request, uuid):
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    has_access = (
            document.users.filter(id=user_profile.id).exists() or
            (document.team and document.team in user_profile.get_teams()) or
            (document.project and document.project in Project.objects.filter(teams__in=user_profile.get_teams()))
    )

    if not has_access and user_profile.role != 'admin':
        messages.error(request, 'Nie masz dostępu do tego dokumentu.')
        return redirect('document_list')

    file_exists = False
    file_url = None
    file_size = 0

    if document.file:
        try:
            file_exists = True
            file_url = document.file.url
        except Exception as e:
            print(f"Error getting file URL: {str(e)}")
            file_exists = False

    if request.GET.get('generate_audio') and document.ai_description and not document.ai_audio:
        try:
            result = generate_speech(document.ai_description)

            # Save audio file
            filename = f"audio_{document.uuid}.wav"
            document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)

            messages.success(request, 'Wygenerowano audio dla dokumentu.')
            return redirect('document_detail', uuid=document.uuid)
        except Exception as e:
            messages.error(request, f'Błąd generowania audio: {str(e)}')

    audio_exists = False
    audio_url = None

    if document.ai_audio:
        try:
            audio_url = document.ai_audio.url
            audio_exists = True
        except Exception as e:
            print(f"Error getting audio URL: {str(e)}")
            audio_exists = False

    context = {
        'document': document,
        'file_exists': file_exists,
        'file_url': file_url,
        'file_size': file_size,
        'audio_exists': audio_exists,
        'audio_url': audio_url,
    }

    return render(request, 'dashboard/document_detail.html', context)


@login_required
def create_document(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)

            if 'file' in request.FILES:
                file = request.FILES['file']

                document.file_type = os.path.splitext(file.name)[1][1:].lower()

                ai_description = analyze_document(file, document.file_type)
                if ai_description:
                    document.ai_description = ai_description

                    try:
                        if request.POST.get('generate_audio'):
                            result = generate_speech(ai_description)

                            audio_data = result["audio_data"]
                        else:
                            audio_data = None
                    except Exception as e:
                        audio_data = None
                        print(f"Error generating audio: {e}")

            document.save()
            document.users.add(user_profile)
            form.save_m2m()

            if ai_description and audio_data:
                filename = f"audio_{document.uuid}.wav"
                document.ai_audio.save(filename, ContentFile(audio_data), save=True)

            messages.success(request, f'Dokument "{document.title}" został pomyślnie utworzony.')
            return redirect('document_detail', uuid=document.uuid)
    else:
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

    form.fields['project'].queryset = Project.objects.filter(teams__in=user_profile.get_teams()).distinct()
    form.fields['team'].queryset = user_profile.get_teams()

    context = {
        'form': form,
    }

    return render(request, 'dashboard/document_form.html', context)


@login_required
def edit_document(request, uuid):
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    is_creator = document.users.filter(id=user_profile.id).exists()
    is_admin = user_profile.role == 'admin'

    if not (is_creator or is_admin):
        messages.error(request, 'Nie masz uprawnień do edycji tego dokumentu.')
        return redirect('document_detail', uuid=document.uuid)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)

            ai_description = None
            audio_data = None

            if 'file' in request.FILES:
                file = request.FILES['file']

                document.file_type = os.path.splitext(file.name)[1][1:].lower()

                ai_description = analyze_document(file, document.file_type)
                if ai_description:
                    document.ai_description = ai_description

                    if document.ai_audio:
                        document.ai_audio.delete(save=False)
                        document.ai_audio = None

                    try:
                        if request.POST.get('generate_audio'):
                            result = generate_speech(ai_description)
                            audio_data = result["audio_data"]
                    except Exception as e:
                        print(f"Error generating audio: {e}")

            document.save()
            form.save_m2m()

            if ai_description and audio_data:
                filename = f"audio_{document.uuid}.wav"
                document.ai_audio.save(filename, ContentFile(audio_data), save=True)

            messages.success(request, f'Dokument "{document.title}" został zaktualizowany.')
            return redirect('document_detail', uuid=document.uuid)
    else:
        form = DocumentForm(instance=document)

    form.fields['project'].queryset = Project.objects.filter(teams__in=user_profile.get_teams()).distinct()
    form.fields['team'].queryset = user_profile.get_teams()

    context = {
        'form': form,
        'document': document,
    }

    return render(request, 'dashboard/document_form.html', context)


@login_required
def delete_document(request, uuid):
    document = get_object_or_404(Document, uuid=uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

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
