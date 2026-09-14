"""Only digests of bearer tokens are persisted; order outbox has no tokens."""
from app.extensions import db
from app.models.product import utcnow


class AccountEmailToken(db.Model):
    __tablename__ = 'account_email_tokens'
    id = db.Column(db.Integer, primary_key=True)
    digest = db.Column(db.String(64), unique=True, nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('customer_accounts.id'), nullable=False, index=True)
    purpose = db.Column(db.String(24), nullable=False)
    credential_digest = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    __table_args__ = (db.CheckConstraint("purpose IN ('verify_email','reset_password')"),)


class EmailRateLimit(db.Model):
    __tablename__ = 'email_rate_limits'
    key = db.Column(db.String(64), primary_key=True)
    hits = db.Column(db.Integer, nullable=False)
    window_start = db.Column(db.DateTime, nullable=False)


class OrderEmailOutbox(db.Model):
    __tablename__ = 'order_email_outbox'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('customer_requests.id'), nullable=False)
    recipient = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    sent_at = db.Column(db.DateTime)
    claimed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
