// Chat interface
document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const sendButton = document.getElementById('send-button');
  
  // Add welcome message
  addBotMessage("Hello! I'm your medical assistant. Describe your symptoms or ask me any health-related questions, and I'll help you find information from the Ghana Standard Treatment Guidelines.");
  
  // Add event listener to chat form
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addUserMessage(message);
    
    // Clear input
    messageInput.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    // Send message to server
    try {
      const response = await fetch(API_ENDPOINTS.CHAT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: message })
      });
      
      const data = await response.json();
      
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      if (data.response) {
        // Add bot response to chat
        addBotMessage(data.response);
      } else {
        addBotMessage("I'm sorry, I couldn't process your request. Please try again.");
      }
    } catch (error) {
      console.error('Chat error:', error);
      
      // Remove typing indicator
      chatMessages.removeChild(typingIndicator);
      
      // Show error message
      addBotMessage("I'm sorry, there was an error processing your request. Please try again later.");
    }
    
    // Scroll to bottom
    scrollToBottom();
  });
  
  // Enable/disable send button based on input
  messageInput.addEventListener('input', () => {
    sendButton.disabled = messageInput.value.trim() === '';
  });
  
  // Initialize send button state
  sendButton.disabled = true;
});

function addUserMessage(message) {
  const messageElement = document.createElement('div');
  messageElement.className = 'message message-user';
  messageElement.textContent = message;
  document.getElementById('chat-messages').appendChild(messageElement);
  
  // Play send sound
  playSound('send');
  
  // Scroll to bottom
  scrollToBottom();
}

function addBotMessage(message) {
  const messageElement = document.createElement('div');
  messageElement.className = 'message message-bot';
  
  // Format message if it contains markdown-like formatting
  message = formatMarkdown(message);
  
  messageElement.innerHTML = message;
  document.getElementById('chat-messages').appendChild(messageElement);
  
  // Play receive sound
  playSound('receive');
  
  // Scroll to bottom
  scrollToBottom();
}

function addTypingIndicator() {
  const indicatorElement = document.createElement('div');
  indicatorElement.className = 'message message-bot typing-indicator';
  indicatorElement.innerHTML = '<span></span><span></span><span></span>';
  document.getElementById('chat-messages').appendChild(indicatorElement);
  
  // Scroll to bottom
  scrollToBottom();
  
  return indicatorElement;
}

function scrollToBottom() {
  const chatMessages = document.getElementById('chat-messages');
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMarkdown(text) {
  // Replace **text** with <strong>text</strong>
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Replace *text* with <em>text</em>
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Replace [text](url) with <a href="url">text</a>
  text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
  
  // Replace newlines with <br>
  text = text.replace(/\n/g, '<br>');
  
  return text;
}

function playSound(type) {
  // Skip sound if audio API not available
  if (!window.AudioContext && !window.webkitAudioContext) {
    return;
  }
  
  // Create audio context
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioContext();
  
  // Create oscillator
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  // Set sound properties based on type
  if (type === 'send') {
    oscillator.type = 'sine';
    oscillator.frequency.value = 600;
    gainNode.gain.value = 0.1;
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.1);
  } else if (type === 'receive') {
    oscillator.type = 'sine';
    oscillator.frequency.value = 440;
    gainNode.gain.value = 0.1;
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.1);
  }
}
