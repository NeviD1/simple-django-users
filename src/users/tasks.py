from celery import shared_task

from .services import send_admin_daily_mail, send_mail_for_new_users


@shared_task
def send_mail_for_new_users_task(emails: list[str]) -> None:
    send_mail_for_new_users(emails)


@shared_task
def send_admin_daily_mail_task() -> None:
    send_admin_daily_mail()
