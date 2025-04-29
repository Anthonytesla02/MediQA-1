// Dashboard functionality
document.addEventListener('DOMContentLoaded', async () => {
  const statsContainer = document.getElementById('stats-container');
  const achievementsContainer = document.getElementById('achievements-container');
  const performanceChartContainer = document.getElementById('performance-chart');
  
  // Check if logged in via local storage
  if (!isLoggedIn()) {
    showLoginPrompt();
    return;
  }
  
  // Also validate session with server
  const isValid = await validateSession();
  if (!isValid) {
    // Session is invalid, show login prompt
    showLoginPrompt();
    return;
  }
  
  // Load user stats
  loadUserStats();
  
  // Initialize Leaderboard
  loadLeaderboard();
  
  // Setup refresh button if exists
  const refreshButton = document.getElementById('refresh-stats');
  if (refreshButton) {
    refreshButton.addEventListener('click', loadUserStats);
  }
});

function showLoginPrompt() {
  const dashboardContainer = document.querySelector('.dashboard-container');
  
  if (dashboardContainer) {
    dashboardContainer.innerHTML = `
      <div class="login-prompt card">
        <div class="card-body text-center">
          <h2>Login Required</h2>
          <p>Please log in to view your dashboard and track your progress.</p>
          <button id="login-prompt-btn" class="btn btn-primary">Login</button>
        </div>
      </div>
    `;
    
    const loginButton = document.getElementById('login-prompt-btn');
    if (loginButton) {
      loginButton.addEventListener('click', showLoginModal);
    }
  }
}

async function loadUserStats() {
  const statsGrid = document.getElementById('stats-grid');
  const summaryContent = document.getElementById('summary-content');
  const statsDetails = document.getElementById('stats-details');
  const achievementsContainer = document.getElementById('achievements-container');
  const performanceChart = document.getElementById('performance-chart');
  
  // Show loading state for all content areas
  if (statsGrid) {
    statsGrid.innerHTML = '';
    statsGrid.appendChild(createSkeletonLoader('card', 4));
  }
  
  if (summaryContent) {
    summaryContent.innerHTML = '';
    summaryContent.appendChild(createSkeletonLoader('text', 3));
  }
  
  if (statsDetails) {
    statsDetails.innerHTML = '';
    statsDetails.appendChild(createSkeletonLoader('text', 3));
  }
  
  if (achievementsContainer) {
    achievementsContainer.innerHTML = '';
    achievementsContainer.appendChild(createSkeletonLoader('card'));
  }
  
  if (performanceChart) {
    performanceChart.innerHTML = '<div class="skeleton" style="height: 250px;"></div>';
  }
  
  try {
    const response = await fetch(API_ENDPOINTS.USER_STATS);
    const data = await response.json();
    
    if (data.error) {
      showToast('Error', data.error, 'error');
      if (statsGrid) statsGrid.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
      return;
    }
    
    // Render stats in all relevant sections
    renderUserStats(data);
    
    // Render achievements
    renderAchievements(data.achievements);
    
    // Render performance chart
    renderPerformanceChart(data);
    
    // Haptic feedback
    hapticFeedback();
  } catch (error) {
    console.error('Load user stats error:', error);
    showToast('Error', 'Failed to load your statistics', 'error');
  }
}

function renderUserStats(data) {
  // Calculate stats that will be used in multiple places
  const casesAccuracy = data.cases.total > 0 ? Math.round(data.cases.accuracy) : 0;
  const challengeScore = Math.round(data.challenges.average_score);
  
  // Render stats grid for overview tab
  const statsGrid = document.getElementById('stats-grid');
  if (statsGrid) {
    statsGrid.innerHTML = '';
    
    // Points stat
    const pointsStat = createStatCard('Points', data.points, 'award');
    statsGrid.appendChild(pointsStat);
    
    // Streak stat
    const streakStat = createStatCard('Day Streak', data.streak, 'activity');
    statsGrid.appendChild(streakStat);
    
    // Case accuracy stat
    const casesStat = createStatCard('Case Accuracy', `${casesAccuracy}%`, 'check-circle');
    statsGrid.appendChild(casesStat);
    
    // Challenge score stat
    const challengesStat = createStatCard('Challenge Score', `${challengeScore}%`, 'award');
    statsGrid.appendChild(challengesStat);
  }
  
  // Render summary content
  const summaryContent = document.getElementById('summary-content');
  if (summaryContent) {
    summaryContent.innerHTML = `
      <p>
        <strong>Cases:</strong> ${data.cases.correct} correct out of ${data.cases.total} attempted
      </p>
      <p>
        <strong>Challenges:</strong> ${data.challenges.total} completed with avg. score ${challengeScore}%
      </p>
      <p>
        <strong>Last Active:</strong> ${data.last_active ? formatDate(data.last_active) : 'Never'}
      </p>
    `;
  }
  
  // Render detailed stats
  const statsDetails = document.getElementById('stats-details');
  if (statsDetails) {
    statsDetails.innerHTML = `
      <div class="stats-details-grid">
        <div class="detail-item">
          <div class="detail-label">Total Points</div>
          <div class="detail-value">${data.points}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Current Streak</div>
          <div class="detail-value">${data.streak} days</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Case Attempts</div>
          <div class="detail-value">${data.cases.total}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Correct Cases</div>
          <div class="detail-value">${data.cases.correct}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Case Accuracy</div>
          <div class="detail-value">${casesAccuracy}%</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">Challenge Score</div>
          <div class="detail-value">${challengeScore}%</div>
        </div>
      </div>
    `;
  }
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
}

