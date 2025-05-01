import os
import logging
import json
import random
import requests
from config import MISTRAL_API_KEY
from rag_engine import generate_context_for_query

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def generate_ai_response(messages, temperature=0.7, max_tokens=1000):
    """Generate a response from Mistral AI."""
    # Check if API key is set to a valid value
    if MISTRAL_API_KEY in ["YOUR_MISTRAL_API_KEY", "", None]:
        logger.warning("Mistral API key not configured. Using fallback response.")
        return "API key not configured. Please provide a valid Mistral API key in the environment variables."
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    payload = {
        "model": "mistral-medium",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # Log entire request for debugging (without API key)
    debug_payload = payload.copy()
    logger.debug(f"Payload: {json.dumps(debug_payload)}")
    
    try:
        # Log request for debugging
        logger.info(f"Making API request to Mistral AI with {len(messages)} messages")
        
        # Direct API call to Mistral AI with shorter timeout
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=30)
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_message = "Error connecting to AI service. Please try again later."
            
            # Add specific handling for rate limiting errors
            if response.status_code == 429:
                logger.error(f"Mistral API rate limit exceeded: {response.text}")
                error_message = "API rate limit exceeded. The system is currently handling too many requests. Please try again in a few minutes."
            else:
                logger.error(f"Mistral API error: Status {response.status_code}, Response: {response.text}")
            
            # Return a more specific fallback message
            return error_message
        
        # Parse the response
        try:
            response_json = response.json()
            
            # Log response for debugging (useful for understanding API structure)
            logger.debug(f"Mistral API raw response: {json.dumps(response_json)}")
            
            if not response_json.get("choices") or len(response_json["choices"]) == 0:
                logger.error(f"Mistral API returned no choices: {response_json}")
                # Return a fallback message instead of None
                return "AI service returned an incomplete response. Please try again later."
                
            return response_json["choices"][0]["message"]["content"]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}. Raw response: {response.text}")
            # Return a fallback message instead of None
            return "Error processing AI response. Please try again later."
    except requests.exceptions.Timeout:
        logger.error("Mistral API request timed out after 30 seconds")
        # Return a fallback message instead of None
        return "AI service request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to Mistral API: {e}")
        # Return a fallback message instead of None
        return "Network error connecting to AI service. Please try again later."
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        # Return a fallback message instead of None
        return "Unexpected error with AI service. Please try again later."

def get_diagnosis_response(user_query):
    """Get an AI diagnosis response based on the user query."""
    # Generate context from document
    context = generate_context_for_query(user_query)
    
    # Check if it's a treatment or diagnosis query to customize prompt
    query_lower = user_query.lower()
    
    # Check for treatment-related queries
    treatment_phrases = ['treatment for', 'treatment of', 'how to treat', 'medicine for', 
                        'drug for', 'therapy for', 'exact treatment', 'management of']
    
    # Check for diagnosis-related queries
    diagnosis_phrases = ['diagnosis of', 'symptoms of', 'signs of', 'diagnosing', 
                        'diagnostic criteria', 'what is', 'what diagnosis']
    
    is_treatment_query = any(phrase in query_lower for phrase in treatment_phrases)
    is_diagnosis_query = any(phrase in query_lower for phrase in diagnosis_phrases)
    
    # Base system prompt - then customize based on query type
    system_content = f"""You are a precise medical assistant that references the Standard Treatment Guidelines.
    Base your responses ONLY on the following medical reference information:
    
    {context}
    
    IMPORTANT INSTRUCTIONS:
    1. Be extremely concise - only provide relevant information.
    2. Focus only on factual information from the reference material.
    3. Format key points with bullet points when appropriate.
    4. Do not include any personal opinions or information not found in the reference.
    5. If the reference doesn't contain relevant information, simply state "The guidelines do not contain specific information about this query."
    """
    
    # Add specific instructions for treatment queries
    if is_treatment_query:
        system_content += """
        Since this is a treatment query, your response should:
        - Begin with the standard/recommended treatment
        - List medications with dosages if specified in the reference
        - Note any alternative treatments or stepwise approaches
        - Include only treatment information, not general disease background
        - Format as a brief, structured treatment plan
        """
    
    # Add specific instructions for diagnosis queries
    elif is_diagnosis_query:
        system_content += """
        Since this is a diagnosis query, your response should:
        - Begin with a clear definition or diagnostic criteria
        - List key symptoms and signs in bullet point format
        - Include any diagnostic tests mentioned in the reference
        - Focus on identification criteria only, not treatment options
        - Keep explanations minimal and fact-based
        """
    
    # Create messages for AI with context and query-specific guidance
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_query}
    ]
    
    # Generate response
    response = generate_ai_response(messages)
    return response

