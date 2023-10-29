import logging

from django.conf import settings
from django.core.mail import EmailMessage


logger = logging.getLogger(__name__)


def send_mail(
    subject: str, message: str, email_to: list[str] | str, attach_file_paths: list[str] | None = None
) -> bool:
    if isinstance(email_to, str):
        email_to = [email_to]

    email = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_USER, to=email_to)
    if attach_file_paths:
        for attach_file_path in attach_file_paths:
            email.attach_file(attach_file_path)

    logger.debug("Отправка сообщения на %s: %s. attach_file_paths=%s", email_to, subject, attach_file_paths)
    try:
        result = email.send()
    except Exception as e:  # pylint: disable=broad-exception-caught
        result = 0
        logger.error(e)

    success = result == 1
    if not success:
        logger.error("Не удалось отправить сообщение на %s: %s", email_to, subject)
    return success
