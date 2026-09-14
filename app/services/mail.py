"""Reusable transport. Never log addresses, message bodies or SMTP exceptions."""
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import urlsplit
import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import update, or_
from app.extensions import db
from app.models.customer_email import OrderEmailOutbox
from app.models.customer_account import REQUEST_STATUS_LABELS
from app.services.customer_portal import now
from datetime import timedelta


def configure_mail(app):
    cfg = app.config
    backend = cfg.get('MAIL_BACKEND', 'smtp')
    strict = cfg.get('ENVIRONMENT') in ('production', 'staging')
    enabled = cfg.get('MAIL_ENABLED', False)
    features = any(cfg.get(k) for k in ('EMAIL_VERIFICATION_ENABLED', 'ACCOUNT_RECOVERY_ENABLED',
                                       'ORDER_EMAIL_NOTIFICATIONS_ENABLED'))
    try:
        base = urlsplit(cfg.get('PUBLIC_BASE_URL', ''))
        base.port  # Validate malformed/out-of-range ports without exposing the URL.
    except ValueError:
        raise RuntimeError('PUBLIC_BASE_URL inválida.') from None
    valid_base = (base.scheme in ('http', 'https') and base.hostname and not base.username
                  and not base.password and not base.query and not base.fragment
                  and base.path in ('', '/') and not re.search(r'[\s\\]', cfg.get('PUBLIC_BASE_URL', '')))
    invalid = backend not in ('smtp', 'fake', 'disabled')
    invalid |= bool(cfg.get('SMTP_USE_TLS') and cfg.get('SMTP_USE_SSL'))
    if enabled and backend == 'smtp':
        address = cfg.get('MAIL_FROM_ADDRESS', '')
        invalid |= not bool(cfg.get('SMTP_HOST') and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', address))
        invalid |= not isinstance(cfg.get('SMTP_PORT'), int) or not 1 <= cfg.get('SMTP_PORT', 0) <= 65535
        invalid |= bool(cfg.get('SMTP_USERNAME')) != bool(cfg.get('SMTP_PASSWORD'))
        invalid |= any('\n' in str(cfg.get(k, '')) or '\r' in str(cfg.get(k, ''))
                       for k in ('MAIL_FROM_NAME', 'MAIL_FROM_ADDRESS', 'SMTP_HOST'))
        if strict:
            invalid |= not (cfg.get('SMTP_USE_TLS') or cfg.get('SMTP_USE_SSL'))
    if features and enabled and backend != 'disabled':
        invalid |= not bool(valid_base)
    if strict:
        invalid |= backend == 'fake'
        invalid |= features and (not enabled or backend == 'disabled')
        invalid |= (features or enabled) and (not valid_base or base.scheme != 'https')
    for key in ('EMAIL_VERIFICATION_LIFETIME_HOURS', 'ACCOUNT_RECOVERY_LIFETIME_HOURS'):
        invalid |= not isinstance(cfg.get(key), int) or not 1 <= cfg.get(key, 0) <= 168
    if invalid:
        raise RuntimeError('Configuración de correo inválida; revise transporte, TLS y PUBLIC_BASE_URL.')
    app.extensions['mail_outbox'] = []  # Exists only in process memory; never an HTTP endpoint.
    app.cli.add_command(retry_order_mail)


def available():
    return bool(current_app.config.get('MAIL_ENABLED') and
                current_app.config.get('MAIL_BACKEND') in ('smtp', 'fake'))


def public_link(path):
    # Paths are application constants/url_for(_external=False), never browser Host.
    return current_app.config['PUBLIC_BASE_URL'].rstrip('/') + path


def send_mail(recipient, subject, body):
    if not available():
        return 'disabled'
    cfg = current_app.config
    try:
        message = EmailMessage()
        message['From'] = formataddr((cfg.get('MAIL_FROM_NAME', 'Yoli'), cfg.get('MAIL_FROM_ADDRESS', 'yoli@example.invalid')))
        message['To'] = recipient
        message['Subject'] = subject
        message.set_content(body)
        if cfg['MAIL_BACKEND'] == 'fake':
            current_app.extensions['mail_outbox'].append(message)
            return 'sent'
        transport = smtplib.SMTP_SSL if cfg.get('SMTP_USE_SSL') else smtplib.SMTP
        kwargs = {'timeout': 10}
        if cfg.get('SMTP_USE_SSL'):
            kwargs['context'] = ssl.create_default_context()
        with transport(cfg['SMTP_HOST'], cfg['SMTP_PORT'], **kwargs) as smtp:
            if cfg.get('SMTP_USE_TLS'):
                smtp.starttls(context=ssl.create_default_context())
            if cfg.get('SMTP_USERNAME'):
                smtp.login(cfg['SMTP_USERNAME'], cfg['SMTP_PASSWORD'])
            smtp.send_message(message)
        return 'sent'
    except Exception:
        current_app.logger.warning('No se pudo entregar un correo; revise el transporte configurado.')
        return 'failed'


def queue_order_email(req):
    """Called inside the business transaction: durable, allow-listed public fields."""
    if not current_app.config.get('ORDER_EMAIL_NOTIFICATIONS_ENABLED') or not available():
        return None
    if not req.account.is_active:
        return None
    body = (f'Solicitud #{req.id:04d}\nEstado: {REQUEST_STATUS_LABELS[req.status]}\n\n'
            + '\n'.join(f'{item.product_code_snapshot} · {item.product_name_snapshot} · Cantidad: {item.quantity}'
                        for item in req.items)
            + '\n\nLos precios se confirman según tamaño y personalización.\n'
            + public_link(f'/cuenta/pedido/{req.id}'))
    row = OrderEmailOutbox(request_id=req.id, recipient=req.account.email,
                           subject=f'Yoli · Solicitud #{req.id:04d}', body=body)
    db.session.add(row)
    return row


def deliver_order_mail(row_id):
    """Separate transaction, after business commit. Lease prevents concurrent retries."""
    if not row_id or not available() or not current_app.config.get('ORDER_EMAIL_NOTIFICATIONS_ENABLED'):
        return
    try:
        claimed = db.session.execute(update(OrderEmailOutbox).where(
            OrderEmailOutbox.id == row_id, OrderEmailOutbox.sent_at.is_(None),
            or_(OrderEmailOutbox.claimed_at.is_(None),
                OrderEmailOutbox.claimed_at < now() - timedelta(minutes=5))
        ).values(claimed_at=now(), attempts=OrderEmailOutbox.attempts + 1))
        db.session.commit()
        if not claimed.rowcount:
            return
        row = db.session.get(OrderEmailOutbox, row_id)
        result = send_mail(row.recipient, row.subject, row.body)
        if result == 'sent':
            row.sent_at = now()
        row.claimed_at = None
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.warning('Notificación pendiente; el pedido permanece guardado.')


@click.command('retry-order-mail')
@click.option('--limit', default=100, type=click.IntRange(1, 1000))
@with_appcontext
def retry_order_mail(limit):
    """Retry pending order notifications; never prints recipients or content."""
    ids = [r.id for r in OrderEmailOutbox.query.filter_by(sent_at=None).order_by(OrderEmailOutbox.id).limit(limit)]
    for row_id in ids:
        deliver_order_mail(row_id)
    click.echo('Revisión de notificaciones terminada.')
