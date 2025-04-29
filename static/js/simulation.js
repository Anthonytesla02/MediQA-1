// Case simulation with sequential question cards
const API_ENDPOINTS = {
  SIMULATION_NEW: '/api/simulation/new',
  SIMULATION_SUBMIT: '/api/simulation/submit'
};

document.addEventListener('DOMContentLoaded', () => {
  const simulationContainer = document.querySelector('.simulation-container');
  const newCaseButton = document.getElementById('new-case-button');
  const caseContent = document.getElementById('case-content');
  const questionContainer = document.getElementById('question-container');
  const caseResults = document.getElementById('case-results');
  
  // State variables
  let currentCase = null;
  let currentQuestionIndex = 0;
  let userAnswers = {};
  
  // Add event listener to new case button
  if (newCaseButton) {
    newCaseButton.addEventListener('click', loadNewCase);
  }
  
  // Load new case on page load
  if (caseContent) {
    loadNewCase();
  }
  
  // Helper function to toggle card expansion
  function toggleCardExpansion(card) {
    const cardBody = card.querySelector('.card-body');
    const toggleIcon = card.querySelector('.toggle-icon');
    
    cardBody.classList.toggle('expanded');
    toggleIcon.classList.toggle('expanded');
  }
  
  // Initialize expandable cards after they're added to the DOM
  function initExpandableCards() {
    document.querySelectorAll('.expandable-card').forEach(card => {
      const cardHeader = card.querySelector('.card-header');
      cardHeader.addEventListener('click', () => {
        toggleCardExpansion(card);
      });
    });
  }
  
  // Function to submit all answers
  async function submitAnswers() {
    // Collect multiple choice answers
    const mcAnswers = {};
    document.querySelectorAll('.mc-question').forEach(question => {
      const questionId = question.dataset.questionId;
      const selectedOption = question.querySelector('input[type="radio"]:checked');
      if (selectedOption) {
        mcAnswers[questionId] = selectedOption.value;
      }
    });
    
    // Collect free text answers
    const ftAnswers = {};
    document.querySelectorAll('.ft-question').forEach(question => {
      const questionId = question.dataset.questionId;
      const answerInput = question.querySelector('.free-text-input');
      if (answerInput && answerInput.value.trim()) {
        ftAnswers[questionId] = answerInput.value.trim();
      }
    });
    
    // Check if all questions are answered
    const mcQuestionsCount = document.querySelectorAll('.mc-question').length;
    const ftQuestionsCount = document.querySelectorAll('.ft-question').length;
    
    if (Object.keys(mcAnswers).length < mcQuestionsCount) {
      showToast('Error', 'Please answer all multiple choice questions', 'error');
      return;
    }
    
    if (Object.keys(ftAnswers).length < ftQuestionsCount) {
      showToast('Error', 'Please answer all free text questions', 'error');
      return;
    }
    
    // Prepare data for submission
    const submission = {
      mc_answers: mcAnswers,
      ft_answers: ftAnswers,
      case_id: currentCase.id || 'current'
    };
    
    // Show loading state
    submitAnswersBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Evaluating...';
    submitAnswersBtn.disabled = true;
    
    try {
      // Submit answers
      const response = await fetch(API_ENDPOINTS.SIMULATION_SUBMIT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submission)
      });
      
      const data = await response.json();
      
      // Reset button
      submitAnswersBtn.innerHTML = 'Submit All Answers';
      submitAnswersBtn.disabled = false;
      
      if (data.error) {
        showToast('Error', data.error, 'error');
        return;
      }
      
      // Show diagnosis result
      showResults(data);
      
      // Hide questions
      caseQuestions.style.display = 'none';
      
      // Show result
      diagnosisResult.style.display = 'block';
      
      // Haptic feedback
      if (typeof hapticFeedback === 'function') {
        hapticFeedback();
      }
      
      // Award points animation if logged in
      if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        showPointsAnimation(data.score || 50);
      }
    } catch (error) {
      console.error('Answer submission error:', error);
      
      // Reset button
      submitAnswersBtn.innerHTML = 'Submit All Answers';
      submitAnswersBtn.disabled = false;
      
      showToast('Error', 'An error occurred submitting your answers', 'error');
    }
  }

