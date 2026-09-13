"""Commercial records. Decimal values are stored as TEXT to avoid SQLite REAL conversion."""
from decimal import Decimal
import secrets
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, Text
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from .product import utcnow


class ExactDecimal(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, Decimal) or not value.is_finite():
            raise ValueError('Se requiere Decimal finito.')
        return format(value, 'f')

    def process_result_value(self, value, dialect):
        return Decimal(value) if value is not None else None


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (db.CheckConstraint("role IN ('admin','vendedor')"),)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(180), unique=True)
    password_hash = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='vendedor')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    session_token = db.Column(db.String(64), default=lambda: secrets.token_hex(24), unique=True, nullable=False)

    def get_id(self):
        return self.session_token

    def set_password(self, password):
        if not isinstance(password, str) or not 12 <= len(password) <= 200:
            raise ValueError('La contraseña debe tener entre 12 y 200 caracteres.')
        self.password_hash = generate_password_hash(password, method='scrypt')
        self.session_token = secrets.token_hex(24)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    identification_type = db.Column(db.String(30))
    identification = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(180), nullable=False, index=True)
    email = db.Column(db.String(180))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class BusinessSettings(db.Model):
    __tablename__ = 'business_settings'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(180), nullable=False, default='Yoli Figuras de Fomix')
    email = db.Column(db.String(180), default='figurasdefomixyoli@gmail.com')
    phone_1 = db.Column(db.String(50), default='0969080116')
    phone_2 = db.Column(db.String(50), default='0986791895')
    city = db.Column(db.String(100), default='Matriz San Gabriel')
    branch = db.Column(db.String(100), default='Sucursal Tulcán')
    currency = db.Column(db.String(8))
    invoice_prefix = db.Column(db.String(15), default='FAC')
    quote_prefix = db.Column(db.String(15), default='COT')
    units = db.Column(db.JSON, default=lambda: ['unidad','hoja','metro','ml','gramo','paquete'])
    payment_methods = db.Column(db.JSON, default=lambda: ['efectivo','transferencia','otro'])


class TaxSetting(db.Model):
    __tablename__ = 'tax_settings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Impuesto configurado')
    percentage = db.Column(ExactDecimal)  # NULL means not configured, never an assumed tax rate.


class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    unit = db.Column(db.String(40), nullable=False)
    unit_cost = db.Column(ExactDecimal, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class ProductCostRecipe(db.Model):
    __tablename__ = 'product_cost_recipes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    name = db.Column(db.String(140), nullable=False)
    requested_size = db.Column(db.String(120))
    personalization = db.Column(db.String(500))
    labor_hours = db.Column(ExactDecimal, nullable=False)
    hourly_cost = db.Column(ExactDecimal, nullable=False)
    indirect_costs = db.Column(db.JSON, nullable=False, default=list)
    profit_method = db.Column(db.String(20), nullable=False)
    profit_percentage = db.Column(ExactDecimal, nullable=False)
    surcharge = db.Column(ExactDecimal, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    product = db.relationship('Product')
    materials = db.relationship('ProductCostMaterial', cascade='all, delete-orphan', order_by='ProductCostMaterial.id')


class ProductCostMaterial(db.Model):
    __tablename__ = 'product_cost_materials'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('product_cost_recipes.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'))
    name = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.String(40), nullable=False)
    quantity = db.Column(ExactDecimal, nullable=False)
    unit_cost = db.Column(ExactDecimal, nullable=False)


class DocumentFields:
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subtotal = db.Column(ExactDecimal, nullable=False)
    discount = db.Column(ExactDecimal, nullable=False)
    tax = db.Column(ExactDecimal)  # Unconfigured tax is allowed only on draft quotes.
    tax_percentage = db.Column(ExactDecimal)
    total = db.Column(ExactDecimal, nullable=False)
    currency = db.Column(db.String(8))
    customer_snapshot = db.Column(db.JSON, nullable=False)
    business_snapshot = db.Column(db.JSON, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class Quote(DocumentFields, db.Model):
    __tablename__ = 'quotes'
    __table_args__ = (db.CheckConstraint("status IN ('draft','sent','accepted','rejected','expired','converted')"),)
    quote_number = db.Column(db.String(40), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    expires_at = db.Column(db.DateTime)
    customer = db.relationship('Customer')
    items = db.relationship('QuoteItem', cascade='all, delete-orphan', order_by='QuoteItem.id')


class QuoteItem(db.Model):
    __tablename__ = 'quote_items'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_code_snapshot = db.Column(db.String(60), nullable=False)
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    quantity = db.Column(ExactDecimal, nullable=False)
    requested_size = db.Column(db.String(120))
    personalization = db.Column(db.String(500))
    unit_cost = db.Column(ExactDecimal, nullable=False)
    unit_price = db.Column(ExactDecimal, nullable=False)
    surcharge = db.Column(ExactDecimal, nullable=False)
    discount = db.Column(ExactDecimal, nullable=False)
    subtotal = db.Column(ExactDecimal, nullable=False)
    cost_snapshot = db.Column(db.JSON, nullable=False)


class Invoice(DocumentFields, db.Model):
    __tablename__ = 'invoices'
    __table_args__ = (db.CheckConstraint("status IN ('draft','issued','paid','cancelled')"),)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), unique=True)
    status = db.Column(db.String(20), nullable=False, default='draft')
    payment_method = db.Column(db.String(80))
    paid_at = db.Column(db.DateTime)
    customer = db.relationship('Customer')
    quote = db.relationship('Quote')
    items = db.relationship('InvoiceItem', cascade='all, delete-orphan', order_by='InvoiceItem.id')


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_code_snapshot = db.Column(db.String(60), nullable=False)
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    quantity = db.Column(ExactDecimal, nullable=False)
    requested_size = db.Column(db.String(120))
    personalization = db.Column(db.String(500))
    unit_price = db.Column(ExactDecimal, nullable=False)
    surcharge = db.Column(ExactDecimal, nullable=False)
    discount = db.Column(ExactDecimal, nullable=False)
    subtotal = db.Column(ExactDecimal, nullable=False)


class NumberSequence(db.Model):
    __tablename__ = 'number_sequences'
    kind = db.Column(db.String(20), primary_key=True)
    value = db.Column(db.Integer, nullable=False)


class AuditEvent(db.Model):
    __tablename__ = 'audit_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entity = db.Column(db.String(40), nullable=False)
    entity_id = db.Column(db.Integer)
    action = db.Column(db.String(60), nullable=False)
    detail = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    user = db.relationship('User')


class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    key = db.Column(db.String(64), primary_key=True)
    failures = db.Column(db.Integer, nullable=False, default=0)
    window_start = db.Column(db.DateTime, nullable=False, default=utcnow)


class SchemaVersion(db.Model):
    __tablename__ = 'schema_versions'
    version = db.Column(db.Integer, primary_key=True)
    applied_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class CostEstimate(db.Model):
    __tablename__ = 'cost_estimates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    requested_size = db.Column(db.String(120))
    personalization = db.Column(db.String(500))
    input_data = db.Column(db.JSON, nullable=False)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    product = db.relationship('Product')
