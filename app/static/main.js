// Main JavaScript for Financial Chat Assistant

document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');

    // Function to add a message to the chat
    function addMessage(sender, text, additionalData = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Add header with icon
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = sender === 'user' ? '👤 You' : '🤖 AI Assistant';
        messageDiv.appendChild(headerDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function sendMessageToAPI(text) {
        try {
            // Add user message
            addMessage('user', text);
            
            // Add loading message
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot-message loading';
            loadingDiv.innerHTML = `
                <div class="message-header">🤖 AI Assistant</div>
                <div class="loading-dots"><span></span><span></span><span></span></div>
            `;
            chatContainer.appendChild(loadingDiv);
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: text,
                    session_id: 'default'
                }),
            });
            
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }
            
            const data = await response.json();
            
            // Remove loading message
            loadingDiv.remove();
            
            // Add bot response
            addMessage('bot', data.response, data.additional_data);
            
        } catch (error) {
            console.error('Error:', error);
            // Remove loading message if it exists
            const loadingMessage = document.querySelector('.loading');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            addMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            messageInput.value = '';
            await sendMessageToAPI(message);
        }
    });

    // Add greeting message when page loads
    addMessage('bot', "Hello! I'm your AI financial assistant. I can help with stock prices, crypto trends, mutual funds, investment advice, and more. What would you like to know?");

    async function loadCategories() {
        try {
            const response = await fetch('/api/knowledge_graph/categories');
            
            if (!response.ok) {
                throw new Error('Failed to load categories');
            }
            
            const data = await response.json();
            if (data.categories && Array.isArray(data.categories)) {
                createCategoryFilters(data.categories);
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }
}); 