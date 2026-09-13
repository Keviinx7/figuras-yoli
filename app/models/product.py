from datetime import datetime, timezone
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (db.CheckConstraint("substr(code, -3) != '000'", name='no_placeholder'),)
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(60), nullable=False, unique=True)
    name = db.Column(db.String(200))
    slug = db.Column(db.String(240), nullable=False, unique=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    size_notes = db.Column(db.Text)
    allows_customization = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    category = db.relationship('Category', back_populates='products')
    images = db.relationship('ProductImage', back_populates='product', cascade='all, delete-orphan', order_by='ProductImage.sort_order')

    @property
    def display_name(self):
        return self.name or self.code

    @property
    def image_path(self):
        return self.images[0].file_path if self.images else 'img/placeholder.svg'
