from django.conf import settings
from django.urls import reverse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse


class TwilioService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.client = Client(self.account_sid, self.auth_token)

    def make_call(self, to_number, message_text, document=None, user_profile=None):
        from ..models import VoiceCall

        try:
            twiml_content = self.generate_twiml_response(message_text)

            call = self.client.calls.create(
                twiml=twiml_content,
                to=to_number,
                from_=self.phone_number,
            )

            voice_call = VoiceCall.objects.create(
                sid=call.sid,
                to_number=to_number,
                from_number=self.phone_number,
                message_text=message_text,
                document=document,
                user_profile=user_profile,
                status='initiated'
            )

            return voice_call
        except Exception as e:
            print(f"Error making call: {str(e)}")
            return None

    def get_call_status(self, call_sid):
        try:
            call = self.client.calls(call_sid).fetch()
            return call.status
        except Exception as e:
            print(f"Error fetching call status: {str(e)}")
            return None

    def end_call(self, call_sid):
        try:
            call = self.client.calls(call_sid).update(status='completed')
            return call.status
        except Exception as e:
            print(f"Error ending call: {str(e)}")
            return None

    def generate_twiml_response(self, message_text):
        response = VoiceResponse()

        gather = response.gather(
            num_digits=1,
            action=f"{settings.SITE_URL}{reverse('twilio_gather')}",
            method='POST',
            timeout=10
        )

        gather.say(message_text, language='pl-PL')
        gather.pause(length=1)
        gather.say("Naciśnij 1 aby potwierdzić otrzymanie wiadomości, lub rozłącz się.",
                   language='pl-PL')

        response.redirect(f"{settings.SITE_URL}{reverse('twilio_no_input')}")

        return str(response)

    def send_document_notification(self, document, phone_numbers):
        calls = []
        message = f"Masz nowy dokument: {document.title}."
        if document.ai_description:
            message += f" {document.ai_description[:200]}"

        for phone_number in phone_numbers:
            call = self.make_call(
                to_number=phone_number,
                message_text=message,
                document=document
            )
            if call:
                calls.append(call)

        return calls

    def send_deadline_reminder(self, document, phone_numbers):
        calls = []
        message = f"Przypomnienie: dokument {document.title} wygasa {document.deadline.strftime('%d.%m.%Y')}."

        for phone_number in phone_numbers:
            call = self.make_call(
                to_number=phone_number,
                message_text=message,
                document=document
            )
            if call:
                calls.append(call)

        return calls

    def send_custom_message(self, phone_numbers, message_text, user_profile=None):
        calls = []

        for phone_number in phone_numbers:
            call = self.make_call(
                to_number=phone_number,
                message_text=message_text,
                user_profile=user_profile
            )
            if call:
                calls.append(call)

        return calls
