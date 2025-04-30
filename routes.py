import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from app import app, db
from models import (
    User, ChatHistory, Case, CaseAttempt, Challenge, 
    ChallengeAttempt, Flashcard, FlashcardProgress, 
    Achievement, UserAchievement
)
from document_processor import search_document
from rag_engine import search_similar_chunks
from ai_service import (
    get_diagnosis_response, generate_case_simulation, 
    generate_daily_challenge, generate_multiple_daily_challenges,
    generate_flashcards, evaluate_diagnosis
)
from gamification import (
    update_user_streak, add_points, award_achievement,
    get_leaderboard, get_user_achievements, initialize_achievements
)
from config import (
    CASE_COMPLETION_POINTS, CHALLENGE_COMPLETION_POINTS,
    CORRECT_DIAGNOSIS_BONUS, FLASHCARD_REVIEW_POINTS
)
from auth import auth_bp

logger = logging.getLogger(__name__)

# Register the authentication blueprint
app.register_blueprint(auth_bp)

# Initialize achievements
with app.app_context():
    initialize_achievements()

# We'll use Flask-Login's built-in login_required decorator

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/chat')
@login_required
def chat():
    """Render the chat page."""
    return render_template('chat.html')

@app.route('/simulation')
# Temporarily removed login_required for testing
# @login_required
def simulation():
    """Render the simulation page."""
    return render_template('simulation.html')

@app.route('/flashcards')
@login_required
def flashcards():
    """Render the flashcards page."""
    return render_template('flashcards.html')

# Challenges route has been removed

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    """Render the leaderboard page."""
    return render_template('leaderboard.html')

