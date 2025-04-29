// Flashcards functionality
document.addEventListener('DOMContentLoaded', () => {
  const topicForm = document.getElementById('topic-form');
  const topicInput = document.getElementById('topic-input');
  const flashcardContainer = document.getElementById('flashcard-container');
  const flashcardElement = document.getElementById('flashcard');
  const questionElement = document.getElementById('flashcard-question');
  const answerElement = document.getElementById('flashcard-answer');
  const nextButton = document.getElementById('next-button');
  const prevButton = document.getElementById('prev-button');
  const ratingButtons = document.querySelectorAll('.rating-btn');
  const dueCardsButton = document.getElementById('due-cards-button');
  
  let currentFlashcards = [];
  let currentIndex = 0;
  let isFlipped = false;
  let isAnimating = false;
  
  // Initialize due cards button if it exists
  if (dueCardsButton) {
    dueCardsButton.addEventListener('click', loadDueCards);
    
    // Only enable due cards button if user is logged in
    if (typeof isLoggedIn === 'function' && !isLoggedIn()) {
      dueCardsButton.disabled = true;
      dueCardsButton.title = 'Login to access your due cards';
    }
  }
  
  // Add event listener to topic form
  if (topicForm) {
    topicForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const topic = topicInput.value.trim();
      if (!topic) {
        showToast('Error', 'Please enter a medical topic', 'error');
        return;
      }
      
      await loadFlashcards(topic);
    });
  }
  
  // Add event listener to flashcard for flipping
  if (flashcardElement) {
    flashcardElement.addEventListener('click', () => {
      if (currentFlashcards.length === 0 || isAnimating) return;
      
      toggleFlashcard();
      
      // Haptic feedback
      if (typeof hapticFeedback === 'function') {
        hapticFeedback();
      }
    });
  }
  
  // Add event listeners to navigation buttons
  if (nextButton) {
    nextButton.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent flashcard from flipping
      
      if (currentFlashcards.length === 0 || isAnimating) return;
      
      goToNextCard();
      
      // Haptic feedback
      if (typeof hapticFeedback === 'function') {
        hapticFeedback();
      }
    });
  }
  
  if (prevButton) {
    prevButton.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent flashcard from flipping
      
      if (currentFlashcards.length === 0 || isAnimating) return;
      
      goToPrevCard();
      
      // Haptic feedback
      if (typeof hapticFeedback === 'function') {
        hapticFeedback();
      }
    });
  }
  
  // Add event listeners to rating buttons
  if (ratingButtons) {
    ratingButtons.forEach(button => {
      button.addEventListener('click', async (e) => {
        e.stopPropagation(); // Prevent flashcard from flipping
        
        if (currentFlashcards.length === 0 || isAnimating) return;
        
        const rating = parseInt(button.dataset.rating);
        await rateFlashcard(rating);
        
        // Go to next card
        goToNextCard();
        
        // Haptic feedback
        if (typeof hapticFeedback === 'function') {
          hapticFeedback();
        }
      });
    });
  }
  
  // Load popular medical topics
  loadPopularTopics();
});

async function loadFlashcards(topic) {
  const flashcardContainer = document.getElementById('flashcard-container');
  const questionElement = document.getElementById('flashcard-question');
  const answerElement = document.getElementById('flashcard-answer');
  const flashcardElement = document.getElementById('flashcard');
  
  // Reset state
  currentIndex = 0;
  isFlipped = false;
  isAnimating = false;
  
  // Show loading state
  flashcardContainer.innerHTML = '';
  flashcardContainer.appendChild(createSkeletonLoader('card'));
  
  try {
    const response = await fetch(API_ENDPOINTS.FLASHCARDS_TOPIC, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ topic })
    });
    
    const data = await response.json();
    
    // Remove loading state
    flashcardContainer.innerHTML = '';
    
    if (data.error) {
      showToast('Error', data.error, 'error');
      return;
    }
    
    if (data.flashcards && data.flashcards.length > 0) {
      window.currentFlashcards = data.flashcards; // Make it global for debugging
      currentFlashcards = data.flashcards;
      
      // Show flashcard UI
      document.getElementById('flashcard-section').style.display = 'block';
      
      // Update flashcard content
      updateFlashcardContent();
      
      // Reset flashcard state
      if (flashcardElement.classList.contains('flipped')) {
        flashcardElement.classList.remove('flipped');
        isFlipped = false;
      }
      
      // Add entrance animation
      flashcardElement.style.opacity = '0';
      flashcardElement.style.transform = 'scale(0.9)';
      
      setTimeout(() => {
        flashcardElement.style.transition = 'opacity 0.5s, transform 0.5s';
        flashcardElement.style.opacity = '1';
        flashcardElement.style.transform = 'scale(1)';
      }, 10);
      
      showToast('Success', `Loaded ${data.flashcards.length} flashcards on ${topic}`, 'success');
    } else {
      showToast('Error', 'No flashcards found for this topic', 'error');
    }
  } catch (error) {
    console.error('Load flashcards error:', error);
    showToast('Error', 'Failed to load flashcards', 'error');
  }
}