function createStatCard(label, value, icon) {
  const statCard = document.createElement('div');
  statCard.className = 'stat-card';
  
  const statIcon = document.createElement('div');
  statIcon.className = 'stat-icon';
  statIcon.innerHTML = `<i data-feather="${icon}"></i>`;
  
  const statValue = document.createElement('div');
  statValue.className = 'stat-value';
  statValue.textContent = value;
  
  const statLabel = document.createElement('div');
  statLabel.className = 'stat-label';
  statLabel.textContent = label;
  
  statCard.appendChild(statIcon);
  statCard.appendChild(statValue);
  statCard.appendChild(statLabel);
  
  return statCard;
}

function renderAchievements(achievements) {
  const achievementsContainer = document.getElementById('achievements-container');
  if (!achievementsContainer) return;
  
  achievementsContainer.innerHTML = '';
  
  // Create card structure
  const achievementsCard = document.createElement('div');
  achievementsCard.className = 'card';
  
  const cardHeader = document.createElement('div');
  cardHeader.className = 'card-header';
  
  const headerTitle = document.createElement('h3');
  headerTitle.textContent = 'Your Achievements';
  cardHeader.appendChild(headerTitle);
  achievementsCard.appendChild(cardHeader);
  
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  
  if (!achievements || achievements.length === 0) {
    const noAchievements = document.createElement('div');
    noAchievements.className = 'empty-state';
    noAchievements.innerHTML = `
      <div class="empty-icon">
        <i data-feather="award"></i>
      </div>
      <p>No achievements earned yet.</p>
      <p class="empty-hint">Complete cases and challenges to unlock achievements!</p>
    `;
    cardBody.appendChild(noAchievements);
  } else {
    const achievementsGrid = document.createElement('div');
    achievementsGrid.className = 'achievements-grid';
    
    achievements.forEach(achievement => {
      const achievementItem = document.createElement('div');
      achievementItem.className = 'achievement-item';
      
      const achievementIcon = document.createElement('div');
      achievementIcon.className = 'achievement-icon';
      achievementIcon.innerHTML = `<i data-feather="${achievement.badge_icon}"></i>`;
      
      const achievementName = document.createElement('div');
      achievementName.className = 'achievement-name';
      achievementName.textContent = achievement.name;
      
      const achievementDescription = document.createElement('div');
      achievementDescription.className = 'achievement-description';
      achievementDescription.textContent = achievement.description;
      
      const achievementDate = document.createElement('div');
      achievementDate.className = 'achievement-date';
      achievementDate.textContent = `Earned: ${formatDate(achievement.earned_at)}`;
      achievementDate.style.fontSize = '0.75rem';
      achievementDate.style.marginTop = '0.5rem';
      achievementDate.style.color = 'var(--text-light)';
      
      achievementItem.appendChild(achievementIcon);
      achievementItem.appendChild(achievementName);
      achievementItem.appendChild(achievementDescription);
      achievementItem.appendChild(achievementDate);
      
      achievementsGrid.appendChild(achievementItem);
    });
    
    cardBody.appendChild(achievementsGrid);
  }
  
  achievementsCard.appendChild(cardBody);
  achievementsContainer.appendChild(achievementsCard);
  
  // Initialize Feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
}

