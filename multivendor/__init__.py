import os
import logging
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask_caching import Cache 

# Load environment variables
load_dotenv()

# Setup logging (production-safe)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("Secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
paystack_secret_key = os.getenv('paystack_secret_key')
PK_test_key=os.getenv("paystack_pk_test")

# Database URI
#app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI2')
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB pool tuning to stay within 20 connection limit
#app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    #"pool_size": 5,         # Keep only 5 persistent connections
    #"max_overflow": 3,      # Allow 3 temporary spikes (total max = 8)
    #"pool_timeout": 10,     # Fail fast if pool is exhausted
    #"pool_recycle": 900,    # Recycle every 15 minutes to avoid stale
    #"pool_pre_ping": True   # Validate connections before using
#}

# SQLAlchemy setup
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Auth and encryption
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("db_user1")
app.config['MAIL_PASSWORD'] = os.getenv("db_password")
mail = Mail(app)
# Configure cache (You can use SimpleCache for local in-memory caching)
app.config['CACHE_TYPE'] = 'simple'  # Simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache timeout in seconds (5 minutes)
cache = Cache(app)

# Import routes and models
from multivendor import routes, models


# Log DB connection lifecycle events (for debugging only)
@event.listens_for(Engine, "connect")
def connect_event(dbapi_connection, connection_record):
    logger.debug("🔗 DBAPI connection opened")

@event.listens_for(Engine, "checkout")
def checkout_event(dbapi_connection, connection_record, connection_proxy):
    logger.debug("✅ Connection checked out")

@event.listens_for(Engine, "checkin")
def checkin_event(dbapi_connection, connection_record):
    logger.debug("↩️ Connection returned to pool")

# Automatically remove DB session after each request to avoid leaks
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
