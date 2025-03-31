document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearButton = document.getElementById('clear-button');
    const categoryFilters = document.getElementById('category-filters');
    
    let messages = [];
    let currentFilters = {};
    
    // Initialize with empty message
    appendMessage('bot', 'Hello! I am your finance assistant. How can I help you today?');
    
    // Load categories and display as filters
    loadCategories();
    
    // Event listeners
    sendButton.addEventListener('click', () => handleUserInput());
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleUserInput();
        }
    });
    
    clearButton.addEventListener('click', () => {
        messages = [];
        chatContainer.innerHTML = '';
        appendMessage('bot', 'Chat cleared. How can I help you today?');
        currentFilters = {};
        updateCategoryFilterUI();
    });
    
    function handleUserInput() {
        const text = userInput.value.trim();
        if (!text) return;
        
        appendMessage('user', text);
        userInput.value = '';
        
        // Show typing indicator
        typingIndicator.style.display = 'block';
        
        // Call API with user message and any active filters
        sendMessageToAPI(text, currentFilters);
    }
    
    function appendMessage(sender, text, data = null) {
        messages.push({ sender, text, data });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Add avatar icon
        const avatarSpan = document.createElement('span');
        avatarSpan.className = 'avatar';
        avatarSpan.textContent = sender === 'user' ? '👤' : '🤖';
        messageDiv.appendChild(avatarSpan);
        
        // Add message content in a container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Format the message with markdown
        const formattedText = formatMessage(text);
        contentDiv.innerHTML = formattedText;
        
        // Add any additional data visualization if provided
        if (data) {
            const dataVisual = createDataVisualization(data);
            if (dataVisual) {
                contentDiv.appendChild(dataVisual);
            }
        }
        
        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function formatMessage(text) {
        // Basic markdown-like formatting
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        
        // Detect and format URLs
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, url => {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
        
        return formatted;
    }
    
    function createDataVisualization(data) {
        // Create visualizations based on data type
        // This is a placeholder for more complex visualizations
        if (!data) return null;
        
        const container = document.createElement('div');
        container.className = 'data-visualization';
        
        // Example: Show key-value pairs for object data
        if (typeof data === 'object' && !Array.isArray(data)) {
            const table = document.createElement('table');
            table.className = 'data-table';
            
            for (const [key, value] of Object.entries(data)) {
                const row = document.createElement('tr');
                
                const keyCell = document.createElement('td');
                keyCell.className = 'key-cell';
                keyCell.textContent = key;
                
                const valueCell = document.createElement('td');
                valueCell.className = 'value-cell';
                valueCell.textContent = JSON.stringify(value);
                
                row.appendChild(keyCell);
                row.appendChild(valueCell);
                table.appendChild(row);
            }
            
            container.appendChild(table);
            return container;
        }
        
        return null;
    }
    
    async function sendMessageToAPI(text, filters = {}) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: text,
                    filters: filters,
                    history: messages.map(m => ({
                        role: m.sender === 'user' ? 'user' : 'assistant',
                        content: m.text
                    }))
                }),
            });
            
            if (!response.ok) {
                throw new Error('API request failed');
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            typingIndicator.style.display = 'none';
            
            // Display bot response
            appendMessage('bot', data.response, data.data);
            
            // Update any knowledge graph elements if included
            if (data.knowledge_graph) {
                updateKnowledgeGraphDisplay(data.knowledge_graph);
            }
            
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            appendMessage('bot', 'Sorry, I encountered an error while processing your request.');
        }
    }
    
    function updateKnowledgeGraphDisplay(graphData) {
        // Placeholder for knowledge graph visualization
        console.log('Knowledge graph data:', graphData);
        // In a real implementation, this would update a visual graph
    }
    
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
    
    function createCategoryFilters(categories) {
        categoryFilters.innerHTML = '<h3>Filter by Category</h3>';
        
        categories.forEach(category => {
            const filterItem = document.createElement('div');
            filterItem.className = 'filter-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${category.name}`;
            checkbox.dataset.category = category.name;
            
            const label = document.createElement('label');
            label.htmlFor = `filter-${category.name}`;
            label.innerHTML = `${category.name} <span class="count">(${category.count})</span>`;
            
            if (category.description) {
                const tooltip = document.createElement('span');
                tooltip.className = 'tooltip';
                tooltip.textContent = category.description;
                label.appendChild(tooltip);
            }
            
            checkbox.addEventListener('change', (e) => {
                const categoryName = e.target.dataset.category;
                if (e.target.checked) {
                    currentFilters[categoryName] = true;
                } else {
                    delete currentFilters[categoryName];
                }
                updateCategoryFilterUI();
            });
            
            filterItem.appendChild(checkbox);
            filterItem.appendChild(label);
            categoryFilters.appendChild(filterItem);
        });
        
        // Add "Clear Filters" button
        const clearFiltersBtn = document.createElement('button');
        clearFiltersBtn.textContent = 'Clear Filters';
        clearFiltersBtn.className = 'clear-filters-btn';
        clearFiltersBtn.addEventListener('click', () => {
            currentFilters = {};
            updateCategoryFilterUI();
        });
        
        categoryFilters.appendChild(clearFiltersBtn);
    }
    
    function updateCategoryFilterUI() {
        // Update checkboxes to match current filters
        document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(checkbox => {
            const category = checkbox.dataset.category;
            checkbox.checked = !!currentFilters[category];
        });
        
        // Show active filters count
        const activeFiltersCount = Object.keys(currentFilters).length;
        const filterLabel = document.querySelector('#category-filters h3');
        if (filterLabel) {
            filterLabel.textContent = activeFiltersCount > 0 
                ? `Filter by Category (${activeFiltersCount} active)` 
                : 'Filter by Category';
        }
    }
});

// Additional utility functions
function getFinancialCategories() {
    return fetch('/api/knowledge/categories')
        .then(response => response.json())
        .catch(error => {
            console.error('Error fetching categories:', error);
            return { categories: [] };
        });
} 