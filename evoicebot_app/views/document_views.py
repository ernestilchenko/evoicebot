import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile

from ..forms import DocumentForm
from ..models import Document, UserProfile, Project, Team
from ..api.openai import analyze_document, generate_speech


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
    file_size_formatted = "0 B"

    if document.file:
        try:
            file_exists = True
            file_url = document.file.url
            file_size = document.file.size
            file_size_formatted = format_file_size(file_size)
            print(f"[DETAIL] File size: {file_size} bytes ({file_size_formatted})")
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            file_exists = False

    if request.GET.get('generate_audio') and document.ai_description and not document.ai_audio:
        print(f"[DETAIL] Generating audio for document {document.title}")
        try:
            result = generate_speech(document.ai_description)
            if result and "audio_data" in result:
                filename = f"audio_{document.uuid}.wav"
                document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)
                print(f"[DETAIL] Audio generated successfully: {filename}")
                messages.success(request, 'Audio zostało wygenerowane.')
            else:
                print("[DETAIL] Error: No audio data received")
                messages.error(request, 'Błąd podczas generowania audio.')
        except Exception as e:
            print(f"[DETAIL] Error generating audio: {e}")
            messages.error(request, 'Błąd podczas generowania audio.')
        return redirect('document_detail', uuid=document.uuid)

    audio_exists = False
    audio_url = None
    audio_size = 0
    audio_size_formatted = "0 B"

    if document.ai_audio:
        try:
            audio_url = document.ai_audio.url
            audio_exists = True
            audio_size = document.ai_audio.size
            audio_size_formatted = format_file_size(audio_size)
            print(f"[DETAIL] Audio size: {audio_size} bytes ({audio_size_formatted})")
        except Exception as e:
            print(f"Error getting audio info: {str(e)}")
            audio_exists = False

    context = {
        'document': document,
        'file_exists': file_exists,
        'file_url': file_url,
        'file_size': file_size,
        'file_size_formatted': file_size_formatted,
        'audio_exists': audio_exists,
        'audio_url': audio_url,
        'audio_size': audio_size,
        'audio_size_formatted': audio_size_formatted,
    }

    return render(request, 'dashboard/document_detail.html', context)


