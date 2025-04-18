from datetime import datetime
from multivendor import db,login_manager,app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    image_file = db.Column(db.String(255), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    shop_image_file = db.Column(db.String(255), nullable=True, default='default2.jpg')
    is_admin = db.Column(db.Boolean, nullable=False,default=False)
    shop_name= db.Column(db.String(20), nullable=True, unique=True)
    shop_motto= db.Column(db.Text, nullable=True,unique=True)
    shop_about= db.Column(db.Text, nullable=True,unique=False)
    shop_theme = db.Column(db.Text, nullable=True, default=None)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.Boolean, nullable=False,default=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    slug1=db.Column(db.String(100), unique=True, nullable=True)
    
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_end = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_super = db.Column(db.Boolean, default=False,nullable=True)
    is_verified = db.Column(db.Boolean, default=False,nullable=True)

    subscription = db.relationship('Subscription', backref='user', uselist=False)
    products = db.relationship('Product', backref='seller', lazy=True)
    personal_info = db.relationship('PersonalInfo', backref='user', uselist=False, cascade="all, delete-orphan")

    
    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            # Pass the expiration time in seconds (e.g., 1800 for 30 minutes)
            data = s.loads(token, max_age=1800)
            user_id = data['user_id']
        except SignatureExpired:
            # Handle expired token
            return None
        except BadSignature:
            # Handle invalid token
            return None

        # Assuming User.query.get retrieves a user by their ID
        return User.query.get(user_id)
    
    
    
    def __repr__(self):
        return f"User('{self.slug}', '{self.is_verified}','{self.is_subscribed}', '{self.subscription_end}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount =db.Column(db.Float, nullable=False)
    category =db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    shelf = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)


    
    

    def __repr__(self):
        return f"Product('{self.name}', '{self.slug}')"


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    product_id=db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    product = db.relationship('Product', backref=db.backref('images', lazy=True))


class Love(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Define relationships
    user = db.relationship('User', backref=db.backref('loves', lazy=True))
    product = db.relationship('Product', backref=db.backref('loves', lazy=True))

    def __repr__(self):
        return f"Like('{self.user_id}', '{self.product_id}')"

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Buyer
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Seller
    product_id = db.Column(db.Integer, db.ForeignKey('product.id',ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False,default=1)
    amount =db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    product = db.relationship('Product', backref='cart_items')



class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Buyer
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Seller
    status = db.Column(db.String(50), nullable=False, default="Pending")  # Pending, Completed, Canceled
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    track_code= db.Column(db.Integer, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='received_orders')
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Order('{self.id}', Buyer: '{self.user_id}', Seller: '{self.seller_id}', code: '{self.track_code}', proce: '{self.total_amount}')"


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f"OrderItem('{self.id}', Order: '{self.order_id}', Product: '{self.product_id}', Qty: '{self.quantity}')"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    initiator= db.Column(db.Integer, nullable=False,default=None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    


    # Define relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
   

    def __repr__(self):
         return f"Notification('{self.content}','{self.user_id}')"

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True,nullable=False)
    plan = db.Column(db.String(50))
    amount = db.Column(db.Integer)
    reference = db.Column(db.String(100))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)

    def __repr__(self):
        return f"Subscription('{self.user_id}', '{self.end_date}','{self.start_date}','{self.amount}','{self.reference}','{self.plan}')"


class PersonalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    day_of_birth = db.Column(db.Integer, nullable=False)
    month_of_birth = db.Column(db.Integer, nullable=False)
    year_of_birth = db.Column(db.Integer, nullable=False)
