import os
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone

from .api.openai import analyze_document, generate_speech
from .api.twilio_service import TwilioService
from .models import Document, VoiceCall
from .utils.twilio_utils import create_voice_message, get_document_recipients_phones


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
    from datetime import timedelta
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


def send_deadline_reminders():
    tomorrow = timezone.now().date() + timedelta(days=1)
    next_week = timezone.now().date() + timedelta(days=7)

    documents_tomorrow = Document.objects.filter(deadline=tomorrow)
    documents_next_week = Document.objects.filter(deadline=next_week)

    service = TwilioService()
    calls_sent = 0

    for document in documents_tomorrow:
        phone_numbers = get_document_recipients_phones(document)
        if phone_numbers:
            message = create_voice_message(document)
            message = f"PILNE: {message} Termin upływa jutro!"

            calls = service.send_custom_message(phone_numbers, message)
            calls_sent += len(calls) if calls else 0

    for document in documents_next_week:
        phone_numbers = get_document_recipients_phones(document)
        if phone_numbers:
            message = create_voice_message(document)
            message = f"Przypomnienie: {message} Termin upływa za tydzień."

            calls = service.send_custom_message(phone_numbers, message)
            calls_sent += len(calls) if calls else 0

    return calls_sent


def check_failed_calls_and_retry():
    failed_calls = VoiceCall.objects.filter(
        status__in=['failed', 'busy', 'no-answer'],
        created_at__gte=timezone.now() - timedelta(hours=1)
    )

    service = TwilioService()
    retried_calls = 0

    for call in failed_calls:
        if call.status == 'failed':
            continue

        new_call = service.make_call(
            to_number=call.to_number,
            message_text=call.message_text,
            document=call.document,
            user_profile=call.user_profile
        )

        if new_call:
            retried_calls += 1

    return retried_calls


def update_call_statuses():
    active_calls = VoiceCall.objects.filter(
        status__in=['initiated', 'ringing', 'in-progress']
    )

    updated_count = 0

    for call in active_calls:
        old_status = call.status
        call.update_status_from_twilio()

        if call.status != old_status:
            updated_count += 1

    return updated_count


def send_daily_report():
    yesterday = timezone.now().date() - timedelta(days=1)

    calls_yesterday = VoiceCall.objects.filter(
        created_at__date=yesterday
    )

    total_calls = calls_yesterday.count()
    completed_calls = calls_yesterday.filter(status='completed').count()
    confirmed_calls = calls_yesterday.filter(confirmation_received=True).count()

    report = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'total_calls': total_calls,
        'completed_calls': completed_calls,
        'confirmed_calls': confirmed_calls,
        'success_rate': round((completed_calls / total_calls * 100) if total_calls > 0 else 0, 2),
        'confirmation_rate': round((confirmed_calls / completed_calls * 100) if completed_calls > 0 else 0, 2)
    }

    return report


def cleanup_old_calls():
    old_date = timezone.now() - timedelta(days=90)

    old_calls = VoiceCall.objects.filter(
        created_at__lt=old_date,
        status__in=['completed', 'failed', 'canceled']
    )

    deleted_count = old_calls.count()
    old_calls.delete()

    return deleted_count


def send_document_notifications_batch(document_ids, phone_numbers, custom_message=None):
    service = TwilioService()
    results = []

    for doc_id in document_ids:
        try:
            document = Document.objects.get(id=doc_id)
            message = custom_message or create_voice_message(document)

            calls = service.send_custom_message(phone_numbers, message)

            results.append({
                'document_id': doc_id,
                'document_title': document.title,
                'calls_sent': len(calls) if calls else 0,
                'success': bool(calls)
            })
        except Document.DoesNotExist:
            results.append({
                'document_id': doc_id,
                'error': 'Document not found',
                'success': False
            })

    return results
