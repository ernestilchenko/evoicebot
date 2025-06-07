import re

from django.core.exceptions import ValidationError


def validate_phone_number(phone_number):
    phone_pattern = r'^\+?[1-9]\d{1,14}$'

    if not re.match(phone_pattern, phone_number):
        raise ValidationError(f'Invalid phone number format: {phone_number}')

    return phone_number


def format_phone_number(phone_number, country_code='+48'):
    phone_number = re.sub(r'[^\d+]', '', phone_number)

    if phone_number.startswith('0'):
        phone_number = country_code + phone_number[1:]
    elif not phone_number.startswith('+'):
        if not phone_number.startswith('48'):
            phone_number = country_code + phone_number
        else:
            phone_number = '+' + phone_number

    return phone_number


def parse_phone_numbers(phone_numbers_string):
    phone_numbers = []

    for phone in phone_numbers_string.split(','):
        phone = phone.strip()
        if phone:
            try:
                formatted_phone = format_phone_number(phone)
                validate_phone_number(formatted_phone)
                phone_numbers.append(formatted_phone)
            except ValidationError:
                continue

    return phone_numbers


def estimate_call_cost(message_length, num_calls, cost_per_minute=0.02):
    estimated_duration = max(1, message_length // 10)
    estimated_cost = estimated_duration * cost_per_minute * num_calls
    return round(estimated_cost, 2)


def create_voice_message(document=None, custom_message=None, include_instructions=True):
    if custom_message:
        message = custom_message
    elif document:
        message = f"Masz nowy dokument: {document.title}."
        if document.ai_description:
            message += f" {document.ai_description[:200]}"
        if document.deadline:
            message += f" Dokument ważny do {document.deadline.strftime('%d %B %Y')}."
    else:
        message = "Masz nowe powiadomienie z systemu EvoiceBot."

    if include_instructions:
        message += " Naciśnij 1 aby potwierdzić otrzymanie wiadomości."

    return message


def get_call_status_display(status):
    status_map = {
        'initiated': 'Zainicjowane',
        'ringing': 'Dzwoni',
        'in-progress': 'W toku',
        'completed': 'Zakończone',
        'busy': 'Zajęty',
        'no-answer': 'Brak odpowiedzi',
        'failed': 'Nieudane',
        'canceled': 'Anulowane'
    }
    return status_map.get(status, status)


def should_retry_call(status):
    retry_statuses = ['busy', 'no-answer', 'failed']
    return status in retry_statuses


def get_team_phone_numbers(team):
    from ..models import TeamMembership

    memberships = TeamMembership.objects.filter(team=team).select_related('user_profile')
    phone_numbers = []

    for membership in memberships:
        if membership.user_profile.phone:
            try:
                formatted_phone = format_phone_number(membership.user_profile.phone)
                validate_phone_number(formatted_phone)
                phone_numbers.append(formatted_phone)
            except ValidationError:
                continue

    return phone_numbers


def get_document_recipients_phones(document):
    phone_numbers = []

    for user_profile in document.users.all():
        if user_profile.phone:
            try:
                formatted_phone = format_phone_number(user_profile.phone)
                validate_phone_number(formatted_phone)
                phone_numbers.append(formatted_phone)
            except ValidationError:
                continue

    if document.team:
        team_phones = get_team_phone_numbers(document.team)
        phone_numbers.extend(team_phones)

    return list(set(phone_numbers))