async function loadNewCase() {
  const caseContent = document.getElementById('case-content');
  const caseQuestions = document.getElementById('case-questions');
  const mcQuestionsContainer = document.getElementById('mc-questions-container');
  const ftQuestionsContainer = document.getElementById('ft-questions-container');
  const diagnosisResult = document.getElementById('diagnosis-result');
  
  // Reset UI
  caseQuestions.style.display = 'none';
  diagnosisResult.style.display = 'none';
  
  // Clear questions containers
  mcQuestionsContainer.innerHTML = '';
  ftQuestionsContainer.innerHTML = '';
  
  // Show loading state
  caseContent.innerHTML = '';
  caseContent.appendChild(createSkeletonLoader('card'));
  
  try {
    const response = await fetch(API_ENDPOINTS.SIMULATION_NEW);
    const data = await response.json();
    
    if (data.error) {
      caseContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
      return;
    }
    
    // Store current case
    currentCase = data;
    
    // Render case
    renderCase(data);
    
    // Render questions
    renderQuestions(data);
    
    // Show questions
    caseQuestions.style.display = 'block';
    
    // Initialize expandable cards
    initExpandableCards();
    
    // Haptic feedback
    if (typeof hapticFeedback === 'function') {
      hapticFeedback();
    }
  } catch (error) {
    console.error('Load case error:', error);
    caseContent.innerHTML = '<div class="alert alert-danger">Failed to load case. Please try again.</div>';
  }
}