# API Routes

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages."""
    try:
        data = request.json
        query = data.get('query', '')
        user_id = session.get('user_id')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Get AI response
        response = get_diagnosis_response(query)
        
        # Save chat history if user is logged in
        if user_id:
            # Update user streak
            update_user_streak(user_id)
            
            # Add chat to history
            chat_history = ChatHistory(
                user_id=user_id,
                messages=json.dumps([
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response}
                ])
            )
            db.session.add(chat_history)
            db.session.commit()
        
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route('/api/simulation/new', methods=['GET'])
# Temporarily removed login_required for testing
# @login_required
def api_new_simulation():
    """API endpoint to get a new simulation case."""
    try:
        # Generate a case from our list of topics using the knowledge base
        logger.info("Requesting new case simulation from knowledge base")
        
        # Get all available topics
        topics = [
            "Diarrhoea", "Rotavirus Disease and Diarrhoea", "Constipation", "Peptic Ulcer Disease",
            "Gastro-oesophageal Reflux Disease", "Haemorrhoids", "Vomiting", "Anaemia", "Measles",
            "Pertussis", "Common cold", "Pneumonia", "Headache", "Boils", "Impetigo", "Buruli ulcer",
            "Yaws", "Superficial Fungal Skin infections", "Pityriasis Versicolor", "Herpes Simplex Infections",
            "Herpes Zoster Infections", "Chicken pox", "Large Chronic Ulcers", "Pruritus", "Urticaria",
            "Reactive Erythema and Bullous Reaction", "Acne Vulgaris", "Eczema", "Intertrigo", "Diabetes Mellitus",
            "Diabetic Ketoacidosis", "Diabetes in Pregnancy", "Treatment-Induced Hypoglycemia", "Dyslipidaemia",
            "Goitre", "Hypothyroidism", "Hyperthyroidism", "Overweight and Obesity", "Dysmenorrhoea",
            "Abortion", "Abnormal Vaginal Bleeding", "Abnormal Vaginal Discharge", "Acute Lower Abdominal Pain",
            "Menopause", "Erectile Dysfunction", "Urinary Tract Infection", "Sexually Transmitted Infections in Adults",
            "Fever", "Tuberculosis", "Typhoid fever", "Malaria", "Uncomplicated Malaria", "Severe Malaria",
            "Malaria in Pregnancy", "Worm Infestation", "Xerophthalmia", "Foreign body in the eye",
            "Neonatal conjunctivitis", "Red eye", "Stridor", "Acute Epiglottitis", "Retropharyngeal Abscess",
            "Pharyngitis and Tonsillitis", "Acute Sinusitis", "Acute otitis Media", "Chronic Otitis Media",
            "Epistaxis", "Dental Caries", "Oral Candidiasis", "Acute Necrotizing Ulcerative Gingivitis",
            "Acute Bacterial Sialoadenitis", "Chronic Periodontal Infections", "Mouth Ulcers", "Odontogenic Infections",
            "Osteoarthritis", "Rheumatoid arthritis", "Juvenile Idiopathic Arthritis", "Back pain", "Gout",
            "Dislocations", "Open Fractures", "Cellulitis", "Burns", "Wounds", "Bites and Stings",
            "Shock", "Acute Allergic Reaction"
        ]
        
        # Randomly select a topic
        from random import choice
        selected_topic = choice(topics)
        logger.info(f"Selected topic for case simulation: {selected_topic}")
        
        # Use the RAG engine to get information about this topic from the knowledge base
        from rag_engine import generate_context_for_query
        topic_info = generate_context_for_query(selected_topic)
        
        # Create a presenting complaint based on the topic
        # For this simpler version, we'll use a more straightforward case template
        from ai_service import get_diagnosis_response
        case_info = get_diagnosis_response(f"What are the symptoms, diagnosis criteria, and treatment for {selected_topic}?")
        
        # Create a patient scenario
        from random import randint
        age = randint(18, 75)  # Random age between 18-75
        gender = choice(["male", "female"])
        
        # Generate a simple presenting complaint
        presenting_complaint = f"A {age}-year-old {gender} presents with symptoms consistent with {selected_topic}."
        
        # Create a case structure with the correct fields
        case_data = {
            'presenting_complaint': presenting_complaint,
            'diagnosis': selected_topic,
            'treatment': "",  # Will be extracted from the topic_info
            'differential_reasoning': ""  # Will be extracted from the topic_info
        }
        
        try:
            # Extract treatment information - handle potential API failures
            treatment_info = get_diagnosis_response(f"What is the exact treatment for {selected_topic}?")
            logger.info(f"Got treatment info (length: {len(treatment_info) if treatment_info else 0})")
            
            # If we got a treatment response, use it; otherwise use a fallback
            if treatment_info and len(treatment_info) > 10:
                case_data['treatment'] = treatment_info
            else:
                # Fallback treatment
                case_data['treatment'] = f"Treatment for {selected_topic} typically includes medication, lifestyle changes, and regular follow-up with healthcare providers."
                logger.warning(f"Using fallback treatment for {selected_topic}")
        except Exception as e:
            logger.error(f"Error getting treatment info: {e}")
            # Fallback treatment
            case_data['treatment'] = f"Treatment for {selected_topic} typically includes medication, lifestyle changes, and regular follow-up with healthcare providers."
        
        try:
            # Generate differential reasoning - handle potential API failures
            # Pick a random related condition for differential diagnosis
            alternative_diagnoses = [t for t in topics if t != selected_topic]
            differential_topic = choice(alternative_diagnoses[:10] if len(alternative_diagnoses) > 10 else alternative_diagnoses)
            logger.info(f"Selected differential topic: {differential_topic}")
            
            differential_info = get_diagnosis_response(f"How do you differentiate {selected_topic} from {differential_topic}?")
            logger.info(f"Got differential info (length: {len(differential_info) if differential_info else 0})")
            
            # If we got a differential response, use it; otherwise use a fallback
            if differential_info and len(differential_info) > 10:
                case_data['differential_reasoning'] = differential_info
            else:
                # Fallback differential reasoning
                case_data['differential_reasoning'] = f"{selected_topic} and {differential_topic} can present with similar symptoms, but can be differentiated through careful history-taking and appropriate diagnostic tests."
                logger.warning(f"Using fallback differential for {selected_topic} vs {differential_topic}")
            
            case_data['differential_topic'] = differential_topic
        except Exception as e:
            logger.error(f"Error getting differential info: {e}")
            # Fallback differential reasoning
            from random import choice
            # Make sure alternative_diagnoses exists in case the exception was before it was created
            if 'alternative_diagnoses' not in locals():
                alternative_diagnoses = [t for t in topics if t != selected_topic]
            differential_topic = choice(alternative_diagnoses[:5]) if alternative_diagnoses else "related condition"
            case_data['differential_reasoning'] = f"{selected_topic} and {differential_topic} can present with similar symptoms, but can be differentiated through careful history-taking and appropriate diagnostic tests."
            case_data['differential_topic'] = differential_topic
        
        # Store case in session
        session['current_case'] = case_data
        
        # Create a client-facing response without the answers
        response_data = case_data.copy()
        response_data.pop('diagnosis', None)
        response_data.pop('treatment', None)
        response_data.pop('differential_reasoning', None)
        
        # Set up the sequential questions structure - just 2 questions as specified
        questions = [
            {
                "id": 1,
                "question": "What's your Diagnosis?",
                "field": "diagnosis"
            },
            {
                "id": 2,
                "question": "How would you treat it?",
                "field": "treatment"
            }
        ]
        
        # Add the questions to the response
        response_data['questions'] = questions
        
        # Log success for debugging
        logger.info("Successfully generated and returned new case simulation")
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error generating simulation: {e}")
        return jsonify({
            "error": "An error occurred generating the simulation. Please try again or contact support if the issue persists."
        }), 500

@app.route('/api/simulation/submit', methods=['POST'])
# Temporarily removed login_required for testing
# @login_required
def api_submit_simulation():
    """API endpoint to submit all simulation answers."""
    try:
        data = request.json
        answers = data.get('answers', {})
        case_id = data.get('case_id')
        user_id = session.get('user_id')
        
        # Get current case from session
        current_case = session.get('current_case')
        if not current_case:
            logger.warning("No active case found in session - attempt to recover")
            # If there's no case in session but we have a case_id, try to create a minimum case
            if case_id:
                logger.info(f"Creating fallback case with id: {case_id}")
                # Create a minimal case structure for evaluation
                from random import choice
                topics = [
                    "Diarrhoea", "Constipation", "Peptic Ulcer Disease", "Fever", "Headache", 
                    "Common cold", "Pneumonia", "Tuberculosis", "Malaria", "Diabetes Mellitus"
                ]
                # Use the provided case_id as the diagnosis if possible
                diagnosis = case_id if case_id in topics else choice(topics)
                current_case = {
                    'diagnosis': diagnosis,
                    'treatment': f"Treatment for {diagnosis} typically includes medications, rest, and symptomatic care.",
                    'differential_reasoning': f"{diagnosis} can be differentiated from other conditions by its characteristic symptoms.",
                    'differential_topic': case_id
                }
                # Store in session for future use
                session['current_case'] = current_case
            else:
                return jsonify({"error": "No active case found. Please start a new case."}), 400
        
        # Validate answers
        if not answers:
            return jsonify({"error": "Answers are required"}), 400
            
        # Required answer fields based on the questions
        required_fields = ['diagnosis', 'treatment']
        missing_fields = [field for field in required_fields if field not in answers]
        
        if missing_fields:
            return jsonify({"error": f"Missing required answers: {', '.join(missing_fields)}"}), 400
        
        # Evaluate diagnosis answer
        # Check if the user's answer contains key terms from the correct diagnosis
        user_diagnosis = answers['diagnosis'].lower()
        correct_diagnosis = current_case['diagnosis'].lower()
        
        # Simple string matching evaluation for diagnosis
        diagnosis_score = 0
        diagnosis_feedback = ""
        
        # Check if the key terms from the diagnosis appear in the user's answer
        diagnosis_key_terms = correct_diagnosis.split()
        matched_terms = 0
        
        for term in diagnosis_key_terms:
            if term.lower() in user_diagnosis and len(term) > 3:  # Only count meaningful terms
                matched_terms += 1
        
        # Calculate score based on term matches
        if correct_diagnosis in user_diagnosis:
            # Exact match gets full score
            diagnosis_score = 100
            diagnosis_feedback = "Perfect! Your diagnosis is correct."
        elif matched_terms >= len(diagnosis_key_terms) // 2:
            # Partial match gets partial score
            diagnosis_score = 75
            diagnosis_feedback = "Your diagnosis is close, but not quite the exact condition."
        else:
            # Few matches gets low score
            diagnosis_score = 40
            diagnosis_feedback = "Your diagnosis is different from the correct one."
        
        # Evaluate treatment answer
        treatment_score = 0
        treatment_feedback = ""
        
        # Convert to lowercase for case-insensitive matching
        user_treatment = answers['treatment'].lower()
        correct_treatment = current_case['treatment'].lower()
        
        # Check for similarity in treatment
        correct_treatment_lines = correct_treatment.split('\n')
        
        # Extract key treatments (looking for medication names, dosages, etc.)
        treatment_key_terms = []
        for line in correct_treatment_lines:
            # Look for medication names, dosages, etc.
            if any(word in line.lower() for word in ["mg", "dose", "daily", "oral", "injection", "tablets"]):
                treatment_key_terms.extend([term for term in line.split() if len(term) > 4])
        
        # If we couldn't find specific treatments, use the whole treatment text
        if not treatment_key_terms:
            treatment_key_terms = correct_treatment.split()
        
        # Count matched terms
        matched_treatment_terms = 0
        for term in treatment_key_terms:
            if term.lower() in user_treatment and len(term) > 3:
                matched_treatment_terms += 1
        
        # Calculate treatment score
        if matched_treatment_terms >= len(treatment_key_terms) // 2:
            treatment_score = 90
            treatment_feedback = "Your treatment plan is appropriate for this condition."
        elif matched_treatment_terms > 0:
            treatment_score = 60
            treatment_feedback = "Your treatment plan has some correct elements, but is missing key components."
        else:
            treatment_score = 30
            treatment_feedback = "Your treatment plan differs from the recommended approach."
        
        # Calculate overall score (weighted average)
        diagnosis_weight = 0.6  # 60% of total score
        treatment_weight = 0.4  # 40% of total score
        
        overall_score = int(
            (diagnosis_score * diagnosis_weight) + 
            (treatment_score * treatment_weight)
        )
        
        # Generate feedback based on score
        if overall_score >= 90:
            feedback = "Excellent work! Your answers demonstrate thorough understanding of the case."
        elif overall_score >= 70:
            feedback = "Good job! You've demonstrated solid clinical reasoning, but there's still room for improvement."
        elif overall_score >= 50:
            feedback = "You're on the right track, but need to improve your clinical analysis and medical knowledge."
        else:
            feedback = "Your answers need significant improvement. Review the key clinical concepts for this condition."
        
        # Save attempt if user is logged in
        if user_id:
            # Create or get case
            case_title = current_case.get('presenting_complaint', 'Unknown Case')
            case = Case.query.filter_by(title=case_title).first()
            
            if not case:
                case = Case(
                    title=case_title,
                    description=json.dumps({}),  # No patient info in new format
                    symptoms=json.dumps({}),  # No symptoms in new format
                    diagnosis=current_case.get('diagnosis', ''),
                    difficulty=2  # Medium difficulty by default
                )
                db.session.add(case)
                db.session.flush()  # To get the ID
            
            # Save attempt with answers
            attempt = CaseAttempt(
                user_id=user_id,
                case_id=case.id,
                completed=True,
                score=overall_score,
                diagnosis=json.dumps(answers),
                correct=overall_score >= 70
            )
            db.session.add(attempt)
            
            # Add points based on score
            if overall_score >= 90:
                # Excellent score
                points = 100
            elif overall_score >= 70:
                # Good score
                points = 50
            else:
                # Partial credit
                points = 20
            
            add_points(user_id, points)
            
            # Award achievement for first case
            if CaseAttempt.query.filter_by(user_id=user_id).count() == 1:
                award_achievement(user_id, 9)  # First Case Solved achievement
            
            # Award achievement for perfect score
            if overall_score >= 95:
                award_achievement(user_id, 10)  # Case Ace achievement
            
            db.session.commit()
        
        # Return result
        return jsonify({
            "score": overall_score,
            "feedback": feedback,
            "questions": [
                {
                    "id": 1,
                    "question": "What's your Diagnosis?",
                    "field": "diagnosis",
                    "correct": diagnosis_score >= 70,
                    "feedback": diagnosis_feedback
                },
                {
                    "id": 2,
                    "question": "How would you treat it?",
                    "field": "treatment",
                    "correct": treatment_score >= 70,
                    "feedback": treatment_feedback
                }
            ],
            "topic": current_case.get('topic', current_case.get('diagnosis', '')),
            "differential_topic": current_case.get('differential_topic', '')
        })
    except Exception as e:
        logger.error(f"Error submitting simulation: {e}")
        return jsonify({"error": "An error occurred processing your submission"}), 500

# Challenge API routes have been removed

# Challenge API routes have been removed

# Challenge API routes have been removed

# Challenge API routes have been removed

@app.route('/api/flashcards/topic', methods=['POST'])
def api_flashcards_topic():
    """API endpoint to get flashcards for a topic."""
    try:
        data = request.json
        topic = data.get('topic', '')
        user_id = session.get('user_id')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        # Check if flashcards for this topic already exist
        existing_cards = Flashcard.query.filter_by(topic=topic).all()
        
        if existing_cards and len(existing_cards) >= 5:
            # Return existing flashcards
            flashcards = [
                {
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "difficulty": card.difficulty
                }
                for card in existing_cards
            ]
        else:
            # Generate new flashcards
            flashcard_data = generate_flashcards(topic)
            
            if not flashcard_data or 'flashcards' not in flashcard_data:
                return jsonify({"error": "Failed to generate flashcards"}), 500
            
            # Save new flashcards
            flashcards = []
            for card_data in flashcard_data.get('flashcards', []):
                card = Flashcard(
                    topic=topic,
                    question=card_data.get('question', ''),
                    answer=card_data.get('answer', ''),
                    difficulty=card_data.get('difficulty', 1)
                )
                db.session.add(card)
                db.session.flush()  # To get the ID before commit
                
                flashcards.append({
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "difficulty": card.difficulty
                })
            
            db.session.commit()
        
        return jsonify({"flashcards": flashcards})
    except Exception as e:
        logger.error(f"Error getting flashcards: {e}")
        return jsonify({"error": "An error occurred getting flashcards"}), 500

@app.route('/api/flashcards/review', methods=['POST'])
def api_flashcard_review():
    """API endpoint to record flashcard review results."""
    try:
        data = request.json
        flashcard_id = data.get('flashcard_id')
        quality = data.get('quality')  # 0-5 rating of recall quality
        user_id = session.get('user_id')
        
        if not flashcard_id or quality is None:
            return jsonify({"error": "Flashcard ID and quality rating are required"}), 400
        
        if not user_id:
            return jsonify({"error": "User must be logged in"}), 401
        
        # Get the flashcard
        flashcard = Flashcard.query.get(flashcard_id)
        if not flashcard:
            return jsonify({"error": "Flashcard not found"}), 404
        
        # Get or create progress record
        progress = FlashcardProgress.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id
        ).first()
        
        now = datetime.utcnow()
        
        if not progress:
            # Create new progress record
            progress = FlashcardProgress(
                user_id=user_id,
                flashcard_id=flashcard_id,
                ease_factor=2.5,  # Default ease factor
                interval=1,       # Default interval (1 day)
                next_review=now + timedelta(days=1),
                last_reviewed=now
            )
            db.session.add(progress)
        else:
            # Update existing progress with SM-2 algorithm
            if quality >= 3:
                # Correct response
                if progress.interval == 1:
                    progress.interval = 6
                elif progress.interval == 6:
                    progress.interval = 25
                else:
                    progress.interval = round(progress.interval * progress.ease_factor)
                
                # Cap interval at 365 days
                progress.interval = min(progress.interval, 365)
            else:
                # Incorrect response, reset interval
                progress.interval = 1
            
            # Update ease factor
            progress.ease_factor += (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            progress.ease_factor = max(1.3, progress.ease_factor)  # Minimum ease factor is 1.3
            
            # Update timestamps
            progress.last_reviewed = now
            progress.next_review = now + timedelta(days=progress.interval)
        
        # Add points for review
        add_points(user_id, FLASHCARD_REVIEW_POINTS)
        
        # Count total flashcard reviews
        review_count = FlashcardProgress.query.filter_by(user_id=user_id).count()
        
        # Award achievement for 50 reviews
        if review_count >= 50:
            award_achievement(user_id, 13)  # Memory Master achievement
        
        # Check for perfect recall streak
        if quality == 5:
            perfect_reviews = session.get('perfect_reviews', 0) + 1
            session['perfect_reviews'] = perfect_reviews
            
            if perfect_reviews >= 10:
                award_achievement(user_id, 14)  # Perfect Recall achievement
                session['perfect_reviews'] = 0
        else:
            session['perfect_reviews'] = 0
        
        db.session.commit()
        
        return jsonify({
            "next_review": progress.next_review.strftime("%Y-%m-%d %H:%M:%S"),
            "interval": progress.interval,
            "ease_factor": progress.ease_factor
        })
    except Exception as e:
        logger.error(f"Error recording flashcard review: {e}")
        return jsonify({"error": "An error occurred recording your review"}), 500

@app.route('/api/flashcards/due', methods=['GET'])
def api_due_flashcards():
    """API endpoint to get flashcards due for review."""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User must be logged in"}), 401
        
        # Get flashcards due for review
        now = datetime.utcnow()
        due_progress = FlashcardProgress.query.filter(
            FlashcardProgress.user_id == user_id,
            FlashcardProgress.next_review <= now
        ).all()
        
        due_flashcard_ids = [p.flashcard_id for p in due_progress]
        due_flashcards = Flashcard.query.filter(Flashcard.id.in_(due_flashcard_ids)).all()
        
        return jsonify({
            "flashcards": [
                {
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "difficulty": card.difficulty,
                    "topic": card.topic
                }
                for card in due_flashcards
            ]
        })
    except Exception as e:
        logger.error(f"Error getting due flashcards: {e}")
        return jsonify({"error": "An error occurred getting due flashcards"}), 500

@app.route('/api/leaderboard', methods=['GET'])
def api_leaderboard():
    """API endpoint to get the leaderboard."""
    try:
        leaderboard_data = get_leaderboard(limit=10)
        return jsonify({"leaderboard": leaderboard_data})
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({"error": "An error occurred getting the leaderboard"}), 500

@app.route('/api/user/stats', methods=['GET'])
@login_required
def api_user_stats():
    """API endpoint to get user statistics."""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User must be logged in"}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get user statistics
        case_attempts = CaseAttempt.query.filter_by(user_id=user_id).all()
        challenge_attempts = ChallengeAttempt.query.filter_by(user_id=user_id).all()
        
        total_cases = len(case_attempts)
        correct_cases = sum(1 for attempt in case_attempts if attempt.correct)
        
        total_challenges = len(challenge_attempts)
        challenge_score = sum(attempt.score for attempt in challenge_attempts) / total_challenges if total_challenges > 0 else 0
        
        # Get achievements
        achievements = get_user_achievements(user_id)
        
        return jsonify({
            "username": user.username,
            "points": user.points,
            "streak": user.streak,
            "last_active": user.last_active.strftime("%Y-%m-%d %H:%M:%S") if user.last_active else None,
            "cases": {
                "total": total_cases,
                "correct": correct_cases,
                "accuracy": (correct_cases / total_cases * 100) if total_cases > 0 else 0
            },
            "challenges": {
                "total": total_challenges,
                "average_score": challenge_score
            },
            "achievements": achievements
        })
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({"error": "An error occurred getting user statistics"}), 500

# Authentication routes have been moved to auth.py blueprint

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search the document."""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Search document
        search_results = search_document(query)
        
        return jsonify({"results": search_results})
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({"error": "An error occurred during search"}), 500