@login_required
def create_document(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        print(f"[CREATE] POST data: {dict(request.POST)}")
        print(f"[CREATE] FILES data: {list(request.FILES.keys())}")

        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)

            if 'file' in request.FILES:
                file = request.FILES['file']
                document.file_type = os.path.splitext(file.name)[1][1:].lower()
                print(f"[CREATE] File uploaded: {file.name}, type: {document.file_type}")

            document.save()
            document.users.add(user_profile)
            form.save_m2m()
            print(f"[CREATE] Document saved with ID: {document.id}")

            if 'file' in request.FILES:
                generate_audio_raw = request.POST.get('generate_audio', '')
                print(f"[CREATE] generate_audio raw value: '{generate_audio_raw}'")

                if generate_audio_raw == 'on':
                    generate_audio = True
                elif generate_audio_raw in ['true', 'True', '1']:
                    generate_audio = True
                elif generate_audio_raw in ['false', 'False', '0', '', None]:
                    generate_audio = False
                else:
                    generate_audio = bool(generate_audio_raw)

                print(f"[CREATE] generate_audio final value: {generate_audio}")

                try:
                    print(f"[CREATE] Starting AI analysis for document {document.id}")
                    ai_description = analyze_document(document.file, document.file_type)

                    if ai_description:
                        document.ai_description = ai_description
                        document.save()
                        print(f"[CREATE] AI description generated: {len(ai_description)} characters")

                        if generate_audio:
                            print("[CREATE] Starting audio generation")
                            result = generate_speech(ai_description)
                            if result and "audio_data" in result:
                                filename = f"audio_{document.uuid}.wav"
                                document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)
                                print(f"[CREATE] Audio generated successfully: {filename}")
                                messages.success(request,
                                                 f'Dokument "{document.title}" został utworzony. Opis AI i audio zostały wygenerowane.')
                            else:
                                print("[CREATE] Error: No audio data received")
                                messages.success(request,
                                                 f'Dokument "{document.title}" został utworzony z opisem AI, ale wystąpił błąd podczas generowania audio.')
                        else:
                            messages.success(request, f'Dokument "{document.title}" został utworzony z opisem AI.')
                    else:
                        print("[CREATE] AI description generation failed")
                        messages.warning(request,
                                         f'Dokument "{document.title}" został utworzony, ale nie udało się wygenerować opisu AI.')

                except Exception as e:
                    print(f"[CREATE] Error during AI processing: {e}")
                    messages.warning(request,
                                     f'Dokument "{document.title}" został utworzony, ale wystąpił błąd podczas przetwarzania AI.')
            else:
                print("[CREATE] No file uploaded")
                messages.success(request, f'Dokument "{document.title}" został utworzony.')

            return redirect('document_detail', uuid=document.uuid)
        else:
            print(f"[CREATE] Form errors: {form.errors}")
    else:
        project_id = request.GET.get('project')
        team_id = request.GET.get('team')
        initial = {}

        if project_id:
            try:
                initial['project'] = Project.objects.get(uuid=project_id)
                print(f"[CREATE] Pre-selected project: {initial['project']}")
            except Project.DoesNotExist:
                print(f"[CREATE] Project not found: {project_id}")

        if team_id:
            try:
                initial['team'] = Team.objects.get(uuid=team_id)
                print(f"[CREATE] Pre-selected team: {initial['team']}")
            except Team.DoesNotExist:
                print(f"[CREATE] Team not found: {team_id}")

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
        print(f"[EDIT] Document: {document.title} (ID: {document.id})")
        print(f"[EDIT] POST data: {dict(request.POST)}")
        print(f"[EDIT] FILES data: {list(request.FILES.keys())}")
        print(f"[EDIT] Existing audio: {bool(document.ai_audio)}")
        print(f"[EDIT] Existing ai_description: {bool(document.ai_description)}")

        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)

            generate_audio_raw = request.POST.get('generate_audio', '')
            print(f"[EDIT] generate_audio raw value: '{generate_audio_raw}'")

            if generate_audio_raw == 'on':
                generate_audio = True
            elif generate_audio_raw in ['true', 'True', '1']:
                generate_audio = True
            elif generate_audio_raw in ['false', 'False', '0', '', None]:
                generate_audio = False
            else:
                generate_audio = bool(generate_audio_raw)

            print(f"[EDIT] generate_audio final value: {generate_audio}")

            new_file_uploaded = False

            if 'file' in request.FILES:
                file = request.FILES['file']
                document.file_type = os.path.splitext(file.name)[1][1:].lower()
                print(f"[EDIT] New file uploaded: {file.name}, type: {document.file_type}")
                new_file_uploaded = True

                if document.ai_audio:
                    print(f"[EDIT] Deleting existing audio: {document.ai_audio.name}")
                    document.ai_audio.delete(save=False)
                    document.ai_audio = None

                document.ai_description = None
                print("[EDIT] Reset ai_description due to new file")

            document.save()
            form.save_m2m()
            print(f"[EDIT] Document saved")

            if new_file_uploaded:
                print(f"[EDIT] Starting full document processing with new file")
                try:
                    ai_description = analyze_document(document.file, document.file_type)

                    if ai_description:
                        document.ai_description = ai_description
                        document.save()
                        print(f"[EDIT] AI description generated: {len(ai_description)} characters")

                        if generate_audio:
                            print("[EDIT] Starting audio generation for new file")
                            result = generate_speech(ai_description)
                            if result and "audio_data" in result:
                                filename = f"audio_{document.uuid}.wav"
                                document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)
                                print(f"[EDIT] Audio generated successfully: {filename}")
                                messages.success(request,
                                                 f'Dokument "{document.title}" został zaktualizowany. Opis AI i audio zostały wygenerowane.')
                            else:
                                print("[EDIT] Error: No audio data received")
                                messages.success(request,
                                                 f'Dokument "{document.title}" został zaktualizowany z opisem AI, ale wystąpił błąd podczas generowania audio.')
                        else:
                            messages.success(request, f'Dokument "{document.title}" został zaktualizowany z opisem AI.')
                    else:
                        print("[EDIT] AI description generation failed")
                        messages.warning(request,
                                         f'Dokument "{document.title}" został zaktualizowany, ale nie udało się wygenerować opisu AI.')

                except Exception as e:
                    print(f"[EDIT] Error during AI processing: {e}")
                    messages.warning(request,
                                     f'Dokument "{document.title}" został zaktualizowany, ale wystąpił błąd podczas przetwarzania AI.')

            elif generate_audio and document.ai_description and not document.ai_audio:
                print(f"[EDIT] Generating audio for existing description (no new file)")
                try:
                    result = generate_speech(document.ai_description)
                    if result and "audio_data" in result:
                        filename = f"audio_{document.uuid}.wav"
                        document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)
                        print(f"[EDIT] Audio generated successfully: {filename}")
                        messages.success(request,
                                         f'Dokument "{document.title}" został zaktualizowany. Audio zostało wygenerowane.')
                    else:
                        print("[EDIT] Error: No audio data received")
                        messages.error(request,
                                       f'Dokument "{document.title}" został zaktualizowany, ale wystąpił błąd podczas generowania audio.')
                except Exception as e:
                    print(f"[EDIT] Error generating audio: {e}")
                    messages.error(request,
                                   f'Dokument "{document.title}" został zaktualizowany, ale wystąpił błąd podczas generowania audio.')

            elif generate_audio and not document.ai_description:
                print(f"[EDIT] Cannot generate audio - no AI description available")
                messages.warning(request,
                                 f'Dokument "{document.title}" został zaktualizowany, ale nie można wygenerować audio - brak opisu AI.')

            elif generate_audio and document.ai_audio:
                print(f"[EDIT] Audio already exists, not regenerating")
                messages.info(request, f'Dokument "{document.title}" został zaktualizowany. Audio już istnieje.')

            else:
                print("[EDIT] Simple update without audio generation")
                messages.success(request, f'Dokument "{document.title}" został zaktualizowany.')

            return redirect('document_detail', uuid=document.uuid)
        else:
            print(f"[EDIT] Form errors: {form.errors}")
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
        print(f"[DELETE] Deleting document: {document_title} (ID: {document.id})")

        if document.file:
            print(f"[DELETE] Deleting file: {document.file.name}")
            try:
                document.file.delete(save=False)
            except Exception as e:
                print(f"[DELETE] Error deleting file: {e}")

        if document.ai_audio:
            print(f"[DELETE] Deleting audio: {document.ai_audio.name}")
            try:
                document.ai_audio.delete(save=False)
            except Exception as e:
                print(f"[DELETE] Error deleting audio: {e}")

        document.delete()
        print(f"[DELETE] Document deleted successfully")

        messages.success(request, f'Dokument "{document_title}" został usunięty.')
        return redirect('document_list')

    context = {
        'document': document,
    }

    return render(request, 'dashboard/document_delete_confirm.html', context)


def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"