function renderCase(caseData) {
  const caseContent = document.getElementById('case-content');
  caseContent.innerHTML = '';
  
  // Create patient info card (always expanded by default)
  const patientCard = createExpandableCard('Patient Information', true);
  
  // Format patient info in a grid
  const infoGrid = document.createElement('div');
  infoGrid.className = 'info-grid';
  
  const patientData = caseData.patient_info || {};
  Object.entries(patientData).forEach(([key, value]) => {
    const infoItem = document.createElement('div');
    infoItem.className = 'info-item';
    
    const infoLabel = document.createElement('div');
    infoLabel.className = 'info-label';
    infoLabel.textContent = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
    
    const infoValue = document.createElement('div');
    infoValue.className = 'info-value';
    // Check if the value is an object and properly format it
    if (typeof value === 'object' && value !== null) {
      // Format the object as a nice-looking string with proper spacing and line breaks
      try {
        const formattedValue = JSON.stringify(value, null, 2)
          .replace(/[{}"[\]]/g, '') // Remove brackets and quotes
          .replace(/,/g, '') // Remove commas
          .trim();
        infoValue.textContent = formattedValue;
      } catch (e) {
        infoValue.textContent = String(value);
      }
    } else {
      infoValue.textContent = value;
    }
    
    infoItem.appendChild(infoLabel);
    infoItem.appendChild(infoValue);
    infoGrid.appendChild(infoItem);
  });
  
  patientCard.querySelector('.card-content').appendChild(infoGrid);
  caseContent.appendChild(patientCard);
  
  // Create presenting complaint card (expanded by default)
  const complaintCard = createExpandableCard('Presenting Complaint', true);
  
  const complaintText = document.createElement('p');
  // Check if presenting_complaint is an object and format it properly
  if (typeof caseData.presenting_complaint === 'object' && caseData.presenting_complaint !== null) {
    // Format the object as a nice-looking string
    try {
      const formattedValue = JSON.stringify(caseData.presenting_complaint, null, 2)
        .replace(/[{}"[\]]/g, '') // Remove brackets and quotes
        .replace(/,/g, '') // Remove commas
        .trim();
      complaintText.textContent = formattedValue;
    } catch (e) {
      complaintText.textContent = 'Error displaying presenting complaint';
    }
  } else {
    complaintText.textContent = caseData.presenting_complaint || 'No presenting complaint provided.';
  }
  complaintCard.querySelector('.card-content').appendChild(complaintText);
  
  caseContent.appendChild(complaintCard);
  
  // Create history card
  const historyCard = createExpandableCard('Medical History');
  
  const historyList = document.createElement('div');
  historyList.className = 'findings-list';
  
  const historyData = caseData.history || {};
  Object.entries(historyData).forEach(([key, value]) => {
    const findingItem = document.createElement('div');
    findingItem.className = 'finding-item';
    
    const findingTitle = document.createElement('strong');
    findingTitle.textContent = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()) + ': ';
    
    findingItem.appendChild(findingTitle);
    // Check if the value is an object and properly format it
    if (typeof value === 'object' && value !== null) {
      // Format the object as a nice-looking string with proper spacing and line breaks
      try {
        const formattedValue = JSON.stringify(value, null, 2)
          .replace(/[{}"[\]]/g, '') // Remove brackets and quotes
          .replace(/,/g, '') // Remove commas
          .trim();
        findingItem.appendChild(document.createTextNode(formattedValue));
      } catch (e) {
        findingItem.appendChild(document.createTextNode(String(value)));
      }
    } else {
      findingItem.appendChild(document.createTextNode(value));
    }
    
    historyList.appendChild(findingItem);
  });
  
  historyCard.querySelector('.card-content').appendChild(historyList);
  caseContent.appendChild(historyCard);
  
  // Create examination findings card
  const examinationCard = createExpandableCard('Examination Findings');
  
  const examinationList = document.createElement('div');
  examinationList.className = 'findings-list';
  
  const examinationData = caseData.examination || {};
  Object.entries(examinationData).forEach(([key, value]) => {
    const findingItem = document.createElement('div');
    findingItem.className = 'finding-item';
    
    const findingTitle = document.createElement('strong');
    findingTitle.textContent = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()) + ': ';
    
    findingItem.appendChild(findingTitle);
    // Check if the value is an object and properly format it
    if (typeof value === 'object' && value !== null) {
      // Format the object as a nice-looking string with proper spacing and line breaks
      try {
        const formattedValue = JSON.stringify(value, null, 2)
          .replace(/[{}"[\]]/g, '') // Remove brackets and quotes
          .replace(/,/g, '') // Remove commas
          .trim();
        findingItem.appendChild(document.createTextNode(formattedValue));
      } catch (e) {
        findingItem.appendChild(document.createTextNode(String(value)));
      }
    } else {
      findingItem.appendChild(document.createTextNode(value));
    }
    
    examinationList.appendChild(findingItem);
  });
  
  examinationCard.querySelector('.card-content').appendChild(examinationList);
  caseContent.appendChild(examinationCard);
  
  // Create vitals card
  const vitalsCard = createExpandableCard('Vital Signs');
  
  const vitalsList = document.createElement('div');
  vitalsList.className = 'findings-list';
  
  const vitalsData = caseData.vitals || {};
  Object.entries(vitalsData).forEach(([key, value]) => {
    const findingItem = document.createElement('div');
    findingItem.className = 'finding-item';
    
    const findingTitle = document.createElement('strong');
    findingTitle.textContent = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()) + ': ';
    
    findingItem.appendChild(findingTitle);
    // Check if the value is an object and properly format it
    if (typeof value === 'object' && value !== null) {
      // Format the object as a nice-looking string with proper spacing and line breaks
      try {
        const formattedValue = JSON.stringify(value, null, 2)
          .replace(/[{}"[\]]/g, '') // Remove brackets and quotes
          .replace(/,/g, '') // Remove commas
          .trim();
        findingItem.appendChild(document.createTextNode(formattedValue));
      } catch (e) {
        findingItem.appendChild(document.createTextNode(String(value)));
      }
    } else {
      findingItem.appendChild(document.createTextNode(value));
    }
    
    vitalsList.appendChild(findingItem);
  });
  
  vitalsCard.querySelector('.card-content').appendChild(vitalsList);
  caseContent.appendChild(vitalsCard);
  
  // Animate cards
  const cards = caseContent.querySelectorAll('.expandable-card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s, transform 0.5s';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 100);
  });
}

// Helper function to create expandable card
function createExpandableCard(title, expanded = false) {
  const card = document.createElement('div');
  card.className = 'expandable-card';
  
  const cardHeader = document.createElement('div');
  cardHeader.className = 'card-header';
  
  const cardTitle = document.createElement('h3');
  cardTitle.textContent = title;
  
  const toggleIcon = document.createElement('span');
  toggleIcon.className = `toggle-icon ${expanded ? 'expanded' : ''}`;
  toggleIcon.innerHTML = '<i data-feather="chevron-down"></i>';
  
  cardHeader.appendChild(cardTitle);
  cardHeader.appendChild(toggleIcon);
  
  const cardBody = document.createElement('div');
  cardBody.className = `card-body ${expanded ? 'expanded' : ''}`;
  
  const cardContent = document.createElement('div');
  cardContent.className = 'card-content';
  
  cardBody.appendChild(cardContent);
  
  card.appendChild(cardHeader);
  card.appendChild(cardBody);
  
  return card;
}

function showDiagnosisResult(data, userDiagnosis) {
  const diagnosisResult = document.getElementById('diagnosis-result');
  diagnosisResult.innerHTML = '';
  
  // Create header with score
  const resultHeader = document.createElement('div');
  resultHeader.className = 'result-header';
  
  const score = data.evaluation.score || 0;
  const isCorrect = score >= 70;
  
  const resultIcon = document.createElement('div');
  resultIcon.className = `result-icon ${isCorrect ? 'correct' : 'incorrect'}`;
  resultIcon.innerHTML = isCorrect ? 
    '<i data-feather="check-circle"></i>' : 
    '<i data-feather="x-circle"></i>';
  
  const resultTitle = document.createElement('h3');
  resultTitle.className = 'result-title';
  resultTitle.textContent = isCorrect ? 'Good job!' : 'Needs improvement';
  
  resultHeader.appendChild(resultIcon);
  resultHeader.appendChild(resultTitle);
  diagnosisResult.appendChild(resultHeader);
  
  // Show score
  const resultScore = document.createElement('div');
  resultScore.className = 'result-score';
  resultScore.textContent = `Score: ${score}/100`;
  diagnosisResult.appendChild(resultScore);
  
  // Show feedback
  const resultFeedback = document.createElement('div');
  resultFeedback.className = 'result-feedback';
  resultFeedback.textContent = data.evaluation.feedback || 'No feedback available.';
  diagnosisResult.appendChild(resultFeedback);
  
  // Create section for correct diagnosis
  const correctDiagnosis = document.createElement('div');
  correctDiagnosis.className = 'correct-diagnosis';
  
  const correctTitle = document.createElement('h4');
  correctTitle.textContent = 'Correct Diagnosis';
  correctDiagnosis.appendChild(correctTitle);
  
  const correctText = document.createElement('p');
  correctText.textContent = data.correct_diagnosis || 'No diagnosis provided.';
  correctDiagnosis.appendChild(correctText);
  
  const reasoningTitle = document.createElement('h4');
  reasoningTitle.textContent = 'Diagnostic Reasoning';
  correctDiagnosis.appendChild(reasoningTitle);
  
  const reasoningText = document.createElement('p');
  reasoningText.textContent = data.reasoning || 'No reasoning provided.';
  correctDiagnosis.appendChild(reasoningText);
  
  diagnosisResult.appendChild(correctDiagnosis);
  
  // Create section for differential diagnoses
  const differentialDiagnoses = document.createElement('div');
  differentialDiagnoses.className = 'differential-diagnoses';
  
  const differentialTitle = document.createElement('h4');
  differentialTitle.textContent = 'Differential Diagnoses';
  differentialDiagnoses.appendChild(differentialTitle);
  
  if (data.differential_diagnoses && data.differential_diagnoses.length > 0) {
    data.differential_diagnoses.forEach(differential => {
      const differentialItem = document.createElement('div');
      differentialItem.className = 'differential-item';
      
      const diagnosisName = document.createElement('strong');
      diagnosisName.textContent = differential.diagnosis || '';
      differentialItem.appendChild(diagnosisName);
      
      if (differential.reason) {
        differentialItem.appendChild(document.createElement('br'));
        differentialItem.appendChild(document.createTextNode(differential.reason));
      }
      
      differentialDiagnoses.appendChild(differentialItem);
    });
  } else {
    const noDifferentials = document.createElement('p');
    noDifferentials.textContent = 'No differential diagnoses provided.';
    differentialDiagnoses.appendChild(noDifferentials);
  }
  
  diagnosisResult.appendChild(differentialDiagnoses);
  
  // Create action buttons
  const actionButtons = document.createElement('div');
  actionButtons.className = 'action-buttons';
  actionButtons.style.marginTop = '2rem';
  actionButtons.style.display = 'flex';
  actionButtons.style.justifyContent = 'center';
  
  const newCaseButton = document.createElement('button');
  newCaseButton.className = 'btn btn-primary';
  newCaseButton.textContent = 'New Case';
  newCaseButton.addEventListener('click', loadNewCase);
  
  actionButtons.appendChild(newCaseButton);
  diagnosisResult.appendChild(actionButtons);
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Animate result in
  diagnosisResult.classList.add('fadeIn');
}

// Function to render questions
function renderQuestions(caseData) {
  const mcQuestionsContainer = document.getElementById('mc-questions-container');
  const ftQuestionsContainer = document.getElementById('ft-questions-container');
  
  // Clear containers
  mcQuestionsContainer.innerHTML = '';
  ftQuestionsContainer.innerHTML = '';
  
  // Render multiple choice questions
  if (caseData.multiple_choice_questions && caseData.multiple_choice_questions.length > 0) {
    caseData.multiple_choice_questions.forEach((question, index) => {
      const questionItem = document.createElement('div');
      questionItem.className = 'question-item mc-question';
      questionItem.dataset.questionId = index;
      
      const questionText = document.createElement('div');
      questionText.className = 'question-text';
      questionText.innerHTML = `<span class="question-number">${index + 1}</span> ${question.question}`;
      questionItem.appendChild(questionText);
      
      const optionsList = document.createElement('ul');
      optionsList.className = 'options-list';
      
      question.options.forEach((option, optIndex) => {
        const optionItem = document.createElement('li');
        optionItem.className = 'option-item';
        optionItem.dataset.optionIndex = optIndex;
        
        const optionLabel = document.createElement('label');
        optionLabel.className = 'option-label';
        
        const optionRadio = document.createElement('input');
        optionRadio.type = 'radio';
        optionRadio.name = `mc-question-${index}`;
        optionRadio.value = option;
        optionRadio.className = 'option-radio';
        
        optionLabel.appendChild(optionRadio);
        optionLabel.appendChild(document.createTextNode(option));
        
        optionItem.appendChild(optionLabel);
        
        // Add click handler to the option item for better UX
        optionItem.addEventListener('click', () => {
          // Check the radio button
          optionRadio.checked = true;
          
          // Add selected class to this option and remove from siblings
          document.querySelectorAll(`ul.options-list li[data-option-index]`).forEach(el => {
            if (el.parentElement === optionsList) {
              el.classList.remove('selected');
            }
          });
          optionItem.classList.add('selected');
        });
        
        optionsList.appendChild(optionItem);
      });
      
      questionItem.appendChild(optionsList);
      mcQuestionsContainer.appendChild(questionItem);
    });
  } else {
    mcQuestionsContainer.innerHTML = '<div class="alert alert-warning">No multiple choice questions available.</div>';
  }
  
  // Render free text questions
  if (caseData.free_text_questions && caseData.free_text_questions.length > 0) {
    caseData.free_text_questions.forEach((question, index) => {
      const questionItem = document.createElement('div');
      questionItem.className = 'question-item ft-question';
      questionItem.dataset.questionId = index;
      
      const questionText = document.createElement('div');
      questionText.className = 'question-text';
      questionText.innerHTML = `<span class="question-number">${index + 1}</span> ${question.question}`;
      questionItem.appendChild(questionText);
      
      const answerInput = document.createElement('textarea');
      answerInput.className = 'free-text-input';
      answerInput.placeholder = 'Type your answer here...';
      
      questionItem.appendChild(answerInput);
      ftQuestionsContainer.appendChild(questionItem);
    });
  } else {
    ftQuestionsContainer.innerHTML = '<div class="alert alert-warning">No free text questions available.</div>';
  }
}

// Function to show results after submission
function showResults(data) {
  const diagnosisResult = document.getElementById('diagnosis-result');
  diagnosisResult.innerHTML = '';
  
  // Create header with score
  const resultHeader = document.createElement('div');
  resultHeader.className = 'result-header';
  
  const score = data.score || 0;
  const isCorrect = score >= 70;
  
  const resultIcon = document.createElement('div');
  resultIcon.className = `result-icon ${isCorrect ? 'correct' : 'incorrect'}`;
  resultIcon.innerHTML = isCorrect ? 
    '<i data-feather="check-circle"></i>' : 
    '<i data-feather="x-circle"></i>';
  
  const resultTitle = document.createElement('h3');
  resultTitle.className = 'result-title';
  resultTitle.textContent = isCorrect ? 'Good job!' : 'Needs improvement';
  
  resultHeader.appendChild(resultIcon);
  resultHeader.appendChild(resultTitle);
  diagnosisResult.appendChild(resultHeader);
  
  // Show score
  const resultScore = document.createElement('div');
  resultScore.className = 'result-score';
  resultScore.textContent = `Score: ${score}/100`;
  diagnosisResult.appendChild(resultScore);
  
  // Show feedback
  const resultFeedback = document.createElement('div');
  resultFeedback.className = 'result-feedback';
  resultFeedback.textContent = data.feedback || 'No feedback available.';
  diagnosisResult.appendChild(resultFeedback);
  
  // Show multiple choice question results
  if (data.mc_results && data.mc_results.length > 0) {
    const mcResultsSection = document.createElement('div');
    mcResultsSection.className = 'question-results-section';
    
    const mcResultsTitle = document.createElement('h4');
    mcResultsTitle.textContent = 'Multiple Choice Questions';
    mcResultsSection.appendChild(mcResultsTitle);
    
    data.mc_results.forEach((result, index) => {
      const resultItem = document.createElement('div');
      resultItem.className = `question-result ${result.correct ? 'correct' : 'incorrect'}`;
      
      const resultQuestion = document.createElement('h5');
      resultQuestion.textContent = `Question ${index + 1}: ${result.question}`;
      resultItem.appendChild(resultQuestion);
      
      const resultAnswer = document.createElement('p');
      resultAnswer.innerHTML = `Your answer: <strong>${result.user_answer}</strong>`;
      if (!result.correct) {
        resultAnswer.innerHTML += `<br>Correct answer: <strong>${result.correct_answer}</strong>`;
      }
      resultItem.appendChild(resultAnswer);
      
      mcResultsSection.appendChild(resultItem);
    });
    
    diagnosisResult.appendChild(mcResultsSection);
  }
  
  // Show free text question results
  if (data.ft_results && data.ft_results.length > 0) {
    const ftResultsSection = document.createElement('div');
    ftResultsSection.className = 'question-results-section';
    
    const ftResultsTitle = document.createElement('h4');
    ftResultsTitle.textContent = 'Free Text Questions';
    ftResultsSection.appendChild(ftResultsTitle);
    
    data.ft_results.forEach((result, index) => {
      const resultItem = document.createElement('div');
      resultItem.className = `question-result ${result.score >= 70 ? 'correct' : 'incorrect'}`;
      
      const resultQuestion = document.createElement('h5');
      resultQuestion.textContent = `Question ${index + 1}: ${result.question}`;
      resultItem.appendChild(resultQuestion);
      
      const resultAnswer = document.createElement('p');
      resultAnswer.innerHTML = `Your answer: <strong>${result.user_answer}</strong>`;
      resultItem.appendChild(resultAnswer);
      
      const resultIdealAnswer = document.createElement('p');
      resultIdealAnswer.innerHTML = `Ideal answer: ${result.ideal_answer}`;
      resultItem.appendChild(resultIdealAnswer);
      
      // Show matched key concepts if available
      if (result.matched_concepts && result.matched_concepts.length > 0) {
        const conceptsTitle = document.createElement('p');
        conceptsTitle.textContent = 'Key concepts identified in your answer:';
        resultItem.appendChild(conceptsTitle);
        
        const conceptsContainer = document.createElement('div');
        conceptsContainer.className = 'key-concepts';
        
        result.matched_concepts.forEach(concept => {
          const conceptSpan = document.createElement('span');
          conceptSpan.className = 'key-concept matched';
          conceptSpan.textContent = concept;
          conceptsContainer.appendChild(conceptSpan);
        });
        
        resultItem.appendChild(conceptsContainer);
      }
      
      // Show missing key concepts if available
      if (result.missing_concepts && result.missing_concepts.length > 0) {
        const missingTitle = document.createElement('p');
        missingTitle.textContent = 'Key concepts missing from your answer:';
        resultItem.appendChild(missingTitle);
        
        const missingContainer = document.createElement('div');
        missingContainer.className = 'key-concepts';
        
        result.missing_concepts.forEach(concept => {
          const conceptSpan = document.createElement('span');
          conceptSpan.className = 'key-concept';
          conceptSpan.textContent = concept;
          missingContainer.appendChild(conceptSpan);
        });
        
        resultItem.appendChild(missingContainer);
      }
      
      ftResultsSection.appendChild(resultItem);
    });
    
    diagnosisResult.appendChild(ftResultsSection);
  }
  
  // Create section for correct diagnosis
  const correctDiagnosis = document.createElement('div');
  correctDiagnosis.className = 'correct-diagnosis';
  
  const correctTitle = document.createElement('h4');
  correctTitle.textContent = 'Correct Diagnosis';
  correctDiagnosis.appendChild(correctTitle);
  
  const correctText = document.createElement('p');
  correctText.textContent = data.diagnosis || 'No diagnosis provided.';
  correctDiagnosis.appendChild(correctText);
  
  const reasoningTitle = document.createElement('h4');
  reasoningTitle.textContent = 'Diagnostic Reasoning';
  correctDiagnosis.appendChild(reasoningTitle);
  
  const reasoningText = document.createElement('p');
  reasoningText.textContent = data.reasoning || 'No reasoning provided.';
  correctDiagnosis.appendChild(reasoningText);
  
  diagnosisResult.appendChild(correctDiagnosis);
  
  // Create section for differential diagnoses
  if (data.differential_diagnoses && data.differential_diagnoses.length > 0) {
    const differentialDiagnoses = document.createElement('div');
    differentialDiagnoses.className = 'differential-diagnoses';
    
    const differentialTitle = document.createElement('h4');
    differentialTitle.textContent = 'Differential Diagnoses';
    differentialDiagnoses.appendChild(differentialTitle);
    
    data.differential_diagnoses.forEach(differential => {
      const differentialItem = document.createElement('div');
      differentialItem.className = 'differential-item';
      
      const diagnosisName = document.createElement('strong');
      diagnosisName.textContent = differential.diagnosis || '';
      differentialItem.appendChild(diagnosisName);
      
      if (differential.reason) {
        differentialItem.appendChild(document.createElement('br'));
        differentialItem.appendChild(document.createTextNode(differential.reason));
      }
      
      differentialDiagnoses.appendChild(differentialItem);
    });
    
    diagnosisResult.appendChild(differentialDiagnoses);
  }
  
  // Create action buttons
  const actionButtons = document.createElement('div');
  actionButtons.className = 'action-buttons';
  
  const newCaseButton = document.createElement('button');
  newCaseButton.className = 'btn btn-primary';
  newCaseButton.innerHTML = '<i data-feather="refresh-cw"></i> New Case';
  newCaseButton.addEventListener('click', loadNewCase);
  
  actionButtons.appendChild(newCaseButton);
  diagnosisResult.appendChild(actionButtons);
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Animate diagnosis result
  diagnosisResult.style.opacity = '0';
  diagnosisResult.style.transform = 'translateY(20px)';
  
  setTimeout(() => {
    diagnosisResult.style.transition = 'opacity 0.5s, transform 0.5s';
    diagnosisResult.style.opacity = '1';
    diagnosisResult.style.transform = 'translateY(0)';
  }, 100);
  
  // Scroll to diagnosis result
  diagnosisResult.scrollIntoView({ behavior: 'smooth' });
}

function showPointsAnimation(points) {
  const pointsElement = document.createElement('div');
  pointsElement.className = 'points-animation';
  pointsElement.textContent = `+${points} points`;
  pointsElement.style.position = 'fixed';
  pointsElement.style.top = '50%';
  pointsElement.style.left = '50%';
  pointsElement.style.transform = 'translate(-50%, -50%)';
  pointsElement.style.fontSize = '2rem';
  pointsElement.style.fontWeight = 'bold';
  pointsElement.style.color = '#2ecc71';
  pointsElement.style.opacity = '0';
  pointsElement.style.zIndex = '9999';
  pointsElement.style.pointerEvents = 'none';
  
  document.body.appendChild(pointsElement);
  
  // Animate points
  pointsElement.animate(
    [
      { opacity: 0, transform: 'translate(-50%, -50%) scale(0.5)' },
      { opacity: 1, transform: 'translate(-50%, -50%) scale(1.2)' },
      { opacity: 0, transform: 'translate(-50%, -50%) scale(1.5) translateY(-50px)' }
    ],
    {
      duration: 1500,
      easing: 'ease-out'
    }
  );
  
  // Remove element after animation
  setTimeout(() => {
    document.body.removeChild(pointsElement);
  }, 1500);
}

// Close the DOMContentLoaded event listener
});
