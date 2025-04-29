/**
 * Authentication Module for MediQA
 * 
 * Handles login, signup, logout, and session management
 */

// API endpoints for authentication
const AUTH_ENDPOINTS = {
  SIGNUP: '/api/user/signup',
  LOGIN: '/api/user/login',
  LOGOUT: '/api/user/logout',
  VALIDATE: '/api/user/validate'
};

/**
 * Shows the login modal
 */
function showLoginModal() {
  console.log('Showing login modal');
  const modal = document.getElementById('auth-modal');
  if (modal) {
    modal.style.display = 'block';
    
    // Set active tab to login
    const loginTab = document.querySelector('[data-tab="login"]');
    const loginForm = document.getElementById('login-form');
    
    if (loginTab && loginForm) {
      document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
      });
      loginTab.classList.add('active');
      
      document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
      });
      loginForm.classList.add('active');
    }
    
    // Focus on email input
    const emailInput = document.getElementById('login-email');
    if (emailInput) {
      emailInput.focus();
    }
  }
}

/**
 * Shows the signup modal
 */
function showSignupModal() {
  console.log('Showing signup modal');
  const modal = document.getElementById('auth-modal');
  if (modal) {
    modal.style.display = 'block';
    
    // Set active tab to signup
    const signupTab = document.querySelector('[data-tab="signup"]');
    const signupForm = document.getElementById('signup-form');
    
    if (signupTab && signupForm) {
      document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
      });
      signupTab.classList.add('active');
      
      document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
      });
      signupForm.classList.add('active');
    }
    
    // Focus on username input
    const usernameInput = document.getElementById('signup-username');
    if (usernameInput) {
      usernameInput.focus();
    }
  }
}

/**
 * Attempt to login with the provided credentials
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise} - Resolves when login is successful
 */
async function login(email, password) {
  try {
    console.log('Login attempt with email:', email);
    
    // Basic validation
    if (!email || !password) {
      showToast('Error', 'Email and password are required', 'error');
      return;
    }
    
    // Disable login button to prevent multiple submissions
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
      loginBtn.disabled = true;
      loginBtn.innerText = 'Logging in...';
    }
    
    // Call login API
    const response = await fetch(AUTH_ENDPOINTS.LOGIN, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password }),
      credentials: 'same-origin'
    });
    
    // Parse response
    const data = await response.json();
    console.log('Login response:', data);
    
    // Re-enable login button
    if (loginBtn) {
      loginBtn.disabled = false;
      loginBtn.innerText = 'Login';
    }
    
    // Handle success or failure
    if (data.success) {
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Show success message
      showToast('Success', data.message || 'Logged in successfully!', 'success');
      
      // Close the modal
      const modal = document.getElementById('auth-modal');
      if (modal) {
        modal.style.display = 'none';
      }
      
      // Show the navigation tabs
      const navTabs = document.getElementById('nav-tabs');
      if (navTabs) {
        navTabs.style.display = 'flex';
      }
      
      // Update user info in the UI
      initUserSession();
      
      // Redirect to dashboard from landing page
      if (window.location.pathname === '/') {
        window.location.href = '/dashboard';
      }
    } else {
      // Show error message
      showToast('Error', data.error || 'Login failed', 'error');
      
      // Log additional details for debugging
      console.error('Login failed:', data.error);
    }
  } catch (error) {
    console.error('Login error:', error);
    showToast('Error', 'An error occurred during login. Please try again.', 'error');
    
    // Re-enable login button
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
      loginBtn.disabled = false;
      loginBtn.innerText = 'Login';
    }
  }
}

/**
 * Attempt to sign up with the provided information
 * 
 * @param {string} username - Desired username
 * @param {string} email - User's email address
 * @param {string} password - User's desired password
 * @returns {Promise} - Resolves when signup is successful
 */
async function signup(username, email, password) {
  try {
    console.log('Signup attempt with:', { username, email });
    
    // Basic validation
    if (!username || !email || !password) {
      showToast('Error', 'All fields are required', 'error');
      return;
    }
    
    if (password.length < 6) {
      showToast('Error', 'Password must be at least 6 characters', 'error');
      return;
    }
    
    // Disable signup button to prevent multiple submissions
    const signupBtn = document.getElementById('signup-btn');
    if (signupBtn) {
      signupBtn.disabled = true;
      signupBtn.innerText = 'Creating account...';
    }
    
    // Call signup API
    const response = await fetch(AUTH_ENDPOINTS.SIGNUP, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, email, password }),
      credentials: 'same-origin'
    });
    
    // Parse response
    const data = await response.json();
    console.log('Signup response:', data);
    
    // Re-enable signup button
    if (signupBtn) {
      signupBtn.disabled = false;
      signupBtn.innerText = 'Sign Up';
    }
    
    // Handle success or failure
    if (data.success) {
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Show success message
      showToast('Success', data.message || 'Account created successfully!', 'success');
      
      // Close the modal
      const modal = document.getElementById('auth-modal');
      if (modal) {
        modal.style.display = 'none';
      }
      
      // Show the navigation tabs
      const navTabs = document.getElementById('nav-tabs');
      if (navTabs) {
        navTabs.style.display = 'flex';
      }
      
      // Update user info in the UI
      initUserSession();
      
      // Redirect to dashboard from landing page
      if (window.location.pathname === '/') {
        window.location.href = '/dashboard';
      }
    } else {
      // Show error message
      showToast('Error', data.error || 'Signup failed', 'error');
      
      // Log additional details for debugging
      console.error('Signup failed:', data.error);
    }
  } catch (error) {
    console.error('Signup error:', error);
    showToast('Error', 'An error occurred during signup. Please try again.', 'error');
    
    // Re-enable signup button
    const signupBtn = document.getElementById('signup-btn');
    if (signupBtn) {
      signupBtn.disabled = false;
      signupBtn.innerText = 'Sign Up';
    }
  }
}

