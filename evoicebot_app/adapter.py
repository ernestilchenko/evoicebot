import re

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):

        user = super().populate_user(request, sociallogin, data)
        if not user.username and sociallogin.account.provider == 'telegram':
            telegram_data = sociallogin.account.extra_data
            if 'username' in telegram_data and telegram_data['username']:
                telegram_username = telegram_data['username']
                user.username = self._clean_username(telegram_username)
            elif 'first_name' in telegram_data:
                first_name = telegram_data.get('first_name', '')
                last_name = telegram_data.get('last_name', '')

                if first_name and last_name:
                    candidate = f"{first_name.lower()}_{last_name.lower()}"
                elif first_name:
                    candidate = first_name.lower()
                else:
                    candidate = f"tg_user_{telegram_data.get('id', '')}"

                user.username = self._clean_username(candidate)

        return user

    def _clean_username(self, username):
        username = re.sub(r'[^\w\.]', '_', username)

        if len(username) > 150:
            username = username[:150]

        return username

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        return user
