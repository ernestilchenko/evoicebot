from datetime import timedelta


def get_document_recipients_emails(document):
    emails = []

    for user_profile in document.users.all():
        if user_profile.user.email:
            emails.append(user_profile.user.email)

    if document.team:
        team_members = document.team.memberships.all()
        for membership in team_members:
            if membership.user_profile.user.email:
                emails.append(membership.user_profile.user.email)

    if document.project:
        for team in document.project.teams.all():
            team_members = team.memberships.all()
            for membership in team_members:
                if membership.user_profile.user.email:
                    emails.append(membership.user_profile.user.email)

    return list(set(emails))


def schedule_deadline_alerts(document):
    from datetime import datetime, time
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    import json

    if not document.deadline:
        return

    deadline_date = document.deadline
    alert_date = deadline_date - timedelta(days=1)

    schedule, created = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=9,
        day_of_month=alert_date.day,
        month_of_year=alert_date.month,
    )

    task_name = f"deadline_alert_{document.uuid}"

    PeriodicTask.objects.update_or_create(
        name=task_name,
        defaults={
            'crontab': schedule,
            'task': 'evoicebot_app.tasks.send_immediate_deadline_alert',
            'args': json.dumps([document.id]),
            'one_off': True,
        }
    )


def cancel_deadline_alerts(document):
    from django_celery_beat.models import PeriodicTask

    task_name = f"deadline_alert_{document.uuid}"
    PeriodicTask.objects.filter(name=task_name).delete()