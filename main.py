
import os
import logging
import threading
from pathlib import Path
from config import DATABASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Auto-initialization flag file path
INIT_FLAG_FILE = ".app_initialized"

def background_initialization():
    """Initialize document processor and RAG engine in background thread"""
    from app import initialize_document_and_rag
    
    logger.info("Starting background initialization of document processor and RAG engine...")
    success = initialize_document_and_rag()
    
    if success:
        logger.info("Background initialization completed successfully")
    else:
        logger.warning("Background initialization completed with issues")

def auto_initialize():
    """Performs initial database setup"""
    logger.info("Starting database initialization...")
    
    # Check if we have a PostgreSQL database
    if not DATABASE_URL:
        logger.error("PostgreSQL database not found. Please ensure DATABASE_URL is configured.")
        return False
    else:
        logger.info("PostgreSQL database found")
    
    # Initialize database tables and data
    try:
        from app import app, db
        with app.app_context():
            # Import models to ensure they're registered with SQLAlchemy
            import models
            
            # Create tables if they don't exist
            db.create_all()
            
            # Initialize achievements
            from gamification import initialize_achievements
            initialize_achievements()
            
            logger.info("Database tables created successfully")
            
            # Create flag file to indicate initialization is complete
            Path(INIT_FLAG_FILE).touch()
            logger.info("Database initialization complete")
            return True
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False

# Import app
from app import app

if __name__ == "__main__":
    # Only run initialization if the flag file doesn't exist
    if not Path(INIT_FLAG_FILE).exists():
        success = auto_initialize()
        if not success:
            logger.error("Initialization failed. Check the logs for details.")
    
    # Start background initialization in a separate thread
    # This allows the app to start while document processing continues
    threading.Thread(target=background_initialization, daemon=True).start()
    
    # Start the application
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    logger.info("Starting MediQA application on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
