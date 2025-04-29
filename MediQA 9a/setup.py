"""
MediQA Auto-Setup Script
This script initializes the necessary environment for the MediQA application.
It installs required packages, sets up the PostgreSQL database, and loads initial data.
"""
import subprocess
import sys
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Required packages
REQUIRED_PACKAGES = [
    'flask',
    'flask-login',
    'flask-sqlalchemy',
    'flask-wtf',
    'gunicorn',
    'mistralai',
    'numpy',
    'openai',
    'anthropic',
    'psycopg2-binary',
    'python-docx',
    'requests',
    'sqlalchemy',
    'werkzeug',
    'email-validator',
    'docx'
]

def install_packages():
    """Install required Python packages."""
    logger.info("Installing required packages...")
    
    try:
        for package in REQUIRED_PACKAGES:
            logger.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        logger.info("All packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing packages: {e}")
        return False

def ensure_postgresql():
    """Ensure PostgreSQL database is available and configured."""
    logger.info("Checking PostgreSQL configuration...")
    
    # Check if DATABASE_URL environment variable is set
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("DATABASE_URL not found in environment variables")
        
        # Check if we're in Replit environment
        if os.path.exists("/.replit"):
            logger.info("Replit environment detected, creating PostgreSQL database")
            try:
                # Try to create a PostgreSQL database using Replit's service
                result = subprocess.run(
                    ["curl", "-X", "POST", "https://replit.com/api/v1/resources/postgresql/create"],
                    capture_output=True, text=True, check=True
                )
                logger.info(f"PostgreSQL database creation response: {result.stdout}")
                
                # Wait for database to initialize
                logger.info("Waiting for database to initialize...")
                time.sleep(5)
                
                # Check if DATABASE_URL is now available
                db_url = os.environ.get('DATABASE_URL')
                if not db_url:
                    logger.error("Failed to create PostgreSQL database through Replit API")
                    return False
            except subprocess.CalledProcessError as e:
                logger.error(f"Error creating PostgreSQL database: {e}")
                return False
        else:
            logger.error("Not running in Replit and DATABASE_URL not set. Please set DATABASE_URL manually.")
            return False
    
    logger.info("PostgreSQL database is available")
    return True

def initialize_database():
    """Initialize the PostgreSQL database with tables and initial data."""
    logger.info("Initializing database...")
    
    try:
        # Import the app to create the database tables
        from app import app, db
        with app.app_context():
            # Drop all tables if they exist and create them fresh
            logger.info("Dropping existing tables if any...")
            db.drop_all()
            
            logger.info("Creating fresh database tables...")
            db.create_all()
            
            # Initialize achievements
            from gamification import initialize_achievements
            initialize_achievements()
            
            # Create a demo admin user
            from models import User
            from werkzeug.security import generate_password_hash
            
            # Add demo user
            demo_user = User(
                username="demo",
                email="demo@example.com",
                password_hash=generate_password_hash("demopassword"),
                points=100,
                streak=5
            )
            db.session.add(demo_user)
            db.session.commit()
            
            logger.info("Database initialized successfully with demo user: demo@example.com / demopassword")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def initialize_document_processor():
    """Initialize the document processor and RAG engine."""
    logger.info("Initializing document processor and RAG engine...")
    
    try:
        from document_processor import initialize_document_processor
        from rag_engine import initialize_rag_engine
        
        initialize_document_processor()
        initialize_rag_engine()
        
        logger.info("Document processor and RAG engine initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing document processor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run auto-setup process."""
    logger.info("Starting MediQA auto-setup...")
    
    # Install packages
    if not install_packages():
        logger.error("Failed to install packages. Setup aborted.")
        return False
    
    # Ensure PostgreSQL database is available
    if not ensure_postgresql():
        logger.error("Failed to ensure PostgreSQL database. Setup aborted.")
        return False
    
    # Initialize database
    if not initialize_database():
        logger.error("Failed to initialize database. Setup aborted.")
        return False
    
    # Initialize document processor
    if not initialize_document_processor():
        logger.warning("Failed to initialize document processor. Continuing but app may not work properly.")
    
    logger.info("======================================================")
    logger.info("MediQA auto-setup completed successfully!")
    logger.info("Demo user created: demo@example.com / demopassword")
    logger.info("Mistral API key is hardcoded in config.py")
    logger.info("To start the application, run: gunicorn --bind 0.0.0.0:5000 main:app")
    logger.info("======================================================")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)