// Constants
const API_ENDPOINTS = {
  CHAT: '/api/chat',
  SIMULATION_NEW: '/api/simulation/new',
  SIMULATION_SUBMIT: '/api/simulation/submit',
  CHALLENGE_DAILY: '/api/challenge/daily',
  CHALLENGE_REGENERATE: '/api/challenge/regenerate',
  CHALLENGE_GET: '/api/challenge/',
  CHALLENGE_SUBMIT: '/api/challenge/submit',
  FLASHCARDS_TOPIC: '/api/flashcards/topic',
  FLASHCARDS_REVIEW: '/api/flashcards/review',
  FLASHCARDS_DUE: '/api/flashcards/due',
  LEADERBOARD: '/api/leaderboard',
  USER_STATS: '/api/user/stats',
  SEARCH: '/api/search'
};

// Tab Navigation
document.addEventListener('DOMContentLoaded', () => {
  // Initialize tab navigation
  const tabItems = document.querySelectorAll('.tab-item');
  
  tabItems.forEach(item => {
    item.addEventListener('click', () => {
      // Get the target page from the data attribute
      const targetPage = item.dataset.target;
      
      // Navigate to the target page
      if (targetPage) {
        window.location.href = targetPage;
      }
    });
  });
  
  // Set active tab based on current page
  const currentPath = window.location.pathname;
  tabItems.forEach(item => {
    const targetPath = item.dataset.target;
    if (currentPath === targetPath) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
  
  // Initialize user session
  initUserSession();
  
  // Initialize toast container
  if (!document.querySelector('.toast-container')) {
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
});

// User Session Management
function initUserSession() {
  const userInfo = document.getElementById('user-info');
  
  if (userInfo) {
    if (window.authModule && window.authModule.isLoggedIn()) {
      // Get user data from localStorage
      const userStr = localStorage.getItem('user');
      if (!userStr) return;
      
      try {
        const userData = JSON.parse(userStr);
        
        // Update user info in UI - with profile icon, username and dropdown
        userInfo.innerHTML = `
          <div class="user-profile" id="profile-trigger">
            <i data-feather="user" class="profile-icon"></i>
            <span>${userData.username}</span>
            <i data-feather="chevron-down" class="profile-icon" style="width: 14px; height: 14px;"></i>
          </div>
          <div class="profile-dropdown" id="profile-dropdown">
            <a href="/dashboard" class="dropdown-item">
              <i data-feather="user"></i>
              Account
            </a>
            <a href="#" class="dropdown-item">
              <i data-feather="settings"></i>
              Settings
            </a>
            <div class="dropdown-divider"></div>
            <a href="#" class="dropdown-item danger" id="logout-dropdown-btn">
              <i data-feather="log-out"></i>
              Logout
            </a>
          </div>
        `;
        
        // Render feather icons
        if (window.feather) {
          feather.replace();
        }
        
        // Initialize profile dropdown
        initProfileDropdown();
        
        // Show tab bar navigation for logged in users
        const navTabs = document.getElementById('nav-tabs');
        if (navTabs) {
          navTabs.style.display = 'flex';
        }
      } catch (e) {
        console.error('Error parsing user data:', e);
        localStorage.removeItem('user');
        
        // Show login button
        showLoginButton();
      }
    } else {
      // User is not logged in, show login button
      showLoginButton();
    }
  }
}

// Initialize profile dropdown functionality
function initProfileDropdown() {
  const profileTrigger = document.getElementById('profile-trigger');
  const profileDropdown = document.getElementById('profile-dropdown');
  const logoutBtn = document.getElementById('logout-dropdown-btn');
  
  if (profileTrigger && profileDropdown) {
    // Toggle dropdown on profile click
    profileTrigger.addEventListener('click', function(e) {
      e.stopPropagation();
      profileDropdown.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
      profileDropdown.classList.remove('show');
    });
    
    // Prevent dropdown from closing when clicking inside
    profileDropdown.addEventListener('click', function(e) {
      e.stopPropagation();
    });
    
    // Logout functionality
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (window.authModule) {
          window.authModule.logout();
        }
      });
    }
  }
}