/**
 * Log the user out
 * 
 * @returns {Promise} - Resolves when logout is successful
 */
async function logout() {
  try {
    console.log('Logging out...');
    
    // Call logout API
    const response = await fetch(AUTH_ENDPOINTS.LOGOUT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    });
    
    const data = await response.json();
    
    // Always clear localStorage regardless of response
    localStorage.removeItem('user');
    
    if (data.success) {
      showToast('Success', data.message || 'Logged out successfully!', 'success');
    } else {
      console.warn('Server-side logout had issues, but local session was cleared');
    }
    
    // Update UI
    initUserSession();
    
    // If on a restricted page, redirect to home
    const restrictedPages = ['/dashboard', '/chat', '/simulation', '/flashcards', '/leaderboard'];
    if (restrictedPages.includes(window.location.pathname)) {
      window.location.href = '/';
    }
  } catch (error) {
    console.error('Logout error:', error);
    
    // Still remove the user from localStorage in case of error
    localStorage.removeItem('user');
    showToast('Warning', 'Logged out locally, but server error occurred', 'warning');
    
    // If on a restricted page, redirect to home
    const restrictedPages = ['/dashboard', '/chat', '/simulation', '/flashcards', '/leaderboard'];
    if (restrictedPages.includes(window.location.pathname)) {
      window.location.href = '/';
    }
  }
}

/**
 * Check if the user is logged in
 * 
 * @returns {boolean} - True if the user is logged in, false otherwise
 */
function isLoggedIn() {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return false;
    
    const user = JSON.parse(userStr);
    return user && user.id;
  } catch (error) {
    console.error('Error checking login status:', error);
    localStorage.removeItem('user');
    return false;
  }
}

/**
 * Get user ID from localStorage
 * 
 * @returns {number|null} - User ID or null if not logged in
 */
function getUserId() {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    
    const user = JSON.parse(userStr);
    return user ? user.id : null;
  } catch (error) {
    console.error('Error getting user ID:', error);
    localStorage.removeItem('user');
    return null;
  }
}

/**
 * Validate the user's session with the server
 * 
 * @returns {Promise<boolean>} - Resolves to true if session is valid, false otherwise
 */
async function validateSession() {
  if (!isLoggedIn()) return false;
  
  try {
    const response = await fetch(AUTH_ENDPOINTS.VALIDATE, {
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
  } catch (error) {
    console.error('Session validation error:', error);
    
    // Clear session data on error
    localStorage.removeItem('user');
    return false;
  }
}

/**
 * Initialize the auth modal event listeners
 */
function initAuthModal() {
  console.log('Initializing auth modal');
  
  // Set up auth tabs
  const authTabs = document.querySelectorAll('.auth-tab');
  authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabType = tab.dataset.tab;
      
      // Update active tab
      authTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // Show corresponding form
      const authForms = document.querySelectorAll('.auth-form');
      authForms.forEach(form => {
        form.classList.toggle('active', form.id === `${tabType}-form`);
      });
    });
  });
  
  // Modal close button
  const closeButton = document.querySelector('#auth-modal .close');
  if (closeButton) {
    closeButton.addEventListener('click', () => {
      document.getElementById('auth-modal').style.display = 'none';
    });
  }
  
  // Click outside to close
  window.addEventListener('click', (event) => {
    const modal = document.getElementById('auth-modal');
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
  
  // Login form submission
  const loginBtn = document.getElementById('login-btn');
  if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
      console.log('Login button clicked');
      const email = document.getElementById('login-email').value;
      const password = document.getElementById('login-password').value;
      await login(email, password);
    });
  }
  
  // Signup form submission
  const signupBtn = document.getElementById('signup-btn');
  if (signupBtn) {
    signupBtn.addEventListener('click', async () => {
      console.log('Signup button clicked');
      const username = document.getElementById('signup-username').value;
      const email = document.getElementById('signup-email').value;
      const password = document.getElementById('signup-password').value;
      await signup(username, email, password);
    });
  }
  
  // Handle enter key in both forms
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    const loginInputs = loginForm.querySelectorAll('input');
    loginInputs.forEach(input => {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          loginBtn.click();
        }
      });
    });
  }
  
  const signupForm = document.getElementById('signup-form');
  if (signupForm) {
    const signupInputs = signupForm.querySelectorAll('input');
    signupInputs.forEach(input => {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          signupBtn.click();
        }
      });
    });
  }
}

// Export functions for use in other modules
window.authModule = {
  showLoginModal,
  showSignupModal,
  login,
  signup,
  logout,
  isLoggedIn,
  getUserId,
  validateSession,
  initAuthModal
};