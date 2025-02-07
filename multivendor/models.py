from datetime import datetime
from multivendor import db,app


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    image_file = db.Column(db.String(255), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False,default=False)
    shop_name= db.Column(db.String(20), nullable=True, unique=True)
    shop_motto= db.Column(db.Text, nullable=True,unique=True)
    phone_number =db.Column(db.Integer, nullable=False,)
    status = db.Column(db.Boolean, nullable=False,default=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='seller', lazy=True)
    
    
    
    def __repr__(self):
        return f"User('{self.username}', '{self.status}','{self.is_admin}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount =db.Column(db.Integer, nullable=False)
    category =db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    
    

    def __repr__(self):
        return f"Product('{self.title}', '{self.slug}')"


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    product_id=db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    product = db.relationship('Product', backref=db.backref('images', lazy=True))


