document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearButton = document.getElementById('clear-button');
    const categoryFilters = document.getElementById('category-filters');
    
    let messages = [];
    let currentFilters = {};
    
    // Initialize with welcome message
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
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = sender === 'bot' ? '🤖' : '👤';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = formatMessage(text);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        // Only display data visualization if there's relevant data to show
        if (data && Object.keys(data).length > 0 && data.price) {
            const dataDiv = document.createElement('div');
            dataDiv.className = 'data-visualization';
            dataDiv.innerHTML = createDataVisualization(data);
            messageDiv.appendChild(dataDiv);
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Hide typing indicator
        typingIndicator.style.display = 'none';
    }
    
    function formatMessage(text) {
        // Convert newlines to <br> tags
        return text.replace(/\n/g, '<br>');
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
                    session_id: 'default'
                }),
            });
            
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }
            
            const data = await response.json();
            
            appendMessage('bot', data.response, data.additional_data);
            
            // Update knowledge graph if available
            if (data.knowledge_graph) {
                updateKnowledgeGraphDisplay(data.knowledge_graph);
            }
        } catch (error) {
            console.error('Error:', error);
            appendMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
    }
    
    function updateKnowledgeGraphDisplay(graphData) {
        // Implementation for knowledge graph visualization
        console.log('Knowledge graph data:', graphData);
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

function createDataVisualization(data) {
    if (!data) return '';
    
    // Financial data visualization for stocks and crypto
    if (data.price || data.symbol) {
        let html = '<div class="financial-data">';
        
        // Price section
        html += `<div class="price-section">
            <span class="current-price">$${parseFloat(data.price).toFixed(2)}</span>
            <span class="change-percent ${parseFloat(data.change_percent) >= 0 ? 'positive' : 'negative'}">
                ${parseFloat(data.change_percent) >= 0 ? '▲' : '▼'} ${Math.abs(parseFloat(data.change_percent)).toFixed(2)}%
            </span>
        </div>`;
        
        // Details section
        html += '<div class="details-section">';
        
        if (data.volume) {
            html += `<div class="data-row"><span class="label">Volume</span><span class="value">${Number(data.volume).toLocaleString()}</span></div>`;
        }
        
        if (data.high_24h) {
            html += `<div class="data-row"><span class="label">24h High</span><span class="value">$${parseFloat(data.high_24h).toFixed(2)}</span></div>`;
        }
        
        if (data.low_24h) {
            html += `<div class="data-row"><span class="label">24h Low</span><span class="value">$${parseFloat(data.low_24h).toFixed(2)}</span></div>`;
        }
        
        if (data.market_cap) {
            html += `<div class="data-row"><span class="label">Market Cap</span><span class="value">$${Number(data.market_cap).toLocaleString()}</span></div>`;
        }
        
        html += '</div>';
        html += '</div>';
        return html;
    }
    
    // Generic data table for other data types
    let html = '<table class="data-table">';
    for (const [key, value] of Object.entries(data)) {
        if (key !== 'type' && typeof value !== 'object') {
            html += `
                <tr>
                    <td class="key-cell">${key}</td>
                    <td class="value-cell">${value}</td>
                </tr>
            `;
        }
    }
    html += '</table>';
    return html;
} 