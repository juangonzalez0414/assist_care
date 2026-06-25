import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def make_email_detail(label, value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return {'label': str(label).strip(), 'value': text}


def compact_email_details(*items):
    return [item for item in items if item and item.get('value')]


def send_html_email(*, subject, to, template_name, context, from_email=None):
    to_list = [to] if isinstance(to, str) else list(to)
    if not to_list:
        return False

    html_body = render_to_string(template_name, context)
    text_body = render_to_string(template_name, {**context, 'plain_text': True})

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to_list,
    )
    msg.attach_alternative(html_body, 'text/html')

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Error enviando correo: %s → %s", subject, to_list)
        return False


def send_notification_email(
    *,
    subject,
    to,
    headline,
    message,
    status_label='Notificacion',
    details=None,
    cta_text='Abrir Assist Care',
    cta_url='',
    footer_note='Este es un correo automatico de Assist Care.',
    from_email=None,
):
    return send_html_email(
        subject=subject,
        to=to,
        from_email=from_email,
        template_name='emails/notificacion_general.html',
        context={
            'status_label': status_label,
            'headline': headline,
            'message': message,
            'details': details or [],
            'cta_text': cta_text,
            'cta_url': cta_url,
            'footer_note': footer_note,
        },
    )