def generate_case_simulation():
    """Generate a simulated patient case with sequential questions."""
    # Get a random topic from the curated list
    curated_topics = [
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
    selected_topic = random.choice(curated_topics)
    logger.info(f"Selected topic for case simulation: {selected_topic}")
    
    # Get relevant document content for the selected topic
    from document_processor import search_document
    from rag_engine import generate_context_for_query
    topic_info = generate_context_for_query(selected_topic)
    
    # Create a medical case based on the selected topic
    case_data = create_medical_case_from_topic(selected_topic, topic_info)
    
    return case_data

def create_medical_case_from_topic(topic, topic_info):
    """Create a medical case based on a specific topic and information."""
    # Generate a differential diagnosis for the case (another condition with similar symptoms)
    differential_topics = [
        "Common cold", "Pneumonia", "Influenza", "Bronchitis", "Sinusitis", "Pharyngitis",
        "Gastroenteritis", "Food poisoning", "Irritable Bowel Syndrome", "Peptic Ulcer Disease",
        "Migraine", "Tension headache", "Cluster headache", "Allergic rhinitis", "Asthma"
    ]
    differential_diagnosis = random.choice([d for d in differential_topics if d != topic])
    
    # Generate the case via AI with specific instructions for the required format
    messages = [
        {"role": "system", "content": """You are a medical case generator for healthcare student training.
        Create a realistic but concise medical case about the specified condition.
        Follow these specific guidelines to create challenging but realistic cases:
        
        1. BE SPECIFIC: If the condition has subtypes (e.g., complicated vs. uncomplicated malaria), select ONE specific subtype and make it clear in the diagnosis field. Don't create cases that require treating multiple subtypes.
        
        2. REALISTIC SYMPTOM PRESENTATION: Include only 3-5 key symptoms/signs in the presenting complaint. Real patients rarely present with all textbook symptoms.
        
        3. AVOID DIAGNOSTIC GIVEAWAYS: Don't include obvious diagnostic clues (like mentioning mosquito bites for malaria). The clinician should diagnose based on symptoms and history, not explicit hints.
        
        The format must follow this structure exactly:
        1. A short patient profile (age, gender, occupation if relevant)
        2. Presenting complaint (3-5 chief symptoms reported by patient, without obvious diagnostic clues)
        3. Patient history (relevant medical history, include only: blood pressure, blood sugar, allergies, current medications)
        4. Diagnosis (the SPECIFIC medical diagnosis including subtype if relevant)
        5. Treatment (the appropriate treatment plan for ONLY the specific diagnosis/subtype, limited to oral medications, topical treatments, and lifestyle modifications that can be provided by a pharmacy - NO injections, IV treatments, or surgical procedures)
        6. Differential reasoning (why this diagnosis instead of the given alternative)
        
        Format the output as a JSON object with these exact keys: 
        patient_info, presenting_complaint, patient_history, diagnosis, treatment, differential_reasoning."""}, 
        {"role": "user", "content": f"Create a case about {topic}. The differential diagnosis to discuss is {differential_diagnosis}. Use relevant medical information about {topic} symptoms, diagnosis and treatment. For specific conditions like malaria, select and specify ONE subtype (e.g., 'Uncomplicated Malaria' or 'Severe Malaria') and only include treatment for that specific subtype. Keep it concise but medically accurate."}
    ]
    
    try:
        response = generate_ai_response(messages, temperature=0.7)
        # Try to parse the JSON from the response
        import json
        
        # Clean up the response in case it contains markdown formatting
        if '```json' in response and '```' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        # Additional cleanup to handle potential JSON issues
        response = response.replace('\n', ' ').replace('\r', ' ')
        response = response.replace('\\', '\\\\')  # Escape backslashes
        
        # Try to find and fix common JSON syntax errors
        response = response.replace('},}', '}}')   # Fix double closing
        response = response.replace(',}', '}')     # Fix trailing commas
        response = response.replace('{,', '{')     # Fix leading commas
        
        # Log the cleaned response for debugging
        logger.debug(f"Cleaned JSON response: {response}")
        
        try:
            case_data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Problematic JSON: {response}")
            # Create a fallback case
            return create_fallback_case_from_topic(topic, differential_diagnosis)
        
        # Ensure all required fields are present
        required_fields = ['patient_info', 'presenting_complaint', 'patient_history', 'diagnosis', 'treatment', 'differential_reasoning']
        missing_fields = [field for field in required_fields if field not in case_data]
        
        if missing_fields:
            logger.error(f"AI-generated case missing fields: {missing_fields}")
            # Create a fallback case
            case_data = create_fallback_case_from_topic(topic, differential_diagnosis)
        
        # Add the topics for reference
        case_data['topic'] = topic
        case_data['differential_topic'] = differential_diagnosis
        
        return case_data
    except Exception as e:
        logger.error(f"Error creating case from topic: {e}")
        return create_fallback_case_from_topic(topic, differential_diagnosis)

def create_fallback_case_from_topic(topic, differential_diagnosis):
    """Create a fallback case when AI generation fails."""
    # Basic template for a fallback case
    case = {
        'patient_info': f"35-year-old patient with symptoms of {topic}",
        'presenting_complaint': f"Main symptoms consistent with {topic}", 
        'patient_history': "Blood pressure: Normal, Blood sugar: Normal, Allergies: None, Medications: None",
        'diagnosis': topic,
        'treatment': f"Standard treatment for {topic}",
        'differential_reasoning': f"The symptoms are more consistent with {topic} than {differential_diagnosis} because of the typical presentation.",
        'topic': topic,
        'differential_topic': differential_diagnosis
    }
    
    return case

def create_medical_case():
    """Create a realistic medical case with patient info and diagnosis."""
    # Define a medical case template
    medical_cases = [
        {
            "patient_info": {
                "age": 62,
                "gender": "Female",
                "demographics": "African American, lives alone, retired teacher"
            },
            "presenting_complaint": "Progressive shortness of breath and fatigue for the past 3 months",
            "history": {
                "medical_history": "Hypertension (well-controlled), Type 2 Diabetes Mellitus, Hyperlipidemia, Chronic Kidney Disease Stage III",
                "medications": "Lisinopril 20mg daily, Metformin 1000mg BID, Atorvastatin 40mg daily, Aspirin 81mg daily",
                "allergies": "Penicillin (rash)"
            },
            "examination": {
                "general": "Looks older than stated age, appears tired",
                "vitals": {
                    "blood_pressure": "135/85 mmHg",
                    "heart_rate": "110 bpm",
                    "respiratory_rate": "24 breaths per minute",
                    "temperature": "37.2°C",
                    "oxygen_saturation": "88% on room air"
                },
                "cardiovascular": "S3 gallop heard, no murmurs, peripheral edema present",
                "pulmonary": "Bibasilar crackles bilaterally, decreased breath sounds at bases",
                "abdomen": "Soft, non-tender, non-distended"
            },
            "vitals": {
                "blood_pressure": "135/85 mmHg",
                "heart_rate": "110 bpm",
                "respiratory_rate": "24 breaths per minute",
                "temperature": "37.2°C",
                "oxygen_saturation": "88% on room air"
            },
            "diagnosis": "Congestive Heart Failure with preserved ejection fraction (HFpEF)",
            "reasoning": "The patient's progressive shortness of breath and fatigue, along with physical examination findings of bibasilar crackles, decreased breath sounds at bases, S3 gallop, and peripheral edema, are consistent with congestive heart failure. Her history of hypertension, diabetes, and chronic kidney disease also increases her risk for developing heart failure.",
            "differential_diagnoses": [
                {
                    "diagnosis": "Chronic Obstructive Pulmonary Disease (COPD)",
                    "reasoning": "The patient's symptoms of shortness of breath and fatigue could be due to COPD. However, the presence of an S3 gallop and peripheral edema, along with the absence of a smoking history, make this less likely."
                },
                {
                    "diagnosis": "Pneumonia",
                    "reasoning": "While pneumonia can cause shortness of breath and fatigue, the patient's bilateral crackles and decreased breath sounds at the bases are more indicative of heart failure than pneumonia."
                },
                {
                    "diagnosis": "Pulmonary Embolism (PE)",
                    "reasoning": "A PE could cause shortness of breath and fatigue, but the patient's bilateral crackles and decreased breath sounds at the bases, along with the absence of pleuritic chest pain or hemoptysis, make this less likely."
                }
            ]
        },
        {
            "patient_info": {
                "age": 45,
                "gender": "Male",
                "demographics": "Caucasian, software engineer, lives with wife and two children"
            },
            "presenting_complaint": "Severe headache, neck stiffness, and fever for the past 24 hours",
            "history": {
                "medical_history": "Generally healthy, occasional migraines",
                "medications": "Sumatriptan as needed for migraines",
                "allergies": "None known"
            },
            "examination": {
                "general": "Appears in distress, photophobic, holding head",
                "vitals": {
                    "blood_pressure": "145/90 mmHg",
                    "heart_rate": "100 bpm",
                    "respiratory_rate": "20 breaths per minute",
                    "temperature": "39.2°C",
                    "oxygen_saturation": "96% on room air"
                },
                "neurological": "Alert but irritable, positive Kernig's and Brudzinski's signs, no focal deficits",
                "head_and_neck": "Neck stiffness present, Unable to touch chin to chest, No papilledema"
            },
            "vitals": {
                "blood_pressure": "145/90 mmHg",
                "heart_rate": "100 bpm",
                "respiratory_rate": "20 breaths per minute",
                "temperature": "39.2°C",
                "oxygen_saturation": "96% on room air"
            },
            "diagnosis": "Bacterial Meningitis",
            "reasoning": "The classic triad of fever, headache, and neck stiffness in combination with positive Kernig's and Brudzinski's signs strongly suggests bacterial meningitis. The acute onset, severity of symptoms, and the patient's irritability are concerning for this life-threatening infection.",
            "differential_diagnoses": [
                {
                    "diagnosis": "Viral Meningitis",
                    "reasoning": "While viral meningitis can present similarly, the severity of symptoms and level of distress suggest bacterial rather than viral etiology."
                },
                {
                    "diagnosis": "Subarachnoid Hemorrhage",
                    "reasoning": "The patient's headache could be due to subarachnoid hemorrhage, but the presence of fever makes an infectious process more likely."
                },
                {
                    "diagnosis": "Migraine with Meningismus",
                    "reasoning": "Although the patient has a history of migraines, the fever and positive meningeal signs are not typical of a migraine attack."
                }
            ]
        },
        {
            "patient_info": {
                "age": 58,
                "gender": "Female",
                "demographics": "Hispanic, restaurant owner, active lifestyle"
            },
            "presenting_complaint": "Right upper quadrant abdominal pain, nausea, and vomiting for 2 days",
            "history": {
                "medical_history": "Hypertension, Hypercholesterolemia, Obesity (BMI 32)",
                "medications": "Amlodipine 5mg daily, Rosuvastatin 10mg daily",
                "allergies": "Sulfa drugs (rash)"
            },
            "examination": {
                "general": "Moderate distress, holding right side",
                "vitals": {
                    "blood_pressure": "140/88 mmHg",
                    "heart_rate": "92 bpm",
                    "respiratory_rate": "18 breaths per minute",
                    "temperature": "38.5°C",
                    "oxygen_saturation": "97% on room air"
                },
                "abdominal": "Tenderness in right upper quadrant, positive Murphy's sign, no rebound tenderness",
                "cardiovascular": "Regular rate and rhythm, no murmurs",
                "respiratory": "Clear bilateral breath sounds"
            },
            "vitals": {
                "blood_pressure": "140/88 mmHg",
                "heart_rate": "92 bpm",
                "respiratory_rate": "18 breaths per minute",
                "temperature": "38.5°C",
                "oxygen_saturation": "97% on room air"
            },
            "diagnosis": "Acute Cholecystitis",
            "reasoning": "The patient's right upper quadrant pain, positive Murphy's sign, and fever are classic findings in acute cholecystitis. Her risk factors include female gender, middle age, and obesity.",
            "differential_diagnoses": [
                {
                    "diagnosis": "Choledocholithiasis",
                    "reasoning": "While this could also present with right upper quadrant pain, the positive Murphy's sign is more specific for gallbladder inflammation."
                },
                {
                    "diagnosis": "Acute Hepatitis",
                    "reasoning": "Hepatitis would likely present with more diffuse liver tenderness rather than localized gallbladder tenderness."
                },
                {
                    "diagnosis": "Peptic Ulcer Disease",
                    "reasoning": "The location of pain and positive Murphy's sign are more consistent with gallbladder pathology than peptic ulcer disease."
                }
            ]
        }
    ]
    
    # Try using Mistral API to enrich the case first
    try:
        messages = [
            {"role": "system", "content": "You are a medical case generator. Generate a realistic medical case with patient info, symptoms, and diagnosis. Keep your response VERY concise."},
            {"role": "user", "content": "Generate a realistic medical case with brief patient info, symptoms, and diagnosis."}
        ]
        
        enriched_case = generate_ai_response(messages, max_tokens=500)
        if enriched_case and len(enriched_case) > 100 and not enriched_case.startswith("Error"):
            # Try to parse and use it if possible
            logger.info("Successfully generated enriched case through AI")
            
            # However, don't rely on it - we've got our fallback ready
            pass
    except Exception as e:
        logger.error(f"Error enriching case: {e}")
    
    # Use a pre-defined case from our list
    import random
    selected_case = random.choice(medical_cases)
    logger.info(f"Selected case with diagnosis: {selected_case['diagnosis']}")
    
    return selected_case

def generate_multiple_choice_questions(diagnosis):
    """Generate multiple choice questions for a specific diagnosis."""
    # Create high-quality multiple choice questions
    multiple_choice_questions = []
    
    # Heart Failure case questions
    if "Heart Failure" in diagnosis:
        multiple_choice_questions = [
            {
                "question": "Which of the following is a risk factor for developing HFpEF?",
                "options": ["Hypertension", "Smoking", "Atrial Fibrillation", "All of the above"],
                "correct_answer": "All of the above"
            },
            {
                "question": "What is the primary mechanism responsible for HFpEF?",
                "options": ["Left ventricular systolic dysfunction", "Left ventricular diastolic dysfunction", "Valvular heart disease", "Coronary artery disease"],
                "correct_answer": "Left ventricular diastolic dysfunction"
            },
            {
                "question": "Which medication class is typically used for symptom management in HFpEF?",
                "options": ["Loop diuretics", "Beta-blockers", "ACE inhibitors", "Calcium channel blockers"],
                "correct_answer": "Loop diuretics"
            },
            {
                "question": "Which diagnostic test is most useful for differentiating HFpEF from HFrEF?",
                "options": ["BNP levels", "Chest X-ray", "Echocardiography", "Electrocardiogram"],
                "correct_answer": "Echocardiography"
            },
            {
                "question": "Which of the following is NOT a classic finding in heart failure?",
                "options": ["S3 gallop", "Peripheral edema", "Bibasilar crackles", "Barrel chest"],
                "correct_answer": "Barrel chest"
            }
        ]
    # Bacterial Meningitis case questions
    elif "Meningitis" in diagnosis:
        multiple_choice_questions = [
            {
                "question": "Which of the following is NOT part of the classic triad of bacterial meningitis?",
                "options": ["Fever", "Headache", "Neck stiffness", "Rash"],
                "correct_answer": "Rash"
            },
            {
                "question": "Which physical examination finding is specific for meningeal irritation?",
                "options": ["Romberg sign", "Kernig's sign", "Babinski sign", "Hoffmann sign"],
                "correct_answer": "Kernig's sign"
            },
            {
                "question": "Which CSF finding is most consistent with bacterial meningitis?",
                "options": ["Decreased glucose", "Increased protein", "Lymphocytic pleocytosis", "Clear appearance"],
                "correct_answer": "Decreased glucose"
            },
            {
                "question": "What is the most appropriate initial antibiotic regimen for suspected bacterial meningitis in adults?",
                "options": ["Vancomycin plus ceftriaxone", "Ampicillin alone", "Azithromycin alone", "Trimethoprim-sulfamethoxazole"],
                "correct_answer": "Vancomycin plus ceftriaxone"
            },
            {
                "question": "Which of the following pathogens is the most common cause of bacterial meningitis in adults?",
                "options": ["Streptococcus pneumoniae", "Neisseria meningitidis", "Listeria monocytogenes", "Haemophilus influenzae"],
                "correct_answer": "Streptococcus pneumoniae"
            }
        ]
    # Cholecystitis case questions
    elif "Cholecystitis" in diagnosis:
        multiple_choice_questions = [
            {
                "question": "Which physical examination finding is characteristic of acute cholecystitis?",
                "options": ["Murphy's sign", "McBurney's point tenderness", "Kehr's sign", "Cullen's sign"],
                "correct_answer": "Murphy's sign"
            },
            {
                "question": "Which imaging modality is considered the gold standard for diagnosing acute cholecystitis?",
                "options": ["Ultrasound", "CT scan", "MRI", "HIDA scan"],
                "correct_answer": "Ultrasound"
            },
            {
                "question": "What is the definitive treatment for recurrent acute cholecystitis?",
                "options": ["Cholecystectomy", "Cholecystostomy", "Ursodeoxycholic acid", "Extracorporeal shock wave lithotripsy"],
                "correct_answer": "Cholecystectomy"
            },
            {
                "question": "Which of the following is NOT a risk factor for gallstone formation?",
                "options": ["Female gender", "Obesity", "Age > 40", "Regular exercise"],
                "correct_answer": "Regular exercise"
            },
            {
                "question": "What is the most common composition of gallstones in Western populations?",
                "options": ["Cholesterol", "Calcium bilirubinate", "Calcium carbonate", "Mixed stones"],
                "correct_answer": "Cholesterol"
            }
        ]
    # Generic questions if diagnosis doesn't match any specific case
    else:
        multiple_choice_questions = [
            {
                "question": f"Which of the following is most likely to cause {diagnosis}?",
                "options": ["Genetic factors", "Environmental factors", "Infectious agents", "Multifactorial causes"],
                "correct_answer": "Multifactorial causes"
            },
            {
                "question": f"Which diagnostic test is most useful for confirming {diagnosis}?",
                "options": ["MRI", "Blood tests", "Biopsy", "Clinical examination"],
                "correct_answer": "Clinical examination"
            },
            {
                "question": f"What is the most common complication of {diagnosis}?",
                "options": ["Organ failure", "Infection", "Pain", "Functional limitation"],
                "correct_answer": "Functional limitation"
            },
            {
                "question": f"Which of the following would NOT be expected in a patient with {diagnosis}?",
                "options": ["Fever", "Pain", "Weight loss", "Skin rash"],
                "correct_answer": "Skin rash"
            },
            {
                "question": f"What is the gold standard treatment for {diagnosis}?",
                "options": ["Medication therapy", "Surgical intervention", "Physical therapy", "Combination approach"],
                "correct_answer": "Combination approach"
            }
        ]
    
    return multiple_choice_questions

def generate_free_text_questions(diagnosis):
    """Generate free text questions for a specific diagnosis."""
    # Create high-quality free text questions
    free_text_questions = []
    
    # Heart Failure case questions
    if "Heart Failure" in diagnosis:
        free_text_questions = [
            {
                "question": "What is the recommended pharmacological treatment for Heart Failure with preserved ejection fraction (HFpEF)?",
                "ideal_answer": "The pharmacological management of HFpEF focuses on symptom control and treatment of comorbidities. Diuretics are first-line for symptom relief of congestion. ACE inhibitors/ARBs and beta-blockers may be used to control hypertension. Aldosterone antagonists can reduce hospitalizations. SGLT2 inhibitors have shown benefit in reducing cardiovascular death and hospitalizations. Rate control is important if atrial fibrillation is present.",
                "key_concepts": ["diuretics", "ACE inhibitors", "ARBs", "beta-blockers", "aldosterone antagonists", "SGLT2 inhibitors", "symptom control", "comorbidities"]
            },
            {
                "question": "What are the key differences between HFpEF and HFrEF in terms of pathophysiology?",
                "ideal_answer": "HFpEF (preserved ejection fraction) is characterized by diastolic dysfunction with normal or preserved systolic function (EF ≥50%), ventricular stiffness, impaired relaxation, and concentric remodeling. HFrEF (reduced ejection fraction) is primarily characterized by systolic dysfunction (EF <40%), impaired contractility, and eccentric remodeling. HFpEF is more commonly associated with hypertension, obesity, and metabolic syndrome.",
                "key_concepts": ["diastolic dysfunction", "systolic function", "ventricular stiffness", "impaired relaxation", "concentric remodeling", "ejection fraction", "hypertension"]
            },
            {
                "question": "Explain the S3 gallop heard in heart failure and its clinical significance.",
                "ideal_answer": "An S3 gallop is an early diastolic filling sound caused by rapid ventricular filling of a non-compliant or volume-overloaded ventricle. It occurs during the rapid filling phase of diastole. In heart failure, it indicates volume overload and is associated with elevated ventricular filling pressures. It has high specificity for heart failure and correlates with disease severity, suggesting active ventricular decompensation that requires prompt treatment.",
                "key_concepts": ["diastolic", "ventricular filling", "non-compliant ventricle", "volume overload", "specificity", "severity", "decompensation"]
            },
            {
                "question": "What are the primary goals of managing a patient with heart failure?",
                "ideal_answer": "The primary goals are to improve symptoms (reduce dyspnea, fatigue, and edema), slow disease progression, reduce hospitalizations, and improve survival. This is achieved through lifestyle modifications (sodium/fluid restriction, exercise), optimal pharmacotherapy, treatment of underlying causes and comorbidities, patient education, and regular monitoring. The focus is on improving quality of life while reducing morbidity and mortality.",
                "key_concepts": ["improve symptoms", "slow progression", "reduce hospitalizations", "improve survival", "lifestyle modifications", "pharmacotherapy", "quality of life"]
            },
            {
                "question": "How would you educate this patient about self-monitoring for heart failure exacerbation?",
                "ideal_answer": "Educate the patient to monitor daily weight (same time/clothing), watch for increased shortness of breath (especially when lying flat), swelling in ankles/legs, increased fatigue, decreased exercise tolerance, and persistent cough. Teach them to track fluid/sodium intake and follow a sodium-restricted diet. They should report weight gain >2kg in 3 days, increased swelling, worsening breathlessness, or decreased activity tolerance. Provide clear instructions on when to contact healthcare providers versus seek emergency care.",
                "key_concepts": ["daily weight", "shortness of breath", "edema", "fatigue", "fluid intake", "sodium restriction", "when to seek help"]
            }
        ]
    # Bacterial Meningitis case questions
    elif "Meningitis" in diagnosis:
        free_text_questions = [
            {
                "question": "What is the recommended pharmacological treatment for Bacterial Meningitis in adults?",
                "ideal_answer": "Initial empiric therapy should include Vancomycin plus a third-generation cephalosporin (Ceftriaxone or Cefotaxime). If Listeria is suspected (elderly, immunocompromised), add Ampicillin. Therapy should be initiated immediately after obtaining CSF cultures, without waiting for results. Once the causative organism is identified, therapy can be narrowed based on susceptibilities. Typical duration is 7-14 days depending on the pathogen. Dexamethasone may be given before or with first antibiotic dose to reduce neurological sequelae.",
                "key_concepts": ["vancomycin", "third-generation cephalosporin", "ceftriaxone", "empiric therapy", "immediate initiation", "pathogen-specific", "dexamethasone"]
            },
            {
                "question": "Describe the typical cerebrospinal fluid (CSF) findings in bacterial meningitis and how they differ from viral meningitis.",
                "ideal_answer": "In bacterial meningitis, CSF typically shows neutrophilic pleocytosis (1,000-5,000 WBCs/mm³, predominantly PMNs), elevated protein (>100 mg/dL), decreased glucose (<40 mg/dL or CSF:serum ratio <0.4), and positive Gram stain/culture. In contrast, viral meningitis shows moderate lymphocytic pleocytosis (50-500 WBCs/mm³), mildly elevated protein (50-100 mg/dL), normal glucose, and negative Gram stain. Bacterial CSF is often cloudy, while viral CSF appears clear.",
                "key_concepts": ["neutrophilic pleocytosis", "elevated protein", "decreased glucose", "positive Gram stain", "lymphocytic pleocytosis", "normal glucose", "CSF appearance"]
            },
            {
                "question": "What are the potential long-term sequelae of bacterial meningitis, and which factors affect prognosis?",
                "ideal_answer": "Long-term sequelae include hearing loss (most common), cognitive impairment, seizures, motor deficits, hydrocephalus, and cranial nerve palsies. Factors affecting prognosis include pathogen type (pneumococcal has worse outcomes), patient age (extremes of age have poorer prognosis), time to treatment initiation (delays worsen outcomes), severity at presentation (altered consciousness, seizures), comorbidities, and immunocompromised status. Early adjunctive dexamethasone may reduce complications, especially hearing loss in pneumococcal meningitis.",
                "key_concepts": ["hearing loss", "cognitive impairment", "seizures", "pathogen type", "time to treatment", "consciousness level", "dexamethasone"]
            },
            {
                "question": "When should lumbar puncture be deferred in a patient with suspected meningitis, and what is the management approach in such cases?",
                "ideal_answer": "Lumbar puncture should be deferred with signs of increased intracranial pressure or focal neurologic deficits, papilledema, immunocompromised state, recent seizure, coagulopathy, or local infection at the puncture site. Management approach: obtain blood cultures, start empiric antibiotics immediately (without delay), perform neuroimaging (CT/MRI) first, and proceed with LP if neuroimaging doesn't show contraindications. If LP must be significantly delayed, empiric antibiotics should never be withheld.",
                "key_concepts": ["increased ICP", "focal deficits", "papilledema", "blood cultures", "immediate antibiotics", "neuroimaging", "don't delay treatment"]
            },
            {
                "question": "Discuss the importance of chemoprophylaxis for close contacts of a patient with bacterial meningitis.",
                "ideal_answer": "Chemoprophylaxis is critical for close contacts of patients with meningococcal meningitis and Haemophilus influenzae type b. Close contacts include household members, daycare contacts, and those with direct exposure to oral secretions. For meningococcal cases, rifampin, ciprofloxacin, or ceftriaxone are recommended within 24 hours of case identification. The goal is to eradicate nasopharyngeal carriage and prevent secondary cases. Healthcare workers need prophylaxis only if directly exposed to respiratory secretions. Vaccination may also be recommended for meningococcal contacts during outbreaks.",
                "key_concepts": ["close contacts", "nasopharyngeal carriage", "meningococcal", "rifampin", "ciprofloxacin", "timing", "secondary cases"]
            }
        ]
    # Cholecystitis case questions
    elif "Cholecystitis" in diagnosis:
        free_text_questions = [
            {
                "question": "What is the recommended pharmacological and surgical management for Acute Cholecystitis?",
                "ideal_answer": "Initial pharmacological management includes NPO status, IV fluids, pain control (NSAIDs or opioids), and broad-spectrum antibiotics covering enteric gram-negative organisms and anaerobes (e.g., Piperacillin-tazobactam or Ceftriaxone plus Metronidazole). Definitive treatment is cholecystectomy, preferably laparoscopic, which should be performed within 24-72 hours of symptom onset for uncomplicated cases. For high-risk surgical patients, percutaneous cholecystostomy may be considered as a temporizing measure.",
                "key_concepts": ["NPO", "IV fluids", "pain control", "antibiotics", "laparoscopic cholecystectomy", "early surgery", "cholecystostomy"]
            },
            {
                "question": "Describe the pathophysiology of acute cholecystitis and how it differs from biliary colic.",
                "ideal_answer": "Acute cholecystitis typically begins with cystic duct obstruction by gallstones (calculous cholecystitis) leading to gallbladder distension, increased intraluminal pressure, and ischemia. Chemical inflammation from concentrated bile salts follows, and secondary bacterial infection can occur. This creates a persistent inflammatory state with gallbladder wall edema and potential gangrene or perforation. Biliary colic, in contrast, involves temporary gallstone obstruction without inflammation, causing intermittent pain that resolves when the stone dislodges. Unlike cholecystitis, biliary colic lacks inflammatory markers, fever, or signs of gallbladder inflammation on imaging.",
                "key_concepts": ["cystic duct obstruction", "gallbladder distension", "ischemia", "inflammation", "bacterial infection", "temporary vs. persistent", "inflammatory markers"]
            },
            {
                "question": "What are the risk factors for developing gallstones and acute cholecystitis?",
                "ideal_answer": "Risk factors for gallstones include: Female gender (especially multiparous), age >40, obesity, rapid weight loss, high-fat/low-fiber diet, certain medications (estrogens, OCPs), genetic factors, ethnicity (Native American, Hispanic), and certain medical conditions (diabetes, Crohn's disease, cirrhosis, sickle cell disease). Cholesterol stones are associated with the 4F's: Female, Forty, Fertile, and Fat. Risk factors specifically for acute cholecystitis include existing gallstones, prolonged fasting, TPN, and critical illness. Acalculous cholecystitis is associated with severe illness, trauma, burns, and prolonged ICU stays.",
                "key_concepts": ["female gender", "obesity", "rapid weight loss", "4F's", "ethnicity", "diabetes", "fasting", "TPN"]
            },
            {
                "question": "Explain how to differentiate acute cholecystitis from other causes of right upper quadrant pain in this patient.",
                "ideal_answer": "Key distinguishing features of acute cholecystitis include: RUQ pain with radiation to right shoulder, positive Murphy's sign, fever, leukocytosis, and ultrasound findings (gallbladder wall thickening, pericholecystic fluid, gallstones). Acute hepatitis presents with jaundice, markedly elevated transaminases, and diffuse liver tenderness. Peptic ulcer disease typically causes epigastric pain relieved by food or antacids. Appendicitis pain migrates to RLQ with McBurney's point tenderness. Pneumonia may cause pleuritic right-sided chest pain with abnormal lung sounds. GERD typically causes burning retrosternal pain. Pancreatitis causes epigastric pain radiating to the back with elevated lipase/amylase.",
                "key_concepts": ["Murphy's sign", "radiation pattern", "fever", "ultrasound findings", "transaminases", "pain migration", "lipase"]
            },
            {
                "question": "What complications can arise from untreated acute cholecystitis and how would you monitor for them?",
                "ideal_answer": "Complications include: Gangrenous cholecystitis, gallbladder perforation, pericholecystic abscess, empyema, cholecystoenteric fistula, gallstone ileus, sepsis, and rarely, emphysematous cholecystitis. Monitoring should include vital signs (tachycardia, hypotension indicate sepsis), escalating pain or changing pain pattern, increasing WBC count, worsening liver function tests, serial physical exams for peritoneal signs, and follow-up imaging to assess for fluid collections or emphysematous changes. Signs of deterioration should prompt urgent surgical intervention. Patients require monitoring for 24-48 hours after initiating treatment to ensure improvement.",
                "key_concepts": ["gangrene", "perforation", "abscess", "fistula", "sepsis", "vital signs", "peritoneal signs", "urgent surgery"]
            }
        ]
    # Generic questions if diagnosis doesn't match any specific case
    else:
        free_text_questions = [
            {
                "question": f"What is the recommended pharmacological treatment for {diagnosis}?",
                "ideal_answer": f"The pharmacological treatment for {diagnosis} typically involves medication to address both symptoms and underlying causes. First-line agents include appropriate medications based on clinical guidelines, with dosing adjusted for patient factors like age, weight, and renal function. Duration depends on clinical response and side effect monitoring is essential.",
                "key_concepts": ["first-line medications", "symptom management", "underlying cause", "dosing", "duration", "side effects", "guidelines"]
            },
            {
                "question": f"Explain the pathophysiology of {diagnosis}.",
                "ideal_answer": f"The pathophysiology of {diagnosis} involves multiple mechanisms including genetic factors, environmental influences, and cellular changes. This leads to functional and structural alterations resulting in the clinical manifestations observed. Disease progression can be influenced by various factors including treatment adherence.",
                "key_concepts": ["genetic factors", "environmental factors", "cellular changes", "structural alterations", "clinical manifestations", "disease progression"]
            },
            {
                "question": f"What are the diagnostic criteria for {diagnosis}?",
                "ideal_answer": f"Diagnosing {diagnosis} requires a combination of clinical findings, laboratory tests, and imaging studies. Key diagnostic criteria include specific symptoms, physical examination findings, and objective test results. Differential diagnosis must rule out similar conditions through systematic evaluation.",
                "key_concepts": ["clinical findings", "laboratory tests", "imaging", "specific symptoms", "physical examination", "differential diagnosis"]
            },
            {
                "question": f"How would you educate a patient newly diagnosed with {diagnosis}?",
                "ideal_answer": f"Patient education for {diagnosis} should cover disease overview, treatment options, medication adherence, lifestyle modifications, symptom monitoring, and when to seek medical attention. Use plain language with visual aids when possible, verify understanding through teach-back, and provide written materials for reference. Set realistic expectations and address psychological aspects of chronic disease management.",
                "key_concepts": ["disease overview", "treatment", "adherence", "lifestyle modifications", "symptom monitoring", "when to seek help", "psychological support"]
            },
            {
                "question": f"What complications can develop from {diagnosis} and how can they be prevented?",
                "ideal_answer": f"Complications of {diagnosis} include acute exacerbations, organ damage, and functional limitations. Prevention strategies focus on optimal disease control through medication adherence, regular monitoring, lifestyle modifications, and addressing risk factors. Early intervention for warning signs can prevent progression to severe complications.",
                "key_concepts": ["acute exacerbations", "organ damage", "functional limitations", "medication adherence", "regular monitoring", "lifestyle modifications", "early intervention"]
            }
        ]
    
    return free_text_questions

def generate_daily_challenge():
    """Generate a daily diagnostic challenge."""
    messages = [
        {"role": "system", "content": """Create a short (3-5 minute) medical diagnostic challenge.
        The challenge should test knowledge of common medical conditions and diagnostic reasoning.
        Structure your response in JSON format with the following fields:
        - title: a catchy title for the challenge
        - scenario: a brief description of the patient and their symptoms
        - questions: an array of exactly 3 multiple-choice questions with the following structure:
          * question: the question text
          * options: an array of exactly 4 string answer options (not objects)
          * correct_answer: the correct answer string that matches one of the options exactly
        - explanation: a detailed explanation of the correct diagnosis and reasoning
        
        IMPORTANT: Make sure options are simple strings, not objects or arrays. 
        Example of a properly formatted question:
        {
          "question": "What is the most likely diagnosis?",
          "options": ["Pneumonia", "Pulmonary Embolism", "Heart Failure", "COPD"],
          "correct_answer": "Pneumonia"
        }
        """},
        {"role": "user", "content": "Create a short daily diagnostic challenge for medical professionals."}
    ]
    
    response = generate_ai_response(messages)
    
    # Check if the response is a string but not JSON (likely an error message from generate_ai_response)
    if isinstance(response, str) and (response.startswith("Error") or response.startswith("AI service")):
        logger.error(f"AI service returned an error: {response}")
        # Return the first fallback challenge instead of None
        return create_fallback_challenge(1)
    
    try:
        # Extract JSON from response if wrapped in text
        if '```json' in response and '```' in response:
            json_str = response.split('```json')[1].split('```')[0].strip()
            challenge_data = json.loads(json_str)
        else:
            try:
                challenge_data = json.loads(response)
            except json.JSONDecodeError:
                # Last attempt: Try to find any JSON-like structure in the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        challenge_data = json.loads(json_match.group(0))
                    except:
                        logger.error("Failed to extract JSON from response after multiple attempts")
                        # Return fallback challenge instead of None
                        return create_fallback_challenge(1)
                else:
                    logger.error("No JSON structure found in response")
                    # Return fallback challenge instead of None
                    return create_fallback_challenge(1)
        
        # Ensure all required fields exist
        required_fields = ['title', 'scenario', 'questions', 'explanation']
        for field in required_fields:
            if field not in challenge_data:
                challenge_data[field] = 'Missing' if field != 'questions' else []
        
        # Validate and fix any potential issues with the challenge data
        if 'questions' in challenge_data:
            valid_questions = []
            for question in challenge_data['questions']:
                # Skip invalid questions
                if not isinstance(question, dict):
                    continue
                    
                # Ensure required fields exist
                if 'question' not in question:
                    question['question'] = 'Missing question text'
                
                # Ensure options are strings and there are exactly 4
                if 'options' not in question or not isinstance(question['options'], list):
                    question['options'] = ['Option A', 'Option B', 'Option C', 'Option D']
                else:
                    # Convert all options to strings
                    question['options'] = [str(option) for option in question['options']]
                    
                    # Ensure we have exactly 4 options
                    while len(question['options']) < 4:
                        question['options'].append(f'Option {len(question["options"]) + 1}')
                    if len(question['options']) > 4:
                        question['options'] = question['options'][:4]
                
                # Ensure correct_answer is a string and matches one of the options
                if 'correct_answer' not in question or not isinstance(question['correct_answer'], str):
                    question['correct_answer'] = question['options'][0]
                else:
                    question['correct_answer'] = str(question['correct_answer'])
                    # Make sure correct_answer matches one of the options
                    if question['correct_answer'] not in question['options']:
                        question['correct_answer'] = question['options'][0]
                
                valid_questions.append(question)
            
            # Ensure we have at least 3 questions
            challenge_data['questions'] = valid_questions
            while len(challenge_data['questions']) < 3:
                # Add a generic question if needed
                challenge_data['questions'].append({
                    'question': f'Sample question {len(challenge_data["questions"]) + 1}',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': 'Option A'
                })
        
        return challenge_data
    except Exception as e:
        logger.error(f"Failed to process challenge response: {str(e)}")
        logger.error(f"Response was: {response}")
        # Return fallback challenge instead of None
        return create_fallback_challenge(1)
        
def generate_multiple_daily_challenges(count=3):
    """Generate multiple daily diagnostic challenges."""
    logger.info(f"Generating {count} daily challenges")
    challenges = []
    max_retries = 2  # Maximum number of retries per challenge
    
    # First attempt: Generate challenges one by one
    for i in range(count):
        logger.info(f"Generating challenge {i+1}/{count}")
        
        # Try to generate each challenge with retries
        for retry in range(max_retries):
            try:
                challenge = generate_daily_challenge()
                # Check if challenge is a valid dictionary with required fields
                if challenge and isinstance(challenge, dict) and 'title' in challenge:
                    challenges.append(challenge)
                    logger.info(f"Successfully generated challenge {i+1}: {challenge.get('title')}")
                    break
                # Check if challenge is a string (error message from the AI service)
                elif challenge and isinstance(challenge, str):
                    logger.warning(f"Challenge {i+1} attempt {retry+1} received error message: {challenge}")
                    if retry == max_retries - 1:  # If this was the last retry
                        # Create fallback challenge with generic content
                        fallback_challenge = create_fallback_challenge(i+1)
                        challenges.append(fallback_challenge)
                        logger.warning(f"Added fallback challenge for position {i+1}")
                else:
                    logger.warning(f"Challenge {i+1} attempt {retry+1} failed to generate valid challenge data")
                    if retry == max_retries - 1:  # If this was the last retry
                        # Create fallback challenge with generic content
                        fallback_challenge = create_fallback_challenge(i+1)
                        challenges.append(fallback_challenge)
                        logger.warning(f"Added fallback challenge for position {i+1}")
            except Exception as e:
                logger.error(f"Error generating challenge {i+1} (attempt {retry+1}): {str(e)}")
                if retry == max_retries - 1:  # If this was the last retry
                    # Create fallback challenge
                    fallback_challenge = create_fallback_challenge(i+1)
                    challenges.append(fallback_challenge)
                    logger.warning(f"Added fallback challenge for position {i+1} after error")
    
    # If we couldn't generate enough challenges, try with a combined approach
    if len(challenges) < count:
        logger.warning(f"Only generated {len(challenges)}/{count} challenges. Trying combined approach.")
        
        # Generate multiple challenges in a single request
        messages = [
            {"role": "system", "content": f"""Create {count - len(challenges)} different short medical diagnostic challenges.
            Each challenge should test knowledge of common medical conditions and diagnostic reasoning.
            Structure your response as a JSON array, with each element having the following fields:
            - title: a catchy title for the challenge
            - scenario: a brief description of the patient and their symptoms
            - questions: an array of exactly 3 multiple-choice questions with the following structure:
              * question: the question text
              * options: an array of exactly 4 string answer options (not objects)
              * correct_answer: the correct answer string that matches one of the options exactly
            - explanation: a detailed explanation of the correct diagnosis and reasoning
            
            IMPORTANT: Return an array of {count - len(challenges)} complete challenge objects.
            """},
            {"role": "user", "content": f"Create {count - len(challenges)} different daily diagnostic challenges."}
        ]
        
        response = generate_ai_response(messages)
        
        if response:
            try:
                # Extract JSON array from response
                if '```json' in response and '```' in response:
                    json_str = response.split('```json')[1].split('```')[0].strip()
                    new_challenges = json.loads(json_str)
                else:
                    try:
                        new_challenges = json.loads(response)
                    except json.JSONDecodeError:
                        # Try to find array-like structure
                        import re
                        json_match = re.search(r'\[.*\]', response, re.DOTALL)
                        if json_match:
                            new_challenges = json.loads(json_match.group(0))
                        else:
                            new_challenges = []
                
                # Process each challenge
                if isinstance(new_challenges, list):
                    for challenge in new_challenges:
                        # Basic validation
                        if not isinstance(challenge, dict):
                            continue
                            
                        # Add required fields if missing
                        required_fields = ['title', 'scenario', 'questions', 'explanation']
                        for field in required_fields:
                            if field not in challenge:
                                challenge[field] = 'Missing' if field != 'questions' else []
                        
                        # Fix questions
                        valid_questions = []
                        for question in challenge.get('questions', []):
                            if not isinstance(question, dict):
                                continue
                                
                            # Add required fields
                            if 'question' not in question:
                                question['question'] = 'Missing question text'
                            
                            # Fix options
                            if 'options' not in question or not isinstance(question['options'], list):
                                question['options'] = ['Option A', 'Option B', 'Option C', 'Option D']
                            else:
                                question['options'] = [str(option) for option in question['options']]
                                while len(question['options']) < 4:
                                    question['options'].append(f'Option {len(question["options"]) + 1}')
                                if len(question['options']) > 4:
                                    question['options'] = question['options'][:4]
                            
                            # Fix correct answer
                            if 'correct_answer' not in question or not isinstance(question['correct_answer'], str):
                                question['correct_answer'] = question['options'][0]
                            else:
                                question['correct_answer'] = str(question['correct_answer'])
                                if question['correct_answer'] not in question['options']:
                                    question['correct_answer'] = question['options'][0]
                            
                            valid_questions.append(question)
                        
                        challenge['questions'] = valid_questions
                        
                        # Add to our list if it has valid questions
                        if valid_questions:
                            challenges.append(challenge)
                            if len(challenges) >= count:
                                break
            except Exception as e:
                logger.error(f"Failed to parse combined challenges: {e}")
    
    logger.info(f"Successfully generated {len(challenges)} challenges")
    return challenges[:count]  # Return only the requested number of challenges

def generate_flashcards(topic):
    """Generate flashcards for a specific medical topic."""
    # First try to generate flashcards using the AI
    try:
        messages = [
            {"role": "system", "content": f"""Create a set of 5 flashcards for studying {topic} in medicine.
            Each flashcard should have a question on one side and a concise, clear answer on the other.
            Structure your response in JSON format with an array of flashcards, each containing:
            - question: the front side of the flashcard
            - answer: the back side with the correct information
            - difficulty: a rating from 1-3 (1=easy, 2=medium, 3=hard)
            """},
            {"role": "user", "content": f"Generate 5 medical flashcards about {topic}."}
        ]
        
        response = generate_ai_response(messages)
        
        # Try to parse the JSON response
        if '```json' in response and '```' in response:
            json_str = response.split('```json')[1].split('```')[0].strip()
            flashcard_data = json.loads(json_str)
            return {'flashcards': flashcard_data}
        else:
            try:
                parsed_data = json.loads(response)
                if isinstance(parsed_data, list) and len(parsed_data) > 0:
                    return {'flashcards': parsed_data}
            except json.JSONDecodeError:
                pass  # Will fallback to predefined cards
    
    except Exception as e:
        logger.error(f"Error generating flashcards with AI: {str(e)}")
    
    # If AI generation fails, use fallback predefined flashcards based on topic
    return get_fallback_flashcards(topic)

def get_fallback_flashcards(topic):
    """Get fallback flashcards for a specific topic when AI generation fails."""
    topic_lower = topic.lower()
    
    # Predefined flashcards for common medical topics
    flashcard_sets = {
        'hypertension': [
            {
                "question": "What is the definition of hypertension?",
                "answer": "Hypertension is defined as a systolic blood pressure (SBP) of 140 mmHg or higher and/or a diastolic blood pressure (DBP) of 90 mmHg or higher.",
                "difficulty": 1
            },
            {
                "question": "What are the two main categories of hypertension?",
                "answer": "The two main categories of hypertension are primary (essential) hypertension and secondary hypertension.",
                "difficulty": 1
            },
            {
                "question": "What percentage of hypertension cases are considered primary (essential)?",
                "answer": "Approximately 90-95% of hypertension cases are considered primary (essential) hypertension, meaning there is no identifiable cause.",
                "difficulty": 2
            },
            {
                "question": "List three common risk factors for hypertension.",
                "answer": "Three common risk factors for hypertension are obesity, physical inactivity, and a high sodium diet.",
                "difficulty": 2
            },
            {
                "question": "Which class of drugs is often used as a first-line treatment for hypertension?",
                "answer": "Thiazide diuretics are often used as a first-line treatment for hypertension.",
                "difficulty": 3
            }
        ],
        
        'diabetes': [
            {
                "question": "What are the main types of diabetes mellitus?",
                "answer": "The main types are Type 1 (autoimmune destruction of beta cells), Type 2 (insulin resistance and relative insulin deficiency), and Gestational diabetes (during pregnancy).",
                "difficulty": 1
            },
            {
                "question": "What is the diagnostic threshold for fasting plasma glucose in diabetes?",
                "answer": "A fasting plasma glucose ≥126 mg/dL (7.0 mmol/L) on two separate occasions is diagnostic for diabetes mellitus.",
                "difficulty": 2
            },
            {
                "question": "What are the classic symptoms of diabetes?",
                "answer": "The classic symptoms are polyuria (frequent urination), polydipsia (increased thirst), polyphagia (increased hunger), and unexplained weight loss.",
                "difficulty": 1
            },
            {
                "question": "What is the role of HbA1c in diabetes management?",
                "answer": "HbA1c (glycated hemoglobin) reflects average blood glucose over the previous 2-3 months, used for diagnosis (≥6.5%) and monitoring treatment effectiveness.",
                "difficulty": 2
            },
            {
                "question": "What are the major microvascular complications of diabetes?",
                "answer": "The major microvascular complications are diabetic nephropathy (kidney damage), retinopathy (eye damage), and neuropathy (nerve damage).",
                "difficulty": 3
            }
        ],
        
        'malaria': [
            {
                "question": "What causes malaria?",
                "answer": "Malaria is caused by Plasmodium parasites, primarily P. falciparum, P. vivax, P. ovale, P. malariae, and P. knowlesi, transmitted to humans through the bite of infected female Anopheles mosquitoes.",
                "difficulty": 1
            },
            {
                "question": "What is the classic symptom pattern of malaria?",
                "answer": "The classic symptom pattern is paroxysms of fever, chills, and sweating occurring at regular intervals (24-72 hours depending on species), though not all patients show this pattern.",
                "difficulty": 2
            },
            {
                "question": "Which Plasmodium species causes the most severe form of malaria?",
                "answer": "Plasmodium falciparum causes the most severe form of malaria with the highest mortality rate due to its ability to cause high parasitemia and cytoadherence leading to microvascular obstruction.",
                "difficulty": 1
            },
            {
                "question": "What is the gold standard for malaria diagnosis?",
                "answer": "Microscopic examination of Giemsa-stained thick and thin blood smears remains the gold standard for diagnosis, allowing species identification and parasite quantification.",
                "difficulty": 2
            },
            {
                "question": "What are the main components of antimalarial chemoprophylaxis?",
                "answer": "Antimalarial chemoprophylaxis includes: risk assessment, appropriate drug selection based on resistance patterns, correct dosing, starting before travel, continuing during exposure, and maintaining after leaving endemic areas.",
                "difficulty": 3
            }
        ],
        
        'asthma': [
            {
                "question": "What is the pathophysiologic hallmark of asthma?",
                "answer": "The pathophysiologic hallmark of asthma is chronic airway inflammation with bronchial hyperresponsiveness leading to recurrent episodes of wheezing, breathlessness, chest tightness, and coughing.",
                "difficulty": 1
            },
            {
                "question": "What are the two main categories of asthma medications?",
                "answer": "The two main categories are controllers (maintenance medications like inhaled corticosteroids) and relievers (rescue medications like short-acting beta-agonists).",
                "difficulty": 1
            },
            {
                "question": "How is the severity of asthma classified?",
                "answer": "Asthma severity is classified as intermittent, mild persistent, moderate persistent, or severe persistent based on frequency of symptoms, nighttime awakenings, rescue inhaler use, and interference with normal activity.",
                "difficulty": 2
            },
            {
                "question": "What is the role of spirometry in asthma diagnosis?",
                "answer": "Spirometry demonstrates airflow obstruction (reduced FEV1 and FEV1/FVC ratio) and documents reversibility with bronchodilators (improvement in FEV1 by ≥12% and ≥200ml), supporting an asthma diagnosis.",
                "difficulty": 2
            },
            {
                "question": "What are the key components of an asthma action plan?",
                "answer": "An asthma action plan includes: recognizing worsening symptoms, adjusting medications based on symptoms/peak flow measurements, identifying when to seek medical help, and guidance for managing exacerbations.",
                "difficulty": 3
            }
        ]
    }
    
    # Check if we have predefined flashcards for the requested topic
    for key, cards in flashcard_sets.items():
        if key in topic_lower or topic_lower in key:
            logger.info(f"Using fallback flashcards for {topic}")
            return {'flashcards': cards}
    
    # Generic medical flashcards for topics we don't have predefined
    generic_cards = [
        {
            "question": f"What is the definition of {topic}?",
            "answer": f"{topic} is a medical condition or concept that involves specific biological mechanisms and clinical presentations.",
            "difficulty": 1
        },
        {
            "question": f"What are the common signs and symptoms of {topic}?",
            "answer": f"Common signs and symptoms of {topic} include relevant clinical presentations that help in diagnosis.",
            "difficulty": 1
        },
        {
            "question": f"How is {topic} diagnosed?",
            "answer": f"Diagnosis of {topic} typically involves clinical evaluation, relevant laboratory tests, and sometimes imaging studies.",
            "difficulty": 2
        },
        {
            "question": f"What are the main treatment approaches for {topic}?",
            "answer": f"Treatment of {topic} may include medications, lifestyle modifications, and other therapeutic interventions based on current clinical guidelines.",
            "difficulty": 2
        },
        {
            "question": f"What are important considerations for patient education regarding {topic}?",
            "answer": f"Patient education for {topic} should cover understanding the condition, medication adherence, monitoring symptoms, and when to seek medical attention.",
            "difficulty": 3
        }
    ]
    
    logger.info(f"Using generic flashcards for {topic}")
    return {'flashcards': generic_cards}

def create_fallback_challenge(position):
    """Create a fallback challenge when API fails.
    
    This function creates realistic medical diagnostic challenges
    that can be used when the AI service fails to generate content.
    
    Args:
        position: Integer indicating the challenge position (1, 2, or 3)
        
    Returns:
        A fully-formed challenge dictionary ready for use
    """
    logger.info(f"Creating fallback challenge for position {position}")
    
    # Define set of realistic medical challenges
    fallback_challenges = [
        # Challenge 1: Respiratory Case
        {
            "title": "Respiratory Case Challenge",
            "scenario": "A 68-year-old male with a history of COPD presents with worsening shortness of breath over the past 3 days, productive cough with yellowish sputum, and low-grade fever. Physical examination reveals diffuse wheezing and crackles at the right lung base. Oxygen saturation is 92% on room air.",
            "questions": [
                {
                    "question": "What is the most likely diagnosis?",
                    "options": [
                        "COPD exacerbation",
                        "Community-acquired pneumonia",
                        "Pulmonary embolism",
                        "Congestive heart failure"
                    ],
                    "correct_answer": "COPD exacerbation"
                },
                {
                    "question": "What is the most appropriate initial management?",
                    "options": [
                        "Bronchodilators and systemic corticosteroids",
                        "Antibiotics only",
                        "Mechanical ventilation",
                        "Diuretics and oxygen"
                    ],
                    "correct_answer": "Bronchodilators and systemic corticosteroids"
                },
                {
                    "question": "Which finding is most consistent with a COPD exacerbation?",
                    "options": [
                        "Diffuse wheezing",
                        "Focal consolidation on chest X-ray",
                        "Elevated D-dimer",
                        "S3 heart sound"
                    ],
                    "correct_answer": "Diffuse wheezing"
                }
            ],
            "explanation": "This patient is experiencing a COPD exacerbation, likely triggered by a respiratory infection. Key features include worsening dyspnea, increased sputum production, and signs of airflow obstruction. First-line treatment includes bronchodilators and systemic corticosteroids to reduce inflammation and improve airflow. Antibiotics may be indicated if bacterial infection is suspected."
        },
        
        # Challenge 2: Cardiac Case
        {
            "title": "Acute Cardiac Case",
            "scenario": "A 56-year-old woman presents to the emergency department with sudden onset of crushing chest pain radiating to her left arm and jaw, which started 2 hours ago. She is diaphoretic and nauseated. Her medical history includes hypertension and hyperlipidemia. ECG shows ST-segment elevation in leads V1-V4.",
            "questions": [
                {
                    "question": "What is the most likely diagnosis?",
                    "options": [
                        "Acute anterior STEMI",
                        "Stable angina",
                        "Pericarditis",
                        "Aortic dissection"
                    ],
                    "correct_answer": "Acute anterior STEMI"
                },
                {
                    "question": "What is the most appropriate immediate management?",
                    "options": [
                        "Immediate cardiac catheterization",
                        "Thrombolytic therapy",
                        "CT angiography",
                        "Echocardiogram"
                    ],
                    "correct_answer": "Immediate cardiac catheterization"
                },
                {
                    "question": "Which medication should NOT be given to this patient?",
                    "options": [
                        "Beta blockers if in cardiogenic shock",
                        "Aspirin",
                        "Nitroglycerin",
                        "Heparin"
                    ],
                    "correct_answer": "Beta blockers if in cardiogenic shock"
                }
            ],
            "explanation": "This patient is presenting with an acute anterior ST-elevation myocardial infarction (STEMI). The diagnosis is based on the characteristic chest pain and ECG findings showing ST-segment elevation in the anterior leads. Immediate reperfusion therapy with primary PCI is the standard of care when available within 90 minutes. Beta-blockers are beneficial in most cases but contraindicated in cardiogenic shock."
        },
        
        # Challenge 3: Neurological Case
        {
            "title": "Neurological Emergency",
            "scenario": "A 72-year-old right-handed man is brought to the emergency department by his wife after she noticed that his speech was slurred and he couldn't raise his left arm when he woke up 45 minutes ago. He has a history of atrial fibrillation and is on warfarin. Blood pressure is 172/94 mmHg.",
            "questions": [
                {
                    "question": "What is the most likely diagnosis?",
                    "options": [
                        "Acute ischemic stroke",
                        "Hemorrhagic stroke",
                        "Todd's paralysis",
                        "Conversion disorder"
                    ],
                    "correct_answer": "Acute ischemic stroke"
                },
                {
                    "question": "What is the next most appropriate step?",
                    "options": [
                        "Urgent non-contrast head CT",
                        "Immediate administration of tPA",
                        "MRI brain with contrast",
                        "Carotid ultrasound"
                    ],
                    "correct_answer": "Urgent non-contrast head CT"
                },
                {
                    "question": "Which factor would be a contraindication for thrombolytic therapy?",
                    "options": [
                        "INR greater than 1.7",
                        "Symptom onset within 3 hours",
                        "Age 72 years",
                        "History of atrial fibrillation"
                    ],
                    "correct_answer": "INR greater than 1.7"
                }
            ],
            "explanation": "This patient is presenting with an acute ischemic stroke in the right middle cerebral artery territory. The sudden onset of left-sided weakness and slurred speech in a patient with atrial fibrillation strongly suggests a cardioembolic stroke. Urgent CT is necessary to rule out hemorrhage before considering thrombolytic therapy. The patient's use of warfarin and INR status are critical factors in determining eligibility for thrombolysis."
        }
    ]
    
    # Return the challenge corresponding to the position (modulo to handle any position)
    index = (position - 1) % len(fallback_challenges)
    return fallback_challenges[index]

def evaluate_diagnosis(user_diagnosis, correct_diagnosis):
    """Evaluate a user's diagnosis against the correct diagnosis."""
    messages = [
        {"role": "system", "content": """You are a medical education expert evaluating a diagnosis.
        Compare the user's diagnosis to the correct diagnosis and provide constructive feedback.
        Rate the accuracy on a scale of 0-100 and explain your reasoning.
        Structure your response in JSON format with:
        - score: numeric score 0-100
        - feedback: detailed feedback explaining strengths and weaknesses
        - correct_points: specific correct elements in the diagnosis
        - improvement_areas: areas where the diagnosis could be improved
        """},
        {"role": "user", "content": f"Evaluate this diagnosis:\nUser diagnosis: {user_diagnosis}\nCorrect diagnosis: {correct_diagnosis}"}
    ]
    
    response = generate_ai_response(messages)
    
    try:
        # Extract JSON from response if wrapped in text
        if '```json' in response and '```' in response:
            json_str = response.split('```json')[1].split('```')[0].strip()
            evaluation = json.loads(json_str)
        else:
            evaluation = json.loads(response)
        
        return evaluation
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from evaluation response: {response}")
        return {"score": 0, "feedback": "Error processing evaluation."}