// Helper function to show login button in user info area
function showLoginButton() {
  const userInfo = document.getElementById('user-info');
  if (userInfo) {
    userInfo.innerHTML = `
      <button id="header-login-btn" class="btn btn-primary btn-sm">Login</button>
    `;
    
    const loginBtn = document.getElementById('header-login-btn');
    if (loginBtn) {
      loginBtn.addEventListener('click', () => {
        if (window.authModule) {
          window.authModule.showLoginModal();
        }
      });
    }
  }
}

// Helper functions
function showToast(title, message, type = 'info') {
  const toastContainer = document.querySelector('.toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  // Set icon based on type
  let icon = 'info-circle';
  if (type === 'success') icon = 'check-circle';
  if (type === 'error') icon = 'x-circle';
  if (type === 'warning') icon = 'alert-triangle';
  
  toast.innerHTML = `
    <div class="toast-icon">
      <i data-feather="${icon}"></i>
    </div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close">
      <i data-feather="x"></i>
    </button>
  `;
  
  toastContainer.appendChild(toast);
  
  // Initialize Feather icons in the toast
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Add click event to close button
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    toastContainer.removeChild(toast);
  });
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (toast.parentNode === toastContainer) {
      toastContainer.removeChild(toast);
    }
  }, 5000);
}

function createSkeletonLoader(type, count = 1) {
  const container = document.createElement('div');
  
  for (let i = 0; i < count; i++) {
    const skeleton = document.createElement('div');
    
    if (type === 'card') {
      skeleton.className = 'skeleton skeleton-card';
    } else if (type === 'text') {
      skeleton.className = 'skeleton skeleton-text';
    } else if (type === 'circle') {
      skeleton.className = 'skeleton skeleton-circle';
    } else if (type === 'button') {
      skeleton.className = 'skeleton skeleton-button';
    }
    
    container.appendChild(skeleton);
  }
  
  return container;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Initialize components when the UI loads
function initComponents() {
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Initialize tooltips (if using Bootstrap)
  if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
      new bootstrap.Tooltip(tooltip);
    });
  }
}

// Add animation to elements
function animateElement(element, animationClass) {
  element.classList.add(animationClass);
  element.addEventListener('animationend', () => {
    element.classList.remove(animationClass);
  });
}

// Add haptic feedback simulation
function hapticFeedback() {
  if ('vibrate' in navigator) {
    navigator.vibrate(50);
  }
}

// Function to check if user is logged in
function isLoggedIn() {
  const user = localStorage.getItem('user');
  if (!user) return false;
  
  try {
    // Check if the stored user data is valid JSON
    const userData = JSON.parse(user);
    return userData && userData.id; // Ensure user has an ID property
  } catch (e) {
    console.error('Invalid user data in localStorage:', e);
    // Clean up invalid data
    localStorage.removeItem('user');
    return false;
  }
}

// Function to get user ID
function getUserId() {
  try {
    const user = localStorage.getItem('user');
    if (user) {
      const userData = JSON.parse(user);
      return userData.id;
    }
  } catch (e) {
    console.error('Error getting user ID:', e);
    localStorage.removeItem('user'); // Clean up invalid data
  }
  return null;
}

// Function to validate user session with server
async function validateSession() {
  // Use the auth module if available
  if (window.authModule && window.authModule.validateSession) {
    return window.authModule.validateSession();
  }
  
  // Fallback implementation if auth module is not available
  if (!isLoggedIn()) return false;
  
  try {
    const response = await fetch('/api/user/validate', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    });
    
    if (!response.ok) {
      // Clear invalid session data
      localStorage.removeItem('user');
      return false;
    }
    
    const data = await response.json();
    return data.valid === true;
  } catch (e) {
    console.error('Session validation error:', e);
    // On error, clear local session data to be safe
    localStorage.removeItem('user');
    return false;
  }
}
