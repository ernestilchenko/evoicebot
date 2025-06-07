from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from twilio.twiml.voice_response import VoiceResponse

from ..api.twilio_service import TwilioService
from ..models import VoiceCall, Document, UserProfile, TeamMembership


@login_required
def voice_call_list(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if user_profile.role == 'admin':
        calls = VoiceCall.objects.all()
    else:
        calls = VoiceCall.objects.filter(user_profile=user_profile)

    context = {
        'calls': calls,
    }

    return render(request, 'dashboard/voice_call_list.html', context)


@login_required
def voice_call_detail(request, call_id):
    call = get_object_or_404(VoiceCall, id=call_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if user_profile.role != 'admin' and call.user_profile != user_profile:
        messages.error(request, 'Nie masz dostępu do tego połączenia.')
        return redirect('voice_call_list')

    call.update_status_from_twilio()

    context = {
        'call': call,
    }

    return render(request, 'dashboard/voice_call_detail.html', context)


@login_required
def make_voice_call(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        phone_numbers = request.POST.get('phone_numbers', '').split(',')
        message_text = request.POST.get('message_text', '')
        document_uuid = request.POST.get('document_uuid', '')

        phone_numbers = [num.strip() for num in phone_numbers if num.strip()]

        if not phone_numbers or not message_text:
            messages.error(request, 'Numer telefonu i treść wiadomości są wymagane.')
            return redirect('make_voice_call')

        service = TwilioService()
        document = None

        if document_uuid:
            try:
                document = Document.objects.get(uuid=document_uuid)
            except Document.DoesNotExist:
                pass

        calls = service.send_custom_message(phone_numbers, message_text, user_profile)

        if calls:
            messages.success(request, f'Zainicjowano {len(calls)} połączeń głosowych.')
        else:
            messages.error(request, 'Nie udało się zainicjować połączeń.')

        return redirect('voice_call_list')

    documents = Document.objects.filter(users=user_profile)

    context = {
        'documents': documents,
    }

    return render(request, 'dashboard/make_voice_call.html', context)


@login_required
def document_voice_notification(request, document_uuid):
    document = get_object_or_404(Document, uuid=document_uuid)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    has_access = (
            document.users.filter(id=user_profile.id).exists() or
            (document.team and document.team in user_profile.get_teams()) or
            (document.project and document.project.teams.filter(memberships__user_profile=user_profile).exists())
    )

    if not has_access and user_profile.role != 'admin':
        messages.error(request, 'Nie masz dostępu do tego dokumentu.')
        return redirect('document_list')

    if request.method == 'POST':
        phone_numbers = request.POST.get('phone_numbers', '').split(',')
        phone_numbers = [num.strip() for num in phone_numbers if num.strip()]

        if not phone_numbers:
            messages.error(request, 'Wprowadź numery telefonów.')
            return redirect('document_voice_notification', document_uuid=document_uuid)

        service = TwilioService()
        calls = service.send_document_notification(document, phone_numbers)

        if calls:
            messages.success(request, f'Wysłano powiadomienia głosowe na {len(calls)} numerów.')
        else:
            messages.error(request, 'Nie udało się wysłać powiadomień.')

        return redirect('document_detail', uuid=document_uuid)

    team_phones = []
    if document.team:
        memberships = TeamMembership.objects.filter(team=document.team)
        team_phones = [m.user_profile.phone for m in memberships if m.user_profile.phone]

    context = {
        'document': document,
        'team_phones': team_phones,
    }

    return render(request, 'dashboard/document_voice_notification.html', context)


@csrf_exempt
def twilio_twiml(request):
    message_text = request.GET.get('message', 'Brak wiadomości')

    service = TwilioService()
    twiml_response = service.generate_twiml_response(message_text)

    return HttpResponse(twiml_response, content_type='text/xml')


@csrf_exempt
@require_POST
def twilio_gather(request):
    digit_pressed = request.POST.get('Digits')
    call_sid = request.POST.get('CallSid')

    response = VoiceResponse()

    if digit_pressed == '1':
        response.say("Dziękujemy za potwierdzenie. Do widzenia.", voice='alice', language='pl')

        try:
            call = VoiceCall.objects.get(sid=call_sid)
            call.confirmation_received = True
            call.save()
        except VoiceCall.DoesNotExist:
            pass
    else:
        response.say("Nieprawidłowa opcja. Do widzenia.", voice='alice', language='pl')

    response.hangup()
    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
def twilio_no_input(request):
    response = VoiceResponse()
    response.say("Nie otrzymaliśmy odpowiedzi. Do widzenia.", voice='alice', language='pl')
    response.hangup()

    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
@require_POST
def twilio_status_callback(request):
    call_sid = request.POST.get('CallSid')
    call_status = request.POST.get('CallStatus')
    call_duration = request.POST.get('CallDuration')

    try:
        call = VoiceCall.objects.get(sid=call_sid)
        call.status = call_status

        if call_duration:
            call.duration = int(call_duration)

        if call_status in ['completed', 'busy', 'no-answer', 'failed', 'canceled']:
            from django.utils import timezone
            call.ended_at = timezone.now()

        call.save()
    except VoiceCall.DoesNotExist:
        pass

    return HttpResponse('OK')


@login_required
def update_call_status(request, call_id):
    call = get_object_or_404(VoiceCall, id=call_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if user_profile.role != 'admin' and call.user_profile != user_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    new_status = call.update_status_from_twilio()

    return JsonResponse({
        'status': new_status or call.status,
        'duration': call.duration,
        'confirmation_received': call.confirmation_received
    })


@login_required
def end_call(request, call_id):
    call = get_object_or_404(VoiceCall, id=call_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if user_profile.role != 'admin' and call.user_profile != user_profile:
        messages.error(request, 'Nie masz uprawnień do zakończenia tego połączenia.')
        return redirect('voice_call_detail', call_id=call_id)

    if call.status in ['initiated', 'ringing', 'in-progress']:
        service = TwilioService()
        result = service.end_call(call.sid)

        if result:
            call.status = 'canceled'
            call.save()
            messages.success(request, 'Połączenie zostało zakończone.')
        else:
            messages.error(request, 'Nie udało się zakończyć połączenia.')
    else:
        messages.info(request, 'To połączenie już zostało zakończone.')

    return redirect('voice_call_detail', call_id=call_id)
