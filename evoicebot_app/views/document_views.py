import base64
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from openai import OpenAI

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
            document = form.save(commit=False)

            # Process file with OpenAI if there's a file
            if 'file' in request.FILES:
                file = request.FILES['file']

                # Save the file type for document
                document.file_type = os.path.splitext(file.name)[1][1:].lower()

                # Read file data for OpenAI processing
                file_data = file.read()
                file.seek(0)  # Reset file pointer after reading

                # Only process if file isn't too large (10MB limit) and has valid file type
                if len(file_data) < 10 * 1024 * 1024 and document.file_type in ['pdf', 'txt', 'doc', 'docx']:
                    try:
                        # Convert to base64
                        base64_string = base64.b64encode(file_data).decode("utf-8")

                        # Determine MIME type based on extension
                        mime_type = "application/pdf"  # Default
                        if document.file_type == 'txt':
                            mime_type = "text/plain"
                        elif document.file_type in ['doc', 'docx']:
                            mime_type = "application/msword"

                        # Initialize OpenAI client
                        client = OpenAI(api_key=settings.OPENAI_API_KEY)

                        # Send to OpenAI
                        response = client.responses.create(
                            model="gpt-4.1",
                            input=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_file",
                                            "filename": file.name,
                                            "file_data": f"data:{mime_type};base64,{base64_string}",
                                        },
                                        {
                                            "type": "input_text",
                                            "text": "Przeanalizuj treść tego dokumentu i napisz krótkie streszczenie jego zawartości w języku polskim (maksymalnie 100 słów).",
                                        },
                                    ],
                                },
                            ]
                        )

                        # Get the description and save it
                        document.ai_description = response.output_text

                    except Exception as e:
                        # Log the error but continue saving the document
                        print(f"Error processing document with AI: {e}")

            # Save the document
            document.save()
            document.users.add(user_profile)  # Add current user
            form.save_m2m()  # Save many-to-many relationships

            messages.success(request, f'Dokument "{document.title}" został pomyślnie utworzony.')
            return redirect('document_detail', uuid=document.uuid)
    else:
        # Handle pre-filled project and team
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

    # Filter available projects and teams
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

    # Check if user has permissions to edit
    is_creator = document.users.filter(id=user_profile.id).exists()
    is_admin = user_profile.role == 'admin'

    if not (is_creator or is_admin):
        messages.error(request, 'Nie masz uprawnień do edycji tego dokumentu.')
        return redirect('document_detail', uuid=document.uuid)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)

            # Process file with OpenAI if a new file is uploaded
            if 'file' in request.FILES:
                file = request.FILES['file']

                # Save the file type for document
                document.file_type = os.path.splitext(file.name)[1][1:].lower()

                # Read file data for OpenAI processing
                file_data = file.read()
                file.seek(0)  # Reset file pointer after reading

                # Only process if file isn't too large (10MB limit) and has valid file type
                if len(file_data) < 10 * 1024 * 1024 and document.file_type in ['pdf', 'txt', 'doc', 'docx']:
                    try:
                        # Convert to base64
                        base64_string = base64.b64encode(file_data).decode("utf-8")

                        # Determine MIME type based on extension
                        mime_type = "application/pdf"  # Default
                        if document.file_type == 'txt':
                            mime_type = "text/plain"
                        elif document.file_type in ['doc', 'docx']:
                            mime_type = "application/msword"

                        # Initialize OpenAI client
                        client = OpenAI(api_key=settings.OPENAI_API_KEY)

                        # Send to OpenAI
                        response = client.responses.create(
                            model="gpt-4.1",
                            input=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_file",
                                            "filename": file.name,
                                            "file_data": f"data:{mime_type};base64,{base64_string}",
                                        },
                                        {
                                            "type": "input_text",
                                            "text": "Przeanalizuj treść tego dokumentu i napisz krótkie streszczenie jego zawartości w języku polskim (maksymalnie 100 słów).",
                                        },
                                    ],
                                },
                            ]
                        )

                        # Get the description and save it
                        document.ai_description = response.output_text

                    except Exception as e:
                        # Log the error but continue saving the document
                        print(f"Error processing document with AI: {e}")

            # Save the document and other relationships
            document.save()
            form.save_m2m()

            messages.success(request, f'Dokument "{document.title}" został zaktualizowany.')
            return redirect('document_detail', uuid=document.uuid)
    else:
        form = DocumentForm(instance=document)

    # Filter available projects and teams
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
