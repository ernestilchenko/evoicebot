import re

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social accounts that automatically generates usernames
    based on data from social providers like Telegram.
    """

    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social account.
        """
        user = super().populate_user(request, sociallogin, data)

        # If the user doesn't have a username yet, and the data has one (like from Telegram)
        if not user.username and sociallogin.account.provider == 'telegram':
            # Try to get username from Telegram data
            telegram_data = sociallogin.account.extra_data
            if 'username' in telegram_data and telegram_data['username']:
                # Use Telegram username directly
                telegram_username = telegram_data['username']
                user.username = self._clean_username(telegram_username)
            elif 'first_name' in telegram_data:
                # Create username from first name and possibly last name
                first_name = telegram_data.get('first_name', '')
                last_name = telegram_data.get('last_name', '')

                if first_name and last_name:
                    candidate = f"{first_name.lower()}_{last_name.lower()}"
                elif first_name:
                    candidate = first_name.lower()
                else:
                    # Fallback to ID-based username
                    candidate = f"tg_user_{telegram_data.get('id', '')}"

                user.username = self._clean_username(candidate)

        return user

    def _clean_username(self, username):
        """
        Clean username to ensure it meets Django requirements.
        """
        # Replace spaces with underscores and remove special characters
        username = re.sub(r'[^\w\.]', '_', username)

        # Ensure username is at most 150 characters (Django User model limitation)
        if len(username) > 150:
            username = username[:150]

        return username
