import os

# Hardcoded API keys and secrets
MISTRAL_API_KEY = "j4h3leTe769ILXBLzwsMkrKEzWqZjOTj"
SESSION_SECRET = "Kyb7NC2kQ4Qw9FoFd2TE0goQcXowJBgZf7ECFSjB6mVZuXBdiL2TpU7OgMG4BL8RR3sl0+GBraoHNwrS6kZhLw=="

# Hardcoded database configuration
DATABASE_URL = "postgresql://neondb_owner:npg_5qCGUsH4Jnkm@ep-sparkling-mouse-a5arych6.us-east-2.aws.neon.tech/neondb?sslmode=require"
PGPORT = "5432"
PGPASSWORD = "npg_5qCGUsH4Jnkm"
PGUSER = "neondb_owner"
PGDATABASE = "neondb"
PGHOST = "ep-sparkling-mouse-a5arych6.us-east-2.aws.neon.tech"

# Document configuration
DOCUMENT_PATH = "attached_assets/pharmacy_guide.docx"

# RAG configuration
VECTOR_DB_PATH = "vector_db"
CHUNK_SIZE = 1500  # Increased for faster processing
CHUNK_OVERLAP = 100  # Decreased for faster processing

# Gamification settings
DAILY_STREAK_POINTS = 10
CASE_COMPLETION_POINTS = {
    "easy": 10,
    "medium": 20,
    "hard": 30
}
CHALLENGE_COMPLETION_POINTS = 15
CORRECT_DIAGNOSIS_BONUS = 25
FLASHCARD_REVIEW_POINTS = 5

# Spaced repetition settings
MIN_INTERVAL = 1
MAX_INTERVAL = 365
EASY_BONUS = 1.3
INITIAL_EASE = 2.5
