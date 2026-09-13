from app.extensions import db


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    file_path = db.Column(db.String(400), nullable=False)
    alt_text = db.Column(db.String(250))
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    product = db.relationship('Product', back_populates='images')
