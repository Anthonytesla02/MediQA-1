import json
import logging
import re
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
        
        # Generate a more realistic presenting complaint without revealing the diagnosis
        prompt = f"Generate a realistic medical case presentation for a {age}-year-old {gender} with {selected_topic}, but DO NOT mention the diagnosis name anywhere in the description. Describe only the patient's symptoms, complaints, and relevant history in 1-2 sentences. Model the style after these examples: 'Patient presents with burning sensation in chest after meals' or 'Patient complains of frequent urination and excessive thirst for the past month'."
        
        try:
            # Get AI to generate a realistic presenting complaint without revealing diagnosis
            from ai_service import generate_ai_response
            messages = [
                {"role": "system", "content": "You are a medical case generator. Generate realistic patient presentations without revealing the diagnosis. Keep descriptions concise and focused on symptoms only."}, 
                {"role": "user", "content": prompt}
            ]
            generated_complaint = generate_ai_response(messages, temperature=0.7, max_tokens=100)
            
            # Clean up and validate the response
            if generated_complaint and len(generated_complaint) > 20 and selected_topic.lower() not in generated_complaint.lower():
                presenting_complaint = generated_complaint
                logger.info(f"Generated presenting complaint: {presenting_complaint[:50]}...")
            else:
                # Fallback to a generic template if something goes wrong
                presenting_complaint = f"A {age}-year-old {gender} presents to the pharmacy with signs and symptoms that require assessment."
                logger.warning("Using fallback presenting complaint template")
        except Exception as e:
            logger.error(f"Error generating presenting complaint: {e}")
            # Fallback to a generic template
            presenting_complaint = f"A {age}-year-old {gender} presents to the pharmacy with signs and symptoms that require assessment."
        
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
                # Fallback treatment (generic - doesn't reveal diagnosis)
                case_data['treatment'] = "Treatment typically includes appropriate medications, lifestyle modifications, and regular monitoring by healthcare professionals."
                logger.warning(f"Using fallback treatment for {selected_topic}")
        except Exception as e:
            logger.error(f"Error getting treatment info: {e}")
            # Fallback treatment (generic - doesn't reveal diagnosis)
            case_data['treatment'] = "Treatment typically includes appropriate medications, lifestyle modifications, and regular monitoring by healthcare professionals."
        
        # Prepare for differential diagnosis
        try:
            # Pick a random related condition for differential diagnosis
            # Safe approach - create a list of alternatives ensuring selected_topic exists
            alternative_diagnoses = [t for t in topics if t != selected_topic]
            # If we ended up with an empty list (shouldn't happen but just in case)
            if not alternative_diagnoses:
                alternative_diagnoses = ["Common cold", "Pneumonia", "Headache", "Fever"]
                
            # Choose a differential topic
            differential_topic = choice(alternative_diagnoses[:10] if len(alternative_diagnoses) > 10 else alternative_diagnoses)
            logger.info(f"Selected differential topic: {differential_topic}")
            
            # Get differential reasoning information
            differential_info = get_diagnosis_response(f"How do you differentiate {selected_topic} from {differential_topic}?")
            logger.info(f"Got differential info (length: {len(differential_info) if differential_info else 0})")
            
            # If we got a differential response, use it; otherwise use a fallback
            if differential_info and len(differential_info) > 10:
                case_data['differential_reasoning'] = differential_info
            else:
                # Fallback differential reasoning
                case_data['differential_reasoning'] = f"These conditions can present with similar symptoms, but can be differentiated through careful history-taking and appropriate diagnostic tests."
                logger.warning(f"Using fallback differential for {selected_topic} vs {differential_topic}")
            
            # Save the differential topic
            case_data['differential_topic'] = differential_topic
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Error getting differential info: {e}")
            
            # Create safe fallback
            from random import choice
            fallback_topics = ["Common cold", "Pneumonia", "Headache", "Fever", "Malaria"]
            differential_topic = choice(fallback_topics)
            
            # Set fallback differential information
            case_data['differential_reasoning'] = "Differential diagnosis requires careful assessment of presenting symptoms, medical history, and appropriate diagnostic tests."
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
                
                # Use a generic treatment description that doesn't reveal the diagnosis
                from ai_service import get_diagnosis_response
                try:
                    treatment_info = get_diagnosis_response(f"What is the exact treatment for {diagnosis}?")
                    if not treatment_info or len(treatment_info) < 10:
                        treatment_info = "Treatment typically includes appropriate medications and lifestyle modifications based on clinical presentation."
                except Exception:
                    treatment_info = "Treatment typically includes appropriate medications and lifestyle modifications based on clinical presentation."
                    
                current_case = {
                    'diagnosis': diagnosis,
                    'treatment': treatment_info,
                    'differential_reasoning': "Differential diagnosis requires careful assessment of presenting symptoms, medical history, and appropriate tests.",
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
        
        # Handle compound diagnoses or subtypes (e.g., "Uncomplicated Malaria")
        # Extract main diagnosis and subtypes
        main_diagnosis = ''
        subtype = ''
        
        # Split the diagnosis to potentially identify subtype
        diagnosis_parts = correct_diagnosis.split()
        
        # Look for common subtype indicators like "uncomplicated", "severe", "chronic", etc.
        subtype_indicators = ['uncomplicated', 'complicated', 'severe', 'mild', 'moderate', 'acute', 'chronic']
        
        # Try to identify main diagnosis and subtype
        if len(diagnosis_parts) > 1:
            # Check if the first word is a subtype indicator
            if diagnosis_parts[0].lower() in subtype_indicators:
                subtype = diagnosis_parts[0].lower()
                main_diagnosis = ' '.join(diagnosis_parts[1:]).lower()
            # Or if the last word is a subtype
            elif diagnosis_parts[-1].lower() in subtype_indicators:
                subtype = diagnosis_parts[-1].lower()
                main_diagnosis = ' '.join(diagnosis_parts[:-1]).lower()
            else:
                # Just use the whole thing as main diagnosis
                main_diagnosis = correct_diagnosis
        else:
            main_diagnosis = correct_diagnosis
            
        # Now we check if the user correctly identified both the main diagnosis and its subtype (if applicable)
        if correct_diagnosis in user_diagnosis:
            # Exact match gets full score
            diagnosis_score = 100
            diagnosis_feedback = "Perfect! Your diagnosis is correct."
        elif main_diagnosis in user_diagnosis:
            if subtype and subtype not in user_diagnosis:
                # Got main diagnosis but missed the subtype
                diagnosis_score = 80
                diagnosis_feedback = f"Your diagnosis identifies the correct condition, but doesn't specify the exact subtype. The correct diagnosis is: {current_case['diagnosis']}."
            else:
                # Just get main diagnosis
                diagnosis_score = 90
                diagnosis_feedback = f"Your diagnosis is very close to the correct one. The precise diagnosis is: {current_case['diagnosis']}."
        else:
            # Check if key terms from main diagnosis are present
            diagnosis_key_terms = main_diagnosis.split()
            matched_terms = 0
            
            for term in diagnosis_key_terms:
                if term.lower() in user_diagnosis and len(term) > 3:  # Only count meaningful terms
                    matched_terms += 1
            
            # Calculate score based on term matches
            if matched_terms >= len(diagnosis_key_terms) // 2:
                # Partial match gets partial score
                diagnosis_score = 60
                diagnosis_feedback = f"Your diagnosis is close, but not quite the exact condition. The correct diagnosis is: {current_case['diagnosis']}."
            else:
                # Few matches gets low score
                diagnosis_score = 40
                diagnosis_feedback = f"Your diagnosis is different from the correct one. The correct diagnosis is: {current_case['diagnosis']}."
        
        # Evaluate treatment answer
        treatment_score = 0
        treatment_feedback = ""
        
        # Convert to lowercase for case-insensitive matching
        user_treatment = answers['treatment'].lower()
        
        # Check if there was an error in the treatment info (rate limiting or API failure)
        if "Error connecting to AI service" in current_case['treatment']:
            # Handle the API error gracefully
            treatment_score = 80  # Give a decent score to avoid frustrating users
            correct_treatment = "Could not verify treatment due to API limitations. Common treatments for this condition typically include specific medications and management strategies appropriate for the severity and patient characteristics."
            treatment_feedback = f"Your treatment plan cannot be fully evaluated due to API limits. {correct_treatment}"
        else:
            correct_treatment = current_case['treatment'].lower()
        
        # Ensure we're evaluating against the appropriate treatment for the specific diagnosis/subtype
        # This is especially important for conditions with multiple subtypes
        
        # First, check if the treatment has sections for different subtypes
        treatment_sections = {}
        current_section = 'general'
        treatment_sections[current_section] = []
        
        # Try to identify if the treatment has different sections for different subtypes
        for line in correct_treatment.split('\n'):
            line = line.strip().lower()
            # Check if this line is a subtype header like "For uncomplicated malaria:" or similar
            if line.startswith('for ') and (':' in line or '-' in line):
                # Extract the subtype from the header
                subtype_header = line.split(':')[0].split('-')[0].replace('for ', '').strip()
                current_section = subtype_header
                treatment_sections[current_section] = []
            elif len(line) > 3:  # Avoid empty lines
                treatment_sections[current_section].append(line)
        
        # Now we determine which section of the treatment to compare against based on the diagnosis
        evaluation_section = 'general'
        if subtype and subtype in treatment_sections:
            # If we identified a subtype in the diagnosis, use that section
            evaluation_section = subtype
        elif 'general' not in treatment_sections and len(treatment_sections) == 1:
            # If there's only one section and it's not 'general', use that
            evaluation_section = list(treatment_sections.keys())[0]
        elif main_diagnosis in treatment_sections:
            # If the main diagnosis is a section, use that
            evaluation_section = main_diagnosis
            
        # Extract key terms from the appropriate treatment section
        treatment_key_terms = []
        evaluation_text = '\n'.join(treatment_sections.get(evaluation_section, correct_treatment.split('\n')))
        
        # Parse the full treatment text into structured parts: treatments, and/or relationships
        treatments = []
        current_treatment = ""
        
        # Extract structured treatments with consideration for 'And'/'Or' relationships
        treatment_blocks = []
        current_block = []
        
        # First, detect if the text has 1st/2nd/3rd line treatment blocks
        treatment_lines = [line.strip() for line in evaluation_text.split('\n') if line.strip()]
        has_treatment_lines = any('line treatment' in line.lower() for line in treatment_lines)
        
        # If we have line treatments, process them differently
        if has_treatment_lines:
            current_line = None
            for line in treatment_lines:
                line_lower = line.lower()
                
                # Check if this is a new treatment line header
                if any(pattern in line_lower for pattern in ['1st line', 'first line', '2nd line', 'second line', '3rd line', 'third line']):
                    if current_line and current_block:
                        treatment_blocks.append((current_line, current_block))
                        current_block = []
                    current_line = line
                elif line.strip() and len(line) > 5:
                    # This is content for the current treatment line
                    if current_line:
                        current_block.append(line)
            
            # Add the last block if it exists
            if current_line and current_block:
                treatment_blocks.append((current_line, current_block))
        else:
            # No line treatments, treat everything as one block
            treatment_blocks.append(("Treatment", treatment_lines))
        
        # Now process each block to extract treatments and relationships
        structured_treatments = []
        
        for block_name, block_lines in treatment_blocks:
            # Process the block to find 'And'/'Or' relationships
            or_groups = []
            current_or_group = []
            
            for line in block_lines:
                line = line.strip()
                line_lower = line.lower()
                
                # Skip empty lines or headers
                if not line or line.lower() in ['or', 'and']:
                    continue
                
                # Check if this is a new 'or' treatment option
                if line_lower.startswith('or ') or (len(or_groups) > 0 and current_or_group and 'or' in line_lower.split()[:2]):
                    # Clean up the 'or' prefix if present
                    if line_lower.startswith('or '):
                        line = line[3:].strip()
                    
                    # Start a new 'or' group if needed
                    if not current_or_group:
                        current_or_group.append(line)
                    else:
                        # If we have an existing group, save it and start a new one
                        or_groups.append(current_or_group)
                        current_or_group = [line]
                elif 'and' in line_lower.split()[:2] and current_or_group:
                    # This is an 'and' addition to the current treatment
                    # Clean up the 'and' prefix if present
                    if line_lower.startswith('and '):
                        line = line[4:].strip()
                    
                    current_or_group.append(("AND", line))
                else:
                    # Regular line, add to current group
                    if not current_or_group:
                        current_or_group = [line]
                    else:
                        # Check if it's a continuation of previous line
                        if any(c.isalpha() for c in line) and line[0].islower():
                            # It's a continuation, append to the last item
                            if isinstance(current_or_group[-1], tuple):
                                # Append to the AND item
                                and_marker, and_text = current_or_group[-1]
                                current_or_group[-1] = (and_marker, and_text + ' ' + line)
                            else:
                                # Append to the regular item
                                current_or_group[-1] += ' ' + line
                        else:
                            # New item in the group
                            current_or_group.append(line)
            
            # Add the last group if it exists
            if current_or_group:
                or_groups.append(current_or_group)
            
            structured_treatments.append((block_name, or_groups))
        
        # Check if the user's treatment answer matches any of the structured treatments
        user_treatment_lower = user_treatment.lower()
        
        # Extract medication names and key details from the user's answer
        user_meds = set()
        user_treatment_phrases = user_treatment_lower.split('\n')
        
        for phrase in user_treatment_phrases:
            # Split phrases at commas, periods, or semicolons
            parts = re.split(r'[,;.] |[,;.]', phrase)
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Check if this is a medication with dosage info
                if any(term in part for term in ['mg', 'ml', 'units', 'oral', 'topical', 'daily', 'hourly', 'weekly', 'tabs', 'tablets', 'capsule', 'cream', 'ointment']):
                    user_meds.add(part)
                
                # Also look for medication names without dosage (at least 3 chars, not common words)
                words = part.split()
                for word in words:
                    if len(word) >= 3 and not word in ['the', 'and', 'for', 'with', 'this', 'that', 'dose', 'take', 'then', 'hours', 'days', 'weeks']:
                        med_candidates = [word]
                        # Also check for 2-word medication names
                        for i, w in enumerate(words):
                            if w == word and i < len(words) - 1:
                                med_candidates.append(word + ' ' + words[i+1])
                        
                        for med in med_candidates:
                            # Only add if it might be a medication (not a common word)
                            if not med.lower() in ['treatment', 'therapy', 'patient', 'adult', 'child', 'children', 'should', 'could']:
                                user_meds.add(med)
        
        # Function to check if a medication/treatment is present in the user's answer
        def treatment_match(treatment_text, user_meds):
            # Normalize the treatment text (remove punctuation, lowercase)
            treatment_lower = treatment_text.lower()
            
            # Handle dosage ranges in treatment (e.g., "500 mg - 1 g" or "6-8 hourly")
            treatment_lower = re.sub(r'(\d+)\s*-\s*(\d+)\s*([a-zA-Z]+)', r'\1\3 or \2\3', treatment_lower)
            treatment_lower = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 or \2', treatment_lower)
            
            # Extract key components (medication name, dosage, frequency, duration)
            key_parts = [part.strip() for part in re.split(r'[,;.]', treatment_lower) if part.strip()]
            
            # Extract medication name (usually the first part before a comma)
            med_name = key_parts[0] if key_parts else ""
            
            # Flag to track if the medication name was matched
            med_name_matched = False
            
            # Check if the medication name is in user's answer
            for user_med in user_meds:
                if med_name and med_name in user_med:
                    med_name_matched = True
                    break
                
                # Also check if any word in med_name is in user_med (for partial matches)
                med_words = [w for w in med_name.split() if len(w) > 3 and not w in ['oral', 'therapy', 'treatment', 'apply', 'dose']]
                for word in med_words:
                    if word in user_med:
                        med_name_matched = True
                        break
                
                if med_name_matched:
                    break
            
            # If main medication is included, that's often sufficient
            return med_name_matched
        
        # Calculate score based on the structured treatments
        treatment_score = 0
        treatment_matches = []
        
        # Track if any treatment line is matched
        any_line_matched = False
        
        for block_name, or_groups in structured_treatments:
            # For each treatment line (1st, 2nd, 3rd, or just "Treatment")
            block_match = False
            
            for or_group in or_groups:
                # Check if any OR option within this group matches
                or_match = False
                matching_treatment = None
                
                # Track AND items that need to be matched within this OR group
                and_items = [item for item in or_group if isinstance(item, tuple) and item[0] == "AND"]
                regular_items = [item for item in or_group if not isinstance(item, tuple)]
                
                # Check if any regular item matches
                for item in regular_items:
                    if treatment_match(item, user_meds):
                        or_match = True
                        matching_treatment = item
                        break
                
                # If a regular treatment matched, also check AND items
                if or_match and and_items:
                    # All AND items must match
                    all_and_matched = True
                    for _, and_item in and_items:
                        if not treatment_match(and_item, user_meds):
                            all_and_matched = False
                            break
                    
                    # Update the match status based on AND requirements
                    or_match = all_and_matched
                
                # If any OR group matched completely (including AND requirements)
                if or_match:
                    block_match = True
                    if matching_treatment:
                        treatment_matches.append(matching_treatment)
                    break
            
            # If any treatment in this block matched
            if block_match:
                any_line_matched = True
                # First line treatments get highest score, but any match is considered good
                if '1st' in block_name or 'first' in block_name.lower():
                    treatment_score = 100
                else:
                    treatment_score = max(treatment_score, 90)  # At least 90 for matching any treatment line
        
        # Set score and feedback based on matches
        if any_line_matched:
            treatment_score = max(treatment_score, 90)
            treatment_feedback = "Your treatment plan is appropriate for this condition."
        else:
            # Check if there are partial matches by comparing key terms
            treatment_key_terms = []
            
            # Extract terms from all treatment blocks
            for block_name, or_groups in structured_treatments:
                for or_group in or_groups:
                    for item in or_group:
                        if isinstance(item, tuple):
                            _, text = item
                        else:
                            text = item
                        
                        # Look for medication names, dosages, etc.
                        if any(word in text.lower() for word in ["mg", "dose", "daily", "oral", "injection", "tablets", "capsule", "cream", "ointment"]):
                            treatment_key_terms.extend([term for term in text.split() if len(term) > 4])
            
            # Add specific medication names that might be shorter than 4 characters
            common_meds = ['ace', 'arb', 'ppi', 'ssri', 'nsaid', 'hrt', 'otc']
            for block_name, or_groups in structured_treatments:
                for or_group in or_groups:
                    for item in or_group:
                        if isinstance(item, tuple):
                            _, text = item
                        else:
                            text = item
                            
                        for med in common_meds:
                            if med in text.lower().split():
                                treatment_key_terms.append(med)
            
            # If we couldn't find specific treatments, use all words
            if not treatment_key_terms:
                for block_name, or_groups in structured_treatments:
                    for or_group in or_groups:
                        for item in or_group:
                            if isinstance(item, tuple):
                                _, text = item
                            else:
                                text = item
                            treatment_key_terms.extend(text.split())
            
            # Count matched terms
            matched_treatment_terms = 0
            for term in treatment_key_terms:
                if term.lower() in user_treatment_lower and len(term) > 3:
                    matched_treatment_terms += 1
            
            # Calculate treatment score based on partial matches
            min_term_count = min(len(treatment_key_terms), 20)  # Cap at 20 terms to prevent overwhelming requirements
            required_matches = max(min_term_count // 3, 2)  # At least 1/3 of terms (minimum 2) for a decent score
            good_matches = max(min_term_count // 2, 3)  # At least 1/2 of terms (minimum 3) for a good score
            
            if matched_treatment_terms >= good_matches:
                treatment_score = 70
                treatment_feedback = "Your treatment plan has most of the correct elements for this condition."
            elif matched_treatment_terms >= required_matches:
                treatment_score = 50
                treatment_feedback = "Your treatment plan has some correct elements, but is missing key components."
            else:
                treatment_score = 30
            
            # Format the correct treatment answer in a clean, concise way
            treatment_feedback = "Your treatment plan differs from the recommended approach.\nCorrect answer:"
            
            # Check if we have matched treatments to display
            if treatment_matches:
                # Format the matched treatments cleanly
                formatted_treatments = []
                
                # First, collect all matched treatments
                for treatment in treatment_matches:
                    # Clean up the treatment text - remove excessive whitespace
                    clean_treatment = re.sub(r'\s+', ' ', treatment).strip()
                    
                    # Add to our formatted list if not already included
                    if clean_treatment not in formatted_treatments:
                        formatted_treatments.append(clean_treatment)
                
                # If nothing was found, show the first appropriate treatment from the structured blocks
                if not formatted_treatments:
                    for block_name, or_groups in structured_treatments:
                        if '1st' in block_name or 'first' in block_name.lower() or 'Treatment' == block_name:
                            # Prefer first line treatments or general treatment
                            if or_groups and or_groups[0]:
                                # Get the first treatment option
                                first_treatment = or_groups[0][0]
                                if isinstance(first_treatment, tuple):
                                    first_treatment = first_treatment[1]  # Get text from tuple
                                
                                # Clean and add to formatted list
                                clean_treatment = re.sub(r'\s+', ' ', first_treatment).strip()
                                formatted_treatments.append(clean_treatment)
                                break
                
                # Filter out any IV/IM treatments - not relevant for pharmacy
                filtered_treatments = []
                for treatment in formatted_treatments:
                    # Skip treatments with IV/IM/injection content
                    if not re.search(r'\b(IV|iv|intravenous|IM|im|intramuscular|injection|infusion|surgical|surgery|incision|drain|catheter|lumbar|puncture|biopsy)\b', treatment):
                        filtered_treatments.append(treatment)
                
                # If filtering removed everything, fall back to the original list
                if not filtered_treatments and formatted_treatments:
                    filtered_treatments = formatted_treatments
                
                # Format the feedback with bullet points
                if filtered_treatments:
                    treatment_feedback += "\n• " + "\n• ".join(filtered_treatments[:5])  # Limit to 5 key treatments
                else:
                    # Use the original treatment as last resort
                    treatment_text = current_case['treatment']
                    treatment_lines = [line.strip() for line in treatment_text.split('.') if len(line.strip()) > 10]
                    # Take only a few lines to keep it concise
                    formatted_text = ".\n• ".join(treatment_lines[:5]) + "."
                    treatment_feedback += "\n" + formatted_text
            else:
                # No matches found, use the original treatment text as a fallback
                treatment_text = current_case['treatment']
                # Clean up the text and format with bullet points
                clean_lines = []
                
                # Split by periods and newlines to get separate statements
                for line in re.split(r'\.|\n', treatment_text):
                    line = line.strip()
                    if len(line) > 10:
                        # Skip lines with IV/IM content
                        if not re.search(r'\b(IV|iv|intravenous|IM|im|intramuscular|injection|infusion|surgical|surgery|incision|drain|catheter|lumbar|puncture|biopsy)\b', line):
                            clean_lines.append(line)
                
                # Format with bullet points, limit to 5 key treatments
                if clean_lines:
                    treatment_feedback += "\n• " + "\n• ".join(clean_lines[:5])
                else:
                    # Last resort - just show the original treatment
                    treatment_feedback += "\n" + treatment_text
        
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
            presenting_complaint = current_case.get('presenting_complaint', 'Unknown Case')
            # Create a shorter title (first 100 chars + ellipsis if needed)
            case_title = presenting_complaint[:100] + ('...' if len(presenting_complaint) > 100 else '')
            case = Case.query.filter_by(title=case_title).first()
            
            if not case:
                case = Case(
                    title=case_title,
                    description=json.dumps({'presenting_complaint': presenting_complaint}),  # Store full complaint
                    symptoms=json.dumps({}),  # No symptoms in new format
                    diagnosis=current_case.get('diagnosis', ''),
                    difficulty=2  # Medium difficulty by default
                )
                db.session.add(case)
                db.session.flush()  # To get the ID
            
            # Save attempt with answers
            try:
                # Convert answers to a more concise format to avoid varchar limits
                answers_truncated = {}
                for key, value in answers.items():
                    # Limit each answer to 100 characters to fit column size
                    answers_truncated[key] = value[:100] + '...' if len(value) > 100 else value
                
                attempt = CaseAttempt(
                    user_id=user_id,
                    case_id=case.id,
                    completed=True,
                    score=overall_score,
                    diagnosis=json.dumps(answers_truncated),
                    correct=overall_score >= 70
                )
                db.session.add(attempt)
            except Exception as e:
                logger.error(f"Error adding attempt: {e}")
                # Continue even if saving the attempt fails
            
            # Add points based on score
            try:
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
            except Exception as e:
                logger.error(f"Error adding points: {e}")
                # Continue even if adding points fails
            
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
            "topic": current_case.get('topic', 'Medical Condition'),
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
