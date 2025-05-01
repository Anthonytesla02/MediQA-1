// Case simulation with sequential questions
// Define API endpoints if not already defined in main.js
if (typeof API_ENDPOINTS === 'undefined') {
  window.API_ENDPOINTS = {};
}

// Set simulation endpoints if not already set
if (!API_ENDPOINTS.SIMULATION_NEW) {
  API_ENDPOINTS.SIMULATION_NEW = '/api/simulation/new';
}
if (!API_ENDPOINTS.SIMULATION_SUBMIT) {
  API_ENDPOINTS.SIMULATION_SUBMIT = '/api/simulation/submit';
}

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const newCaseButton = document.getElementById('new-case-button');
  const presentingComplaint = document.getElementById('presenting-complaint');
  const questionsContainer = document.getElementById('questions-container');
  const resultsContainer = document.getElementById('results-container');
  
  // State variables
  let currentCase = null;
  let currentQuestionIndex = 0;
  let userAnswers = {};
  
  // Add keyboard shortcut support
  document.addEventListener('keydown', handleKeyboardShortcuts);
  
  // Add event listener to new case button
  if (newCaseButton) {
    newCaseButton.addEventListener('click', loadNewCase);
  }
  
  // Load new case on page load or restore previous session
  if (presentingComplaint) {
    // Try to restore from session storage first
    try {
      const savedCase = sessionStorage.getItem('currentCase');
      if (savedCase) {
        currentCase = JSON.parse(savedCase);
        console.log('Restored case from sessionStorage:', currentCase);
        
        // Render the restored case
        renderPresentingComplaint(currentCase.presenting_complaint);
        
        if (currentCase.questions && currentCase.questions.length > 0) {
          console.log('Creating question cards from saved case:', currentCase.questions.length);
          createQuestionCards(currentCase.questions);
        }
      } else {
        // No saved case, load a new one
        loadNewCase();
      }
    } catch (e) {
      console.error('Error restoring case from sessionStorage:', e);
      loadNewCase();
    }
  }
  
  // Function to load a new medical case
  async function loadNewCase() {
    console.log('Loading new case...');
    
    // Reset UI
    if (presentingComplaint) presentingComplaint.innerHTML = '';
    if (questionsContainer) {
      questionsContainer.innerHTML = '';
      questionsContainer.style.display = 'block'; // Ensure questions are visible
    }
    if (resultsContainer) {
      resultsContainer.innerHTML = ''; // Clear previous results
      resultsContainer.style.display = 'none';
    }
    
    // Reset state
    currentQuestionIndex = 0;
    userAnswers = {};
    currentCase = null; // Clear current case reference
    
    // Show loading state
    presentingComplaint.innerHTML = '<div class="skeleton-loader"></div>';
    
    try {
      console.log('Fetching from:', API_ENDPOINTS.SIMULATION_NEW);
      
      const response = await fetch(API_ENDPOINTS.SIMULATION_NEW);
      console.log('Response received:', response.status);
      
      const data = await response.json();
      console.log('Data received:', data);
      
      if (data.error) {
        console.error('Error in response:', data.error);
        presentingComplaint.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
      }
      
      // Store current case
      currentCase = data;
      console.log('Case data stored:', currentCase);
      
      // Store in sessionStorage for persistence
      try {
        sessionStorage.setItem('currentCase', JSON.stringify(currentCase));
        console.log('Case saved to sessionStorage');
      } catch (e) {
        console.error('Failed to save case to sessionStorage:', e);
      }
      
      // Render presenting complaint
      console.log('Rendering complaint:', data.presenting_complaint);
      renderPresentingComplaint(data.presenting_complaint);
      
      // Create question cards (initially hidden except first)
      if (data.questions && data.questions.length > 0) {
        console.log('Creating question cards:', data.questions.length);
        createQuestionCards(data.questions);
      } else {
        console.warn('No questions received in data');
      }
      
      // Haptic feedback if available
      if (typeof hapticFeedback === 'function') {
        hapticFeedback();
      }
    } catch (error) {
      console.error('Load case error:', error);
      presentingComplaint.innerHTML = '<div class="alert alert-danger">Failed to load case. Please try again.</div>';
    }
  }
  
  // Function to render the presenting complaint
  function renderPresentingComplaint(complaint) {
    presentingComplaint.innerHTML = '';
    
    const complaintCard = document.createElement('div');
    complaintCard.className = 'complaint-card';
    
    const complaintTitle = document.createElement('h3');
    complaintTitle.textContent = 'Presenting Complaint';
    complaintCard.appendChild(complaintTitle);
    
    const complaintText = document.createElement('p');
    complaintText.textContent = complaint;
    complaintCard.appendChild(complaintText);
    
    presentingComplaint.appendChild(complaintCard);
  }
  
  // Function to create question cards
  function createQuestionCards(questions) {
    questionsContainer.innerHTML = '';
    
    // Add a progress indicator if there are multiple questions
    if (questions.length > 1) {
      const progressContainer = document.createElement('div');
      progressContainer.className = 'question-progress';
      progressContainer.innerHTML = `<div class="progress-text">Question <span id="current-question">1</span> of ${questions.length}</div>`;
      questionsContainer.appendChild(progressContainer);
      
      // Add keyboard shortcut notice
      const shortcutNotice = document.createElement('div');
      shortcutNotice.className = 'shortcut-notice';
      shortcutNotice.innerHTML = `<small>Tip: Use 'n' or '→' to advance, 's' to submit on the final question</small>`;
      questionsContainer.appendChild(shortcutNotice);
    }
    
    questions.forEach((question, index) => {
      const questionCard = document.createElement('div');
      questionCard.className = index === 0 ? 'question-card' : 'question-card hidden-question';
      questionCard.id = `question-${question.id}`;
      questionCard.dataset.questionIndex = index;
      
      const questionTitle = document.createElement('h3');
      questionTitle.textContent = question.question;
      questionCard.appendChild(questionTitle);
      
      const answerInput = document.createElement('div');
      answerInput.className = 'answer-input';
      
      const textarea = document.createElement('textarea');
      textarea.placeholder = 'Enter your answer here...';
      textarea.id = `answer-${question.id}`;
      textarea.dataset.field = question.field;
      
      answerInput.appendChild(textarea);
      questionCard.appendChild(answerInput);
      
      const submitButton = document.createElement('button');
      submitButton.className = 'submit-btn';
      submitButton.textContent = index === questions.length - 1 ? 'Submit' : 'Next';
      
      submitButton.addEventListener('click', () => {
        handleQuestionSubmit(question, index);
      });
      
      questionCard.appendChild(submitButton);
      questionsContainer.appendChild(questionCard);
    });
  }
  
  // Function to handle question submission
  function handleQuestionSubmit(question, index) {
    // Get answer text
    const textarea = document.querySelector(`#answer-${question.id}`);
    const answerText = textarea.value.trim();
    
    // Validate answer
    if (!answerText) {
      if (typeof showToast === 'function') {
        showToast('Error', 'Please provide an answer', 'error');
      } else {
        alert('Please provide an answer');
      }
      return;
    }
    
    // Save answer
    userAnswers[question.field] = answerText;
    
    // If this is the last question, submit all answers
    if (index === currentCase.questions.length - 1) {
      submitAllAnswers();
    } else {
      // Show next question
      moveToNextQuestion(index);
    }
  }
  
  // Function to move to the next question
  function moveToNextQuestion(currentIndex) {
    // Hide current question
    const currentQuestion = document.querySelector(`.question-card[data-question-index="${currentIndex}"]`);
    currentQuestion.classList.add('hidden-question');
    
    // Show next question
    const nextIndex = currentIndex + 1;
    const nextQuestion = document.querySelector(`.question-card[data-question-index="${nextIndex}"]`);
    nextQuestion.classList.remove('hidden-question');
    
    // Update progress indicator
    const progressIndicator = document.getElementById('current-question');
    if (progressIndicator) {
      progressIndicator.textContent = nextIndex + 1; // +1 because it's 0-indexed
    }
    
    // Focus on the next textarea
    setTimeout(() => {
      const nextTextarea = nextQuestion.querySelector('textarea');
      if (nextTextarea) nextTextarea.focus();
    }, 100);
  }
  
  // Function to submit all answers
  async function submitAllAnswers() {
    // Check if all questions are answered
    if (Object.keys(userAnswers).length < currentCase.questions.length) {
      if (typeof showToast === 'function') {
        showToast('Error', 'Please answer all questions', 'error');
      } else {
        alert('Please answer all questions');
      }
      return;
    }
    
    // Get and disable the submit button
    const lastQuestion = document.querySelector(`.question-card[data-question-index="${currentCase.questions.length - 1}"]`);
    const submitBtn = lastQuestion.querySelector('.submit-btn');
    
    // Show loading state
    submitBtn.textContent = 'Evaluating...';
    submitBtn.disabled = true;
    
    try {
      // Submit answers to server
      console.log('Submitting answers:', userAnswers, 'for case topic:', currentCase.differential_topic);
      const response = await fetch(API_ENDPOINTS.SIMULATION_SUBMIT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          answers: userAnswers,
          case_id: currentCase.differential_topic // Include an identifier for the case
        })
      });
      
      const data = await response.json();
      
      // Reset button
      submitBtn.textContent = 'Submit';
      submitBtn.disabled = false;
      
      if (data.error) {
        if (typeof showToast === 'function') {
          showToast('Error', data.error, 'error');
        } else {
          alert('Error: ' + data.error);
        }
        return;
      }
      
      // Hide questions and show results
      questionsContainer.style.display = 'none';
      showResults(data);
      
    } catch (error) {
      console.error('Answer submission error:', error);
      
      // Reset button
      submitBtn.textContent = 'Submit';
      submitBtn.disabled = false;
      
      if (typeof showToast === 'function') {
        showToast('Error', 'An error occurred submitting your answers', 'error');
      } else {
        alert('An error occurred submitting your answers');
      }
    }
  }
  
  // Function to show results
  function showResults(data) {
    console.log('Showing results:', data);
    resultsContainer.innerHTML = '';
    resultsContainer.style.display = 'block';
    questionsContainer.style.display = 'none'; // Hide questions when showing results
    
    // Clear the saved case since we're showing results
    try {
      sessionStorage.removeItem('currentCase');
      console.log('Cleared case from sessionStorage after showing results');
    } catch (e) {
      console.error('Failed to clear case from sessionStorage:', e);
    }
    
    // Create result title
    const resultTitle = document.createElement('h3');
    resultTitle.className = 'result-title';
    resultTitle.textContent = 'Case Results';
    resultsContainer.appendChild(resultTitle);
    
    // Add score
    const scoreElement = document.createElement('div');
    scoreElement.className = 'score';
    scoreElement.innerHTML = `<span>Your Score: <strong>${data.score}%</strong></span>`;
    resultsContainer.appendChild(scoreElement);
    
    // Add overall feedback if available
    if (data.feedback) {
      const feedbackElement = document.createElement('p');
      feedbackElement.className = 'result-feedback';
      feedbackElement.textContent = data.feedback;
      resultsContainer.appendChild(feedbackElement);
    }
    
    // Display question-by-question results
    if (data.questions && data.questions.length > 0) {
      const questionsTitle = document.createElement('h4');
      questionsTitle.className = 'questions-title';
      questionsTitle.textContent = 'Detailed Feedback';
      questionsTitle.style.marginTop = '1.5rem';
      resultsContainer.appendChild(questionsTitle);
      
      data.questions.forEach(question => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item' + (question.correct ? ' correct' : ' incorrect');
        
        // Question
        const questionElement = document.createElement('div');
        questionElement.className = 'result-question';
        questionElement.textContent = question.question;
        resultItem.appendChild(questionElement);
        
        // User answer
        const userAnswerTitle = document.createElement('div');
        userAnswerTitle.className = 'result-subtitle';
        userAnswerTitle.textContent = 'Your answer:';
        resultItem.appendChild(userAnswerTitle);
        
        const userAnswer = document.createElement('div');
        userAnswer.className = 'result-user-answer';
        userAnswer.textContent = userAnswers[question.field] || 'No answer provided';
        resultItem.appendChild(userAnswer);
        
        // Feedback
        if (question.feedback) {
          const feedbackElement = document.createElement('div');
          feedbackElement.className = 'result-feedback';
          feedbackElement.textContent = question.feedback;
          resultItem.appendChild(feedbackElement);
        }
        
        // Add correct answer display for incorrect answers
        if (!question.correct && question.feedback) {
          let correctAnswer = '';
          
          // Extract correct answer from feedback text
          if (question.field === 'diagnosis') {
            const match = question.feedback.match(/The correct diagnosis is: ([^.]+)/);
            if (match && match[1]) {
              correctAnswer = match[1];
            }
          } else if (question.field === 'treatment') {
            // Handle various treatment feedback formats
            // First, try to match the new "Correct answer:" format
            let match = question.feedback.match(/Correct answer:([\s\S]+)/);
            
            // If not found, try legacy formats
            if (!match) {
              match = question.feedback.match(/Recommended treatment: ([\s\S]+)/);
            }
            if (!match) {
              match = question.feedback.match(/Recommended treatment includes: ([\s\S]+)/);
            }
            
            if (match && match[1]) {
              correctAnswer = match[1].trim();
            }
          }
          
          // Only show if we extracted a correct answer
          if (correctAnswer) {
            const correctTitle = document.createElement('div');
            correctTitle.className = 'result-subtitle correct-answer-title';
            correctTitle.textContent = 'Correct answer:';
            resultItem.appendChild(correctTitle);
            
            // For treatment responses, we need to format and trim them
            if (question.field === 'treatment') {
              // Check if the answer already contains bullet points\n              let formattedAnswer = "";\n              \n              if (correctAnswer.includes("\n") || correctAnswer.includes("\u2022")) {\n                // The answer is already formatted with bullets or line breaks\n                formattedAnswer = correctAnswer;\n              } else if (correctAnswer.length > 200) {\n                // For plain text answers that are long, format with bullet points\n                // Detect common separators (periods, semicolons)\n                let lines = [];\n                if (correctAnswer.includes(";")) {\n                  lines = correctAnswer.split(";");\n                } else {\n                  lines = correctAnswer.split(".");\n                }\n                \n                let bulletPoints = [];\n                \n                // Process each line into bullet points, skipping empty ones\n                for (let line of lines) {\n                  line = line.trim();\n                  if (line.length > 10) { // Skip very short fragments\n                    // Remove any numbering or dash prefixes\n                    line = line.replace(/^\\d+\\s*[\\)\\.]*\\s*/, "");\n                    line = line.replace(/^-\\s*/, "");\n                    line = line.replace(/^\\u2022\\s*/, "");\n                    \n                    // Skip lines with IV/IM mentions - not for pharmacy practice\n                    if (!line.match(/\\b(IV|iv|intravenous|IM|im|intramuscular|injection|infusion|surgical|surgery|incision|drain|catheter|lumbar|puncture|biopsy)\\b/i)) {\n                      bulletPoints.push("\\u2022 " + line);\n                    }\n                  }\n                }\n                \n                // Take only up to 5 key points to keep it manageable\n                bulletPoints = bulletPoints.slice(0, 5);\n                formattedAnswer = bulletPoints.join("\\n");\n              } else {\n                formattedAnswer = correctAnswer;\n              }
              
              const correctAnswerEl = document.createElement('div');
              correctAnswerEl.className = 'result-correct-answer';
              correctAnswerEl.style.whiteSpace = 'pre-line';
              correctAnswerEl.textContent = formattedAnswer;
              resultItem.appendChild(correctAnswerEl);
            } else {
              // For diagnoses, just show the full answer (it's usually short)
              const correctAnswerEl = document.createElement('div');
              correctAnswerEl.className = 'result-correct-answer';
              correctAnswerEl.textContent = correctAnswer;
              resultItem.appendChild(correctAnswerEl);
            }
          }
        }
        
        resultsContainer.appendChild(resultItem);
      });
    }
    
    // Add summary based on topic
    if (data.topic) {
      const topicElement = document.createElement('div');
      topicElement.className = 'topic-summary';
      topicElement.innerHTML = `<p><strong>This case focused on: </strong>${data.topic}</p>`;
      
      if (data.differential_topic) {
        topicElement.innerHTML += `<p><strong>Differential consideration: </strong>${data.differential_topic}</p>`;
      }
      
      resultsContainer.appendChild(topicElement);
    }
    
    // Add new case button
    const newCaseButton = document.createElement('button');
    newCaseButton.className = 'btn btn-primary';
    newCaseButton.textContent = 'Try Another Case';
    newCaseButton.addEventListener('click', loadNewCase);
    
    const buttonContainer = document.createElement('div');
    buttonContainer.style.textAlign = 'center';
    buttonContainer.style.marginTop = '1.5rem';
    buttonContainer.appendChild(newCaseButton);
    
    resultsContainer.appendChild(buttonContainer);
  }
  
  // Helper function to create skeleton loader if not available
  function createSkeletonLoader() {
    const loader = document.createElement('div');
    loader.className = 'skeleton-loader';
    return loader;
  }
  
  // Handle keyboard shortcuts
  function handleKeyboardShortcuts(event) {
    // Only process if we have an active case
    if (!currentCase) return;
    
    // Don't process if inside a textarea or results are showing
    if (event.target.tagName === 'TEXTAREA' || resultsContainer.style.display === 'block') return;
    
    // Get the current active question
    const activeQuestion = document.querySelector('.question-card:not(.hidden-question)');
    if (!activeQuestion) return;
    
    const questionIndex = parseInt(activeQuestion.dataset.questionIndex);
    const isLastQuestion = questionIndex === currentCase.questions.length - 1;
    
    // Process shortcuts
    switch (event.key) {
      case 'n':
      case 'ArrowRight':
        // Next question/submit shortcut (if text entered)
        const textarea = activeQuestion.querySelector('textarea');
        if (textarea && textarea.value.trim()) {
          const submitBtn = activeQuestion.querySelector('.submit-btn');
          if (submitBtn) submitBtn.click();
        }
        break;
        
      case 's':
        // Submit shortcut (if on last question and text entered)
        if (isLastQuestion) {
          const textarea = activeQuestion.querySelector('textarea');
          if (textarea && textarea.value.trim()) {
            const submitBtn = activeQuestion.querySelector('.submit-btn');
            if (submitBtn) submitBtn.click();
          }
        }
        break;
    }
  }
});