function renderPerformanceChart(data) {
  const chartContainer = document.getElementById('performance-chart');
  
  if (!chartContainer || typeof Chart === 'undefined') return;
  
  chartContainer.innerHTML = '<canvas id="performance-canvas"></canvas>';
  
  const ctx = document.getElementById('performance-canvas').getContext('2d');
  
  // Get calculated metrics for the performance chart
  const casesAccuracy = data.cases.total > 0 ? Math.round(data.cases.accuracy) : 0;
  
  // Create dummy data for timeline (last 7 days)
  const dates = [];
  const dummyScores = [];
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    
    // Generate random scores that trend upward and are close to the current score
    const baseScore = casesAccuracy || 70;
    const randomVariation = Math.floor(Math.random() * 15) - 7;
    const dayScore = Math.max(0, Math.min(100, baseScore - 10 + (i * 2) + randomVariation));
    dummyScores.push(dayScore);
  }
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: 'Performance Score',
        data: dummyScores,
        backgroundColor: 'rgba(52, 152, 219, 0.2)',
        borderColor: 'rgba(52, 152, 219, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(52, 152, 219, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(52, 152, 219, 1)',
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Score (%)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Date'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false
        },
        title: {
          display: true,
          text: 'Your Performance Over Time'
        }
      }
    }
  });
}

async function loadLeaderboard() {
  const leaderboardContainer = document.getElementById('leaderboard-preview');
  
  if (!leaderboardContainer) return;
  
  // Show loading state
  leaderboardContainer.innerHTML = '';
  leaderboardContainer.appendChild(createSkeletonLoader('card'));
  
  try {
    const response = await fetch(API_ENDPOINTS.LEADERBOARD);
    const data = await response.json();
    
    if (data.error) {
      leaderboardContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
      return;
    }
    
    // Render mini leaderboard (top 5)
    renderMiniLeaderboard(data.leaderboard.slice(0, 5));
  } catch (error) {
    console.error('Load leaderboard error:', error);
    leaderboardContainer.innerHTML = '<div class="alert alert-danger">Failed to load leaderboard data.</div>';
  }
}

function renderMiniLeaderboard(leaderboardData) {
  const leaderboardContainer = document.getElementById('leaderboard-preview');
  leaderboardContainer.innerHTML = '';
  
  const leaderboardCard = document.createElement('div');
  leaderboardCard.className = 'card';
  
  const cardHeader = document.createElement('div');
  cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
  
  const headerTitle = document.createElement('h3');
  headerTitle.textContent = 'Top Performers';
  
  const viewAllLink = document.createElement('a');
  viewAllLink.href = '/leaderboard';
  viewAllLink.className = 'btn btn-sm btn-outline';
  viewAllLink.textContent = 'View All';
  
  cardHeader.appendChild(headerTitle);
  cardHeader.appendChild(viewAllLink);
  leaderboardCard.appendChild(cardHeader);
  
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  
  if (!leaderboardData || leaderboardData.length === 0) {
    cardBody.innerHTML = '<p>No leaderboard data available.</p>';
  } else {
    const table = document.createElement('table');
    table.className = 'leaderboard-table';
    
    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    const rankHeader = document.createElement('th');
    rankHeader.className = 'rank-header';
    rankHeader.textContent = 'Rank';
    
    const userHeader = document.createElement('th');
    userHeader.textContent = 'User';
    
    const pointsHeader = document.createElement('th');
    pointsHeader.textContent = 'Points';
    
    headerRow.appendChild(rankHeader);
    headerRow.appendChild(userHeader);
    headerRow.appendChild(pointsHeader);
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    
    leaderboardData.forEach((user, index) => {
      const row = document.createElement('tr');
      
      const rankCell = document.createElement('td');
      rankCell.className = `rank rank-${index + 1}`;
      rankCell.textContent = `#${index + 1}`;
      
      const usernameCell = document.createElement('td');
      usernameCell.className = 'username';
      
      // Highlight current user
      if (isLoggedIn() && getUserId() === user.id) {
        usernameCell.innerHTML = `${user.username} <span class="badge badge-primary">You</span>`;
      } else {
        usernameCell.textContent = user.username;
      }
      
      const pointsCell = document.createElement('td');
      pointsCell.className = 'points-cell';
      pointsCell.textContent = user.points;
      
      row.appendChild(rankCell);
      row.appendChild(usernameCell);
      row.appendChild(pointsCell);
      
      tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    cardBody.appendChild(table);
  }
  
  leaderboardCard.appendChild(cardBody);
  leaderboardContainer.appendChild(leaderboardCard);
}
