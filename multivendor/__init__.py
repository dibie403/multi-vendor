import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail, Message
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
# Application secret key
app.config['SECRET_KEY'] = os.getenv("Secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
paystack_secret_key = os.getenv('paystack_secret_key')
PK_test_key=os.getenv("paystack_pk_test")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("db_user1")  # Email username from env
app.config['MAIL_PASSWORD'] = os.environ.get("db_password")  # Email password from env
mail = Mail(app)

from multivendor import routes
from multivendor import models
