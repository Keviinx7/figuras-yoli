"""Customer-facing accounts and persisted requests for the public store.

Nothing economic is stored here: no prices, costs or margins. Requests are
the starting point that staff later turns into an internal quote/invoice.
"""
import secrets
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from .product import utcnow

REQUEST_STATUSES = ('pending', 'processing', 'completed', 'rejected')
REQUEST_STATUS_LABELS = {'pending': 'Por atender', 'processing': 'En elaboración',
                         'completed': 'Completada', 'rejected': 'Rechazada'}


class CustomerAccount(db.Model):
    __tablename__ = 'customer_accounts'
    __table_args__ = (CheckConstraint("length(password_hash) > 0"),)
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'),
                            unique=True, nullable=False, index=True)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(300), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    session_token = db.Column(db.String(64), default=lambda: secrets.token_hex(24),
                              unique=True, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    customer = db.relationship('Customer')

    def set_password(self, password):
        if not isinstance(password, str) or not 12 <= len(password) <= 200:
            raise ValueError('La contraseña debe tener entre 12 y 200 caracteres.')
        self.password_hash = generate_password_hash(password, method='scrypt')
        # Rotating the token invalidates every existing session and recovery link.
        self.session_token = secrets.token_hex(24)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CustomerRequest(db.Model):
    __tablename__ = 'customer_requests'
    __table_args__ = (CheckConstraint("status IN ('pending','processing','completed','rejected')"),)
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('customer_accounts.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    delivery = db.Column(db.String(40), nullable=False)
    delivery_label = db.Column(db.String(120))
    customer_snapshot = db.Column(db.JSON, nullable=False)
    notes = db.Column(db.String(3000))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    customer = db.relationship('Customer')
    account = db.relationship('CustomerAccount')
    items = db.relationship('CustomerRequestItem', cascade='all, delete-orphan',
                            order_by='CustomerRequestItem.id')


class CustomerRequestItem(db.Model):
    __tablename__ = 'customer_request_items'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('customer_requests.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_code_snapshot = db.Column(db.String(60), nullable=False)
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    requested_size = db.Column(db.String(120))
    personalization = db.Column(db.String(500))
    request = db.relationship('CustomerRequest', overlaps='items')
    product = db.relationship('Product')