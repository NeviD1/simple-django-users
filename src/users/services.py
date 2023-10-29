from .models import User
from app.services import send_mail


def send_mail_for_new_users(emails: list[str]) -> None:
    subject = "Подтвердите регистрацию"
    message = "Чтобы подтвердить регистрацию, перейдите по ссылке: ..."
    for email in emails:
        send_mail(subject=subject, message=message, email_to=email)


def send_admin_daily_mail() -> None:
    active_user_count = get_active_user_count()
    subject = "Количество активных пользователей"
    message = f"Количество активных пользователей: {active_user_count}"
    admin_emails = get_admin_emails()
    send_mail(subject=subject, message=message, email_to=admin_emails)


def get_active_user_count() -> int:
    return User.objects.filter(is_active=True).count()


def get_admin_emails() -> list[str]:
    return list(User.objects.filter(is_superuser=True, is_active=True).values_list("email", flat=True))
