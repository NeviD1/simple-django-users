from app.services import send_mail


def send_mail_for_new_users(emails: list[str]) -> None:
    subject = "Подтвердите регистрацию"
    message = "Чтобы подтвердить регистрацию, перейдите по ссылке: ..."
    for email in emails:
        send_mail(subject=subject, message=message, email_to=email)
