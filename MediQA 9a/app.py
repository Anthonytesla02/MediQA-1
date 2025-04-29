import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import DATABASE_URL, SESSION_SECRET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = SESSION_SECRET
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
# Handle potential "postgres://" to "postgresql://" conversion for Heroku-style DATABASE_URLs
database_url = DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # Redirect to index page when login required
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "error"  # For styling the flash message

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import routes after db is initialized
import models  # noqa: F401
import routes  # noqa: F401

# We'll move document processing initialization to a separate function that can be called
# from main.py to avoid blocking the app startup
def initialize_document_and_rag():
    with app.app_context():
        try:
            from document_processor import initialize_document_processor
            from rag_engine import initialize_rag_engine
            
            doc_init_success = initialize_document_processor()
            if doc_init_success:
                rag_init_success = initialize_rag_engine()
                if rag_init_success:
                    logger.info("Document processor and RAG engine initialized successfully")
                    return True
                else:
                    logger.warning("RAG engine initialization failed, some features may be limited")
            else:
                logger.warning("Document processor initialization failed, proceeding with limited functionality")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.info("Application will continue with limited functionality")
        
        return False