async function loadDueCards() {
  if (typeof isLoggedIn === 'function' && !isLoggedIn()) {
    showToast('Error', 'Please log in to view your due cards', 'error');
    return;
  }
  
  const flashcardContainer = document.getElementById('flashcard-container');
  
  // Reset state
  currentIndex = 0;
  isFlipped = false;
  isAnimating = false;
  
  // Show loading state
  flashcardContainer.innerHTML = '';
  flashcardContainer.appendChild(createSkeletonLoader('card'));
  
  try {
    const response = await fetch(API_ENDPOINTS.FLASHCARDS_DUE);
    const data = await response.json();
    
    // Remove loading state
    flashcardContainer.innerHTML = '';
    
    if (data.error) {
      showToast('Error', data.error, 'error');
      return;
    }
    
    if (data.flashcards && data.flashcards.length > 0) {
      currentFlashcards = data.flashcards;
      
      // Show flashcard UI
      document.getElementById('flashcard-section').style.display = 'block';
      
      // Update flashcard content
      updateFlashcardContent();
      
      // Reset flashcard state
      const flashcardElement = document.getElementById('flashcard');
      if (flashcardElement.classList.contains('flipped')) {
        flashcardElement.classList.remove('flipped');
        isFlipped = false;
      }
      
      showToast('Success', `Loaded ${data.flashcards.length} cards due for review`, 'success');
    } else {
      showToast('Info', 'No cards due for review at the moment', 'info');
    }
  } catch (error) {
    console.error('Load due cards error:', error);
    showToast('Error', 'Failed to load due cards', 'error');
  }
}

function updateFlashcardContent() {
  if (currentFlashcards.length === 0) return;
  
  const questionElement = document.getElementById('flashcard-question');
  const answerElement = document.getElementById('flashcard-answer');
  const counterElement = document.getElementById('flashcard-counter');
  
  const currentCard = currentFlashcards[currentIndex];
  
  // Update content
  questionElement.textContent = currentCard.question;
  answerElement.textContent = currentCard.answer;
  
  // Update counter
  if (counterElement) {
    counterElement.textContent = `Card ${currentIndex + 1} of ${currentFlashcards.length}`;
  }
}

function toggleFlashcard() {
  const flashcardElement = document.getElementById('flashcard');
  
  if (isAnimating) return;
  isAnimating = true;
  
  isFlipped = !isFlipped;
  
  // Add or remove flipped class with animation
  if (isFlipped) {
    flashcardElement.classList.add('flipped');
    
    // Add sound effect if possible
    const flipSound = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-quick-jump-arcade-game-239.mp3');
    try {
      flipSound.volume = 0.3;
      flipSound.play().catch(e => console.log('Could not play sound', e));
    } catch (e) {
      console.log('Sound play error', e);
    }
  } else {
    flashcardElement.classList.remove('flipped');
  }
  
  // Reset animation lock after animation completes
  setTimeout(() => {
    isAnimating = false;
  }, 600); // Match the CSS transition duration
}

