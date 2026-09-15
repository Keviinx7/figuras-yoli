"""Purpose-bound, revocable random tokens, atomic consumption and DB throttling."""
import hashlib
import secrets
from datetime import timedelta
from flask import abort, request, current_app, url_for
from sqlalchemy import update, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from app.extensions import db
from app.models.customer_email import AccountEmailToken, EmailRateLimit
from app.models.customer_account import CustomerAccount
from app.services.customer_portal import now
from app.services.mail import available, public_link, send_mail


def feature_enabled(purpose):
    return bool(current_app.config.get('EMAIL_VERIFICATION_ENABLED' if purpose == 'verify_email'
                                       else 'ACCOUNT_RECOVERY_ENABLED'))


def throttle(scope, identity=None, limit=5, seconds=900):
    """Atomic DB counters shared by workers; count all attempts, even unknown emails."""
    if identity is None:
        identity = request.remote_addr or 'local'
    insert = sqlite_insert if db.engine.dialect.name == 'sqlite' else postgres_insert
    for kind, value, maximum in [('ip', request.remote_addr or 'local', limit * 4),
                                  ('identity', identity, limit)]:
        key = hashlib.sha256(f'{scope}:{kind}:{value}'.encode()).hexdigest()
        stamp = now()
        db.session.execute(insert(EmailRateLimit).values(key=key, hits=0, window_start=stamp)
                           .on_conflict_do_nothing(index_elements=['key']))
        db.session.execute(update(EmailRateLimit).where(
            EmailRateLimit.key == key, EmailRateLimit.window_start <= stamp - timedelta(seconds=seconds)
        ).values(hits=0, window_start=stamp))
        result = db.session.execute(update(EmailRateLimit).where(
            EmailRateLimit.key == key, EmailRateLimit.hits < maximum
        ).values(hits=EmailRateLimit.hits + 1))
        db.session.commit()
        if not result.rowcount:
            abort(429)


def revoke_tokens(account, purpose=None):
    query = update(AccountEmailToken).where(AccountEmailToken.account_id == account.id,
                                           AccountEmailToken.used_at.is_(None))
    if purpose:
        query = query.where(AccountEmailToken.purpose == purpose)
    db.session.execute(query.values(used_at=now()))


def issue_token(account, purpose):
    if purpose not in ('verify_email', 'reset_password'):
        raise ValueError('Propósito inválido.')
    # Lock the account before revoking earlier tokens, also on PostgreSQL.
    db.session.execute(update(CustomerAccount).where(CustomerAccount.id == account.id)
                       .values(id=CustomerAccount.id))
    db.session.refresh(account)
    revoke_tokens(account, purpose)
    token = secrets.token_urlsafe(32)
    hours = current_app.config.get('EMAIL_VERIFICATION_LIFETIME_HOURS', 24) if purpose == 'verify_email' else current_app.config.get('ACCOUNT_RECOVERY_LIFETIME_HOURS', 1)
    row = AccountEmailToken(account_id=account.id, purpose=purpose, email=account.email,
                            credential_digest=hashlib.sha256(account.password_hash.encode()).hexdigest(),
                            digest=hashlib.sha256(token.encode()).hexdigest(),
                            expires_at=now() + timedelta(hours=hours))
    db.session.add(row)
    db.session.commit()
    return token


def find_token(token, purpose):
    if not isinstance(token, str) or len(token) != 43:
        return None
    row = AccountEmailToken.query.filter_by(digest=hashlib.sha256(token.encode()).hexdigest(),
                                            purpose=purpose, used_at=None).first()
    if not row or row.expires_at <= now():
        return None
    account = db.session.get(CustomerAccount, row.account_id)
    if not account or not account.is_active or account.email != row.email or hashlib.sha256(account.password_hash.encode()).hexdigest() != row.credential_digest:
        return None
    return row


def consume_token(token, purpose):
    """Caller commits consumption together with account mutation; GET never consumes."""
    row = find_token(token, purpose)
    if not row:
        return None
    db.session.execute(update(CustomerAccount).where(CustomerAccount.id == row.account_id)
                       .values(id=CustomerAccount.id))
    account = db.session.execute(select(CustomerAccount).where(
        CustomerAccount.id == row.account_id).execution_options(populate_existing=True)).scalar_one()
    if not account.is_active or account.email != row.email or hashlib.sha256(account.password_hash.encode()).hexdigest() != row.credential_digest:
        return None
    result = db.session.execute(update(AccountEmailToken).where(
        AccountEmailToken.id == row.id, AccountEmailToken.used_at.is_(None),
        AccountEmailToken.expires_at > now()).values(used_at=now()))
    return account if result.rowcount else None


def send_account_email(account, purpose):
    if not feature_enabled(purpose) or not available() or not account.is_active:
        current_app.logger.info('account mail skipped: feature or transport disabled, or account inactive')
        return 'disabled'
    token = issue_token(account, purpose)
    current_app.logger.info('account mail purpose=%s token created; delivery started', purpose)
    endpoint = 'portal.verify' if purpose == 'verify_email' else 'portal.reset'
    subject = 'Verifica tu correo' if purpose == 'verify_email' else 'Restablece tu contraseña'
    result = send_mail(account.email, 'Yoli · ' + subject,
                       subject + '\n\n' + public_link(url_for(endpoint, token=token, _external=False))
                       + '\n\nEste enlace es temporal y de un solo uso. Si no lo solicitaste, ignóralo.')
    current_app.logger.info('account mail purpose=%s result=%s', purpose, result)
    if result != 'sent':
        row = find_token(token, purpose)
        if row:
            row.used_at = now()
            db.session.commit()
    return result
