// Gamification functionality
document.addEventListener('DOMContentLoaded', () => {
  // Check and update streak on page load if logged in
  if (isLoggedIn()) {
    updateUserStreak();
  }
});

// Update user streak
async function updateUserStreak() {
  const streakElement = document.getElementById('user-streak');
  
  if (!streakElement) return;
  
  try {
    // Triggering the streak update happens automatically on the server
    // when any authenticated endpoint is accessed
    
    // Check user stats to get updated streak
    const response = await fetch(API_ENDPOINTS.USER_STATS);
    const data = await response.json();
    
    if (data.error) {
      console.error('Error updating streak:', data.error);
      return;
    }
    
    // Update UI with streak information
    if (data.streak > 0) {
      streakElement.textContent = data.streak;
      
      // Update streak in local storage
      const user = JSON.parse(localStorage.getItem('user'));
      if (user) {
        user.streak = data.streak;
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      // If streak just reached a milestone, show celebration
      const milestones = [3, 7, 14, 30, 60, 100, 365];
      if (milestones.includes(data.streak)) {
        celebrateStreakMilestone(data.streak);
      }
    }
  } catch (error) {
    console.error('Error updating streak:', error);
  }
}

// Generate confetti effect
function createConfetti() {
  // Only create if the DOM is ready
  if (document.readyState !== 'complete') return;
  
  const confettiContainer = document.createElement('div');
  confettiContainer.className = 'confetti-container';
  confettiContainer.style.position = 'fixed';
  confettiContainer.style.top = '0';
  confettiContainer.style.left = '0';
  confettiContainer.style.width = '100%';
  confettiContainer.style.height = '100%';
  confettiContainer.style.pointerEvents = 'none';
  confettiContainer.style.zIndex = '9999';
  
  document.body.appendChild(confettiContainer);
  
  // Create 100 confetti pieces
  for (let i = 0; i < 100; i++) {
    const confetti = document.createElement('div');
    
    // Random color
    const colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c'];
    const color = colors[Math.floor(Math.random() * colors.length)];
    
    // Random size
    const size = Math.random() * 10 + 5;
    
    // Random position
    const posX = Math.random() * 100;
    
    // Set styles
    confetti.style.position = 'absolute';
    confetti.style.width = `${size}px`;
    confetti.style.height = `${size}px`;
    confetti.style.backgroundColor = color;
    confetti.style.borderRadius = '50%';
    confetti.style.left = `${posX}%`;
    confetti.style.top = '0';
    confetti.style.opacity = '1';
    
    // Add to container
    confettiContainer.appendChild(confetti);
    
    // Animate falling
    const duration = Math.random() * 3 + 2;
    const delay = Math.random() * 2;
    
    confetti.animate(
      [
        { transform: 'translateY(0) rotate(0)', opacity: 1 },
        { transform: `translateY(${window.innerHeight}px) rotate(${Math.random() * 360}deg)`, opacity: 0 }
      ],
      {
        duration: duration * 1000,
        delay: delay * 1000,
        easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
        iterations: 1,
        fill: 'forwards'
      }
    );
  }
  
  // Remove container after animations complete
  setTimeout(() => {
    if (confettiContainer.parentNode) {
      document.body.removeChild(confettiContainer);
    }
  }, 6000);
}

// Celebrate streak milestone
function celebrateStreakMilestone(streak) {
  // Create modal for celebration
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.style.display = 'flex';
  modal.style.position = 'fixed';
  modal.style.top = '0';
  modal.style.left = '0';
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
  modal.style.zIndex = '9998';
  modal.style.alignItems = 'center';
  modal.style.justifyContent = 'center';
  
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-content streak-celebration';
  modalContent.style.backgroundColor = 'white';
  modalContent.style.borderRadius = 'var(--border-radius)';
  modalContent.style.padding = '2rem';
  modalContent.style.maxWidth = '90%';
  modalContent.style.width = '400px';
  modalContent.style.textAlign = 'center';
  modalContent.style.position = 'relative';
  modalContent.style.animation = 'fadeIn 0.5s, pulse 2s infinite';
  
  const closeButton = document.createElement('button');
  closeButton.innerHTML = '&times;';
  closeButton.style.position = 'absolute';
  closeButton.style.top = '10px';
  closeButton.style.right = '10px';
  closeButton.style.border = 'none';
  closeButton.style.background = 'none';
  closeButton.style.fontSize = '1.5rem';
  closeButton.style.cursor = 'pointer';
  closeButton.style.color = '#777';
  
  closeButton.addEventListener('click', () => {
    document.body.removeChild(modal);
  });
  
  const icon = document.createElement('div');
  icon.innerHTML = '<i data-feather="award"></i>';
  icon.style.fontSize = '3rem';
  icon.style.color = 'var(--primary-color)';
  icon.style.marginBottom = '1rem';
  
  const title = document.createElement('h2');
  title.textContent = `${streak} Day Streak!`;
  title.style.marginBottom = '1rem';
  title.style.color = 'var(--primary-color)';
  
  const message = document.createElement('p');
  message.textContent = `Congratulations! You've maintained your learning streak for ${streak} days in a row. Keep up the great work!`;
  message.style.marginBottom = '1.5rem';
  
  const bonusPoints = streak * 5;
  
  const bonusMessage = document.createElement('p');
  bonusMessage.textContent = `Bonus: +${bonusPoints} points awarded!`;
  bonusMessage.style.fontWeight = 'bold';
  bonusMessage.style.color = 'var(--success-color)';
  
  const continueButton = document.createElement('button');
  continueButton.textContent = 'Continue Learning';
  continueButton.className = 'btn btn-primary';
  continueButton.style.marginTop = '1rem';
  
  continueButton.addEventListener('click', () => {
    document.body.removeChild(modal);
  });
  
  modalContent.appendChild(closeButton);
  modalContent.appendChild(icon);
  modalContent.appendChild(title);
  modalContent.appendChild(message);
  modalContent.appendChild(bonusMessage);
  modalContent.appendChild(continueButton);
  
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Show confetti
  createConfetti();
  
  // Play celebration sound
  playCelebrationSound();
  
  // Haptic feedback
  if ('vibrate' in navigator) {
    navigator.vibrate([100, 50, 100, 50, 100]);
  }
}

// Play celebration sound
function playCelebrationSound() {
  // Skip sound if audio API not available
  if (!window.AudioContext && !window.webkitAudioContext) {
    return;
  }
  
  // Create audio context
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioContext();
  
  // Create oscillator for a short jingle
  const playNote = (frequency, startTime, duration) => {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gainNode.gain.value = 0.1;
    
    oscillator.start(startTime);
    oscillator.stop(startTime + duration);
  };
  
  // Play a simple ascending melody
  const now = audioContext.currentTime;
  playNote(440, now, 0.1);      // A4
  playNote(554.37, now + 0.1, 0.1);  // C#5
  playNote(659.25, now + 0.2, 0.1);  // E5
  playNote(880, now + 0.3, 0.2);     // A5
}

// Award points animation
function showPointsAnimation(points, targetElement = null) {
  const pointsElement = document.createElement('div');
  pointsElement.className = 'points-animation';
  pointsElement.textContent = `+${points} points`;
  pointsElement.style.position = 'fixed';
  pointsElement.style.fontSize = '2rem';
  pointsElement.style.fontWeight = 'bold';
  pointsElement.style.color = '#2ecc71';
  pointsElement.style.zIndex = '9999';
  pointsElement.style.pointerEvents = 'none';
  
  // Position near target element if provided, otherwise center
  if (targetElement) {
    const rect = targetElement.getBoundingClientRect();
    pointsElement.style.top = `${rect.top - 20}px`;
    pointsElement.style.left = `${rect.left + rect.width / 2}px`;
    pointsElement.style.transform = 'translate(-50%, -50%)';
  } else {
    pointsElement.style.top = '50%';
    pointsElement.style.left = '50%';
    pointsElement.style.transform = 'translate(-50%, -50%)';
  }
  
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
  
  // Update user points in localstorage
  updateUserPoints(points);
  
  // Remove element after animation
  setTimeout(() => {
    document.body.removeChild(pointsElement);
  }, 1500);
}

// Update user points in localStorage
function updateUserPoints(pointsToAdd) {
  if (!isLoggedIn()) return;
  
  const user = JSON.parse(localStorage.getItem('user'));
  if (user) {
    user.points += pointsToAdd;
    localStorage.setItem('user', JSON.stringify(user));
    
    // Update points display if it exists
    const pointsDisplay = document.querySelector('#user-info .badge-primary');
    if (pointsDisplay) {
      pointsDisplay.textContent = `${user.points} pts`;
    }
  }
}

// Update achievement progress
function updateAchievementProgress(achievementId, progress, total) {
  const achievementElement = document.querySelector(`.achievement-item[data-id="${achievementId}"]`);
  
  if (!achievementElement) return;
  
  const progressBar = achievementElement.querySelector('.achievement-progress-bar');
  const progressText = achievementElement.querySelector('.achievement-progress-text');
  
  if (progressBar) {
    const percentage = Math.min(100, Math.round((progress / total) * 100));
    progressBar.style.width = `${percentage}%`;
  }
  
  if (progressText) {
    progressText.textContent = `${progress}/${total}`;
  }
}

// Unlock achievement animation
function showAchievementUnlocked(achievement) {
  const notification = document.createElement('div');
  notification.className = 'achievement-notification';
  notification.style.position = 'fixed';
  notification.style.bottom = '20px';
  notification.style.right = '20px';
  notification.style.backgroundColor = 'var(--card-background)';
  notification.style.borderRadius = 'var(--border-radius)';
  notification.style.boxShadow = 'var(--shadow)';
  notification.style.padding = '1rem';
  notification.style.zIndex = '9999';
  notification.style.display = 'flex';
  notification.style.alignItems = 'center';
  notification.style.maxWidth = '350px';
  notification.style.transform = 'translateX(400px)';
  notification.style.transition = 'transform 0.5s ease-out';
  
  const iconContainer = document.createElement('div');
  iconContainer.style.marginRight = '1rem';
  iconContainer.style.fontSize = '2rem';
  iconContainer.style.color = 'var(--primary-color)';
  iconContainer.innerHTML = `<i data-feather="${achievement.badge_icon}"></i>`;
  
  const contentContainer = document.createElement('div');
  contentContainer.style.flex = '1';
  
  const title = document.createElement('div');
  title.style.fontWeight = 'bold';
  title.style.marginBottom = '0.25rem';
  title.textContent = 'Achievement Unlocked!';
  
  const name = document.createElement('div');
  name.style.fontWeight = '500';
  name.style.marginBottom = '0.25rem';
  name.textContent = achievement.name;
  
  const description = document.createElement('div');
  description.style.fontSize = '0.875rem';
  description.style.color = 'var(--text-light)';
  description.textContent = achievement.description;
  
  const points = document.createElement('div');
  points.style.fontSize = '0.875rem';
  points.style.marginTop = '0.5rem';
  points.style.color = 'var(--success-color)';
  points.style.fontWeight = 'bold';
  points.textContent = `+${achievement.points} points`;
  
  contentContainer.appendChild(title);
  contentContainer.appendChild(name);
  contentContainer.appendChild(description);
  contentContainer.appendChild(points);
  
  notification.appendChild(iconContainer);
  notification.appendChild(contentContainer);
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 100);
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Play achievement sound
  playAchievementSound();
  
  // Haptic feedback
  if ('vibrate' in navigator) {
    navigator.vibrate([100, 50, 100]);
  }
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    notification.style.transform = 'translateX(400px)';
    
    // Remove from DOM after animation completes
    setTimeout(() => {
      if (notification.parentNode) {
        document.body.removeChild(notification);
      }
    }, 500);
  }, 5000);
}

// Play achievement unlock sound
function playAchievementSound() {
  // Skip sound if audio API not available
  if (!window.AudioContext && !window.webkitAudioContext) {
    return;
  }
  
  // Create audio context
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioContext();
  
  // Create oscillator for achievement sound
  const playNote = (frequency, startTime, duration) => {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gainNode.gain.value = 0.1;
    
    oscillator.start(startTime);
    oscillator.stop(startTime + duration);
  };
  
  // Play a simple achievement melody
  const now = audioContext.currentTime;
  playNote(587.33, now, 0.1);     // D5
  playNote(783.99, now + 0.1, 0.1); // G5
  playNote(1046.50, now + 0.2, 0.3); // C6
}
