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
@login_required
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
def api_new_simulation():
    """API endpoint to get a new simulation case."""
    try:
        # Generate case with improved logging
        logger.info("Requesting new case simulation from AI")
        case_data = generate_case_simulation()
        
        if not case_data:
            logger.error("Case simulation generation returned None")
            return jsonify({
                "error": "Failed to generate case simulation. The AI service may be experiencing issues."
            }), 500
        
        # Validate case data
        required_fields = ['patient_info', 'presenting_complaint', 'history', 'examination', 'vitals', 'diagnosis']
        missing_fields = [field for field in required_fields if field not in case_data]
        
        if missing_fields:
            logger.error(f"Missing required fields in case data: {missing_fields}")
            return jsonify({"error": f"Case data is missing required fields: {', '.join(missing_fields)}"}), 500
        
        # Store case in session
        session['current_case'] = case_data
        
        # Remove diagnosis from response to avoid spoilers
        response_data = case_data.copy()
        response_data.pop('diagnosis', None)
        response_data.pop('reasoning', None)
        response_data.pop('differential_diagnoses', None)
        
        # Log success for debugging
        logger.info("Successfully generated and returned new case simulation")
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error generating simulation: {e}")
        return jsonify({
            "error": "An error occurred generating the simulation. Please try again or contact support if the issue persists."
        }), 500

@app.route('/api/simulation/submit', methods=['POST'])
def api_submit_simulation():
    """API endpoint to submit simulation answers."""
    try:
        data = request.json
        mc_answers = data.get('mc_answers', {})
        ft_answers = data.get('ft_answers', {})
        user_id = session.get('user_id')
        
        # Get current case from session
        current_case = session.get('current_case')
        if not current_case:
            return jsonify({"error": "No active case found"}), 400
        
        # Validate multiple choice answers
        if not mc_answers:
            return jsonify({"error": "Multiple choice answers are required"}), 400
            
        # Validate free text answers
        if not ft_answers:
            return jsonify({"error": "Free text answers are required"}), 400
        
        # Evaluate multiple choice answers
        mc_results = []
        mc_score = 0
        mc_questions = current_case.get('multiple_choice_questions', [])
        
        for q_id_str, answer in mc_answers.items():
            q_id = int(q_id_str)
            if q_id < len(mc_questions):
                question = mc_questions[q_id]
                is_correct = answer == question.get('correct_answer')
                
                mc_results.append({
                    'question': question.get('question', 'Unknown question'),
                    'user_answer': answer,
                    'correct_answer': question.get('correct_answer', ''),
                    'correct': is_correct
                })
                
                if is_correct:
                    mc_score += 1
        
        mc_percent = (mc_score / len(mc_questions)) * 100 if mc_questions else 0
        
        # Evaluate free text answers
        ft_results = []
        ft_score = 0
        ft_questions = current_case.get('free_text_questions', [])
        
        for q_id_str, answer in ft_answers.items():
            q_id = int(q_id_str)
            if q_id < len(ft_questions):
                question = ft_questions[q_id]
                
                # Get key concepts from question
                key_concepts = question.get('key_concepts', [])
                ideal_answer = question.get('ideal_answer', '')
                
                # Simple concept matching (case-insensitive)
                matched_concepts = []
                missing_concepts = []
                
                # Check each concept
                for concept in key_concepts:
                    if concept.lower() in answer.lower():
                        matched_concepts.append(concept)
                    else:
                        missing_concepts.append(concept)
                
                # Calculate score based on matched concepts
                question_score = (len(matched_concepts) / len(key_concepts)) * 100 if key_concepts else 0
                
                ft_results.append({
                    'question': question.get('question', 'Unknown question'),
                    'user_answer': answer,
                    'ideal_answer': ideal_answer,
                    'matched_concepts': matched_concepts,
                    'missing_concepts': missing_concepts,
                    'score': question_score
                })
                
                ft_score += question_score
        
        ft_percent = ft_score / len(ft_questions) if ft_questions else 0
        
        # Calculate overall score (50% from MC, 50% from FT)
        overall_score = int((mc_percent * 0.5) + (ft_percent * 0.5))
        
        # Generate feedback based on score
        if overall_score >= 90:
            feedback = "Excellent work! Your answers demonstrate thorough understanding of the clinical scenario and medical concepts."
        elif overall_score >= 70:
            feedback = "Good job! You've demonstrated solid clinical reasoning, but there's still room for improvement."
        elif overall_score >= 50:
            feedback = "You're on the right track, but need to improve your clinical analysis and knowledge of key medical concepts."
        else:
            feedback = "Your answers need significant improvement. Review the key clinical concepts and medical knowledge relevant to this case."
        
        # Save attempt if user is logged in
        if user_id:
            # Create or get case
            case_title = current_case.get('presenting_complaint', 'Unknown Case')
            case = Case.query.filter_by(title=case_title).first()
            
            if not case:
                case = Case(
                    title=case_title,
                    description=json.dumps(current_case.get('patient_info', {})),
                    symptoms=json.dumps(current_case.get('history', {})),
                    diagnosis=current_case.get('diagnosis', ''),
                    difficulty=2  # Medium difficulty by default
                )
                db.session.add(case)
                db.session.commit()
            
            # Save attempt with combined answers
            combined_answers = {
                'mc_answers': mc_answers,
                'ft_answers': ft_answers
            }
            
            attempt = CaseAttempt(
                user_id=user_id,
                case_id=case.id,
                completed=True,
                score=overall_score,
                diagnosis=json.dumps(combined_answers),
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
            "diagnosis": current_case.get('diagnosis', ''),
            "reasoning": current_case.get('reasoning', ''),
            "differential_diagnoses": current_case.get('differential_diagnoses', []),
            "mc_results": mc_results,
            "ft_results": ft_results
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