function goToNextCard() {
  if (currentFlashcards.length === 0 || isAnimating) return;
  
  isAnimating = true;
  
  const flashcardElement = document.getElementById('flashcard');
  
  // Apply slide-out animation to the left
  flashcardElement.style.transition = 'transform 0.3s, opacity 0.3s';
  flashcardElement.style.transform = 'translateX(-100%) scale(0.8)';
  flashcardElement.style.opacity = '0';
  
  // After slide-out animation completes, update content and slide in from right
  setTimeout(() => {
    // Update index
    currentIndex = (currentIndex + 1) % currentFlashcards.length;
    
    // Reset flipped state
    if (flashcardElement.classList.contains('flipped')) {
      flashcardElement.classList.remove('flipped');
      isFlipped = false;
    }
    
    // Update content
    updateFlashcardContent();
    
    // Position off-screen to the right (without animation)
    flashcardElement.style.transition = 'none';
    flashcardElement.style.transform = 'translateX(100%) scale(0.8)';
    
    // Force reflow to apply the position change
    void flashcardElement.offsetWidth;
    
    // Slide in from right with animation
    flashcardElement.style.transition = 'transform 0.3s, opacity 0.3s';
    flashcardElement.style.transform = 'translateX(0) scale(1)';
    flashcardElement.style.opacity = '1';
    
    // Reset animation lock after slide-in completes
    setTimeout(() => {
      isAnimating = false;
    }, 300);
  }, 300);
}

function goToPrevCard() {
  if (currentFlashcards.length === 0 || isAnimating) return;
  
  isAnimating = true;
  
  const flashcardElement = document.getElementById('flashcard');
  
  // Apply slide-out animation to the right
  flashcardElement.style.transition = 'transform 0.3s, opacity 0.3s';
  flashcardElement.style.transform = 'translateX(100%) scale(0.8)';
  flashcardElement.style.opacity = '0';
  
  // After slide-out animation completes, update content and slide in from left
  setTimeout(() => {
    // Update index
    currentIndex = (currentIndex - 1 + currentFlashcards.length) % currentFlashcards.length;
    
    // Reset flipped state
    if (flashcardElement.classList.contains('flipped')) {
      flashcardElement.classList.remove('flipped');
      isFlipped = false;
    }
    
    // Update content
    updateFlashcardContent();
    
    // Position off-screen to the left (without animation)
    flashcardElement.style.transition = 'none';
    flashcardElement.style.transform = 'translateX(-100%) scale(0.8)';
    
    // Force reflow to apply the position change
    void flashcardElement.offsetWidth;
    
    // Slide in from left with animation
    flashcardElement.style.transition = 'transform 0.3s, opacity 0.3s';
    flashcardElement.style.transform = 'translateX(0) scale(1)';
    flashcardElement.style.opacity = '1';
    
    // Reset animation lock after slide-in completes
    setTimeout(() => {
      isAnimating = false;
    }, 300);
  }, 300);
}

async function rateFlashcard(quality) {
  if (!isLoggedIn()) {
    showToast('Error', 'Please log in to save your progress', 'error');
    return;
  }
  
  if (currentFlashcards.length === 0) return;
  
  const currentCard = currentFlashcards[currentIndex];
  
  try {
    const response = await fetch(API_ENDPOINTS.FLASHCARDS_REVIEW, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        flashcard_id: currentCard.id,
        quality: quality
      })
    });
    
    const data = await response.json();
    
    if (data.error) {
      showToast('Error', data.error, 'error');
      return;
    }
    
    // Show review feedback
    let reviewMessage = "Reviewed! ";
    
    if (data.interval === 1) {
      reviewMessage += "You'll see this card again soon.";
    } else {
      reviewMessage += `Next review in ${data.interval} days.`;
    }
    
    showToast('Success', reviewMessage, 'success');
    
    // Award points animation
    showPointsAnimation(5);
  } catch (error) {
    console.error('Rate flashcard error:', error);
    showToast('Error', 'Failed to save your review', 'error');
  }
}

function loadPopularTopics() {
  const topicsContainer = document.getElementById('popular-topics');
  
  if (!topicsContainer) return;
  
  const popularTopics = [
    'Hypertension', 'Diabetes', 'Malaria', 
    'Asthma', 'HIV/AIDS', 'Tuberculosis', 
    'Pneumonia', 'Diarrhea', 'Anemia', 
    'Sickle Cell Disease'
  ];
  
  topicsContainer.innerHTML = '<h3>Popular Topics</h3>';
  
  const topicsList = document.createElement('div');
  topicsList.className = 'topics-list';
  
  popularTopics.forEach(topic => {
    const topicButton = document.createElement('button');
    topicButton.className = 'btn btn-outline topic-btn';
    topicButton.textContent = topic;
    topicButton.addEventListener('click', async () => {
      document.getElementById('topic-input').value = topic;
      await loadFlashcards(topic);
    });
    
    topicsList.appendChild(topicButton);
  });
  
  topicsContainer.appendChild(topicsList);
}

function showPointsAnimation(points) {
  if (!isLoggedIn()) return;
  
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
