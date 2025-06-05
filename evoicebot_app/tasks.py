import os
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings

from .api.openai import analyze_document, generate_speech
from .models import Document


@shared_task
def process_document_ai(document_id, generate_audio=False):
    try:
        document = Document.objects.get(id=document_id)

        if document.file:
            file_type = os.path.splitext(document.file.name)[1][1:].lower()

            ai_description = analyze_document(document.file, file_type)
            if ai_description:
                document.ai_description = ai_description
                document.save()

                if generate_audio:
                    result = generate_speech(ai_description)
                    filename = f"audio_{document.uuid}.wav"
                    document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)

        return f"Document {document.title} processed successfully"
    except Exception as e:
        return f"Error processing document: {str(e)}"


@shared_task
def generate_document_audio(document_id):
    try:
        document = Document.objects.get(id=document_id)

        if document.ai_description and not document.ai_audio:
            result = generate_speech(document.ai_description)
            filename = f"audio_{document.uuid}.wav"
            document.ai_audio.save(filename, ContentFile(result["audio_data"]), save=True)
            return f"Audio generated for document {document.title}"

        return "No description found or audio already exists"
    except Exception as e:
        return f"Error generating audio: {str(e)}"


@shared_task
def send_notification_email(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email sent to {len(recipient_list)} recipients"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def cleanup_old_files():
    from datetime import datetime, timedelta
    from django.utils import timezone

    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        old_documents = Document.objects.filter(
            created_at__lt=cutoff_date,
            ai_audio__isnull=False
        )

        count = 0
        for doc in old_documents:
            if doc.ai_audio:
                doc.ai_audio.delete()
                count += 1

        return f"Cleaned up {count} old audio files"
    except Exception as e:
        return f"Error cleaning up files: {str(e)}"


@shared_task
def bulk_process_documents(document_ids, generate_audio=False):
    results = []
    for doc_id in document_ids:
        result = process_document_ai.delay(doc_id, generate_audio)
        results.append(result.id)

    return f"Started processing {len(document_ids)} documents. Task IDs: {results}"


@shared_task
def send_document_expiry_notifications():
    from datetime import date, timedelta
    from django.contrib.auth.models import User

    try:
        tomorrow = date.today() + timedelta(days=1)
        expiring_docs = Document.objects.filter(deadline=tomorrow)

        notifications_sent = 0
        for doc in expiring_docs:
            users = doc.users.all()
            if users:
                recipient_emails = [user.user.email for user in users if user.user.email]
                if recipient_emails:
                    send_notification_email.delay(
                        subject=f"Dokument '{doc.title}' wygasa jutro",
                        message=f"Dokument '{doc.title}' wygasa {doc.deadline}. Sprawdź czy wymaga odnowienia.",
                        recipient_list=recipient_emails
                    )
                    notifications_sent += 1

        return f"Sent {notifications_sent} expiry notifications"
    except Exception as e:
        return f"Error sending expiry notifications: {str(e)}"