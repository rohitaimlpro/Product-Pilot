// DOM Elements
const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("send-btn");
const userQuery = document.getElementById("user-query");
const userEmail = document.getElementById("user-email");
const statusDiv = document.getElementById("status");
const emptyState = document.getElementById("empty-state");
const typingIndicator = document.getElementById("typing-indicator");

/**
 * Format markdown-like text to HTML
 * @param {string} text - The text to format
 * @returns {string} - Formatted HTML
 */
function formatText(text) {
    // Convert ### headers to h3
    text = text.replace(/###\s+(.+)/g, '<h3>$1</h3>');
    
    // Convert #### headers to h4
    text = text.replace(/####\s+(.+)/g, '<h4>$1</h4>');
    
    // Convert **bold** to strong
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to em
    text = text.replace(/\*(.+?)\*\*/g, '<em>$1</em>');
    
    // Convert --- to hr
    text = text.replace(/^---$/gm, '<hr>');
    
    // Convert bullet points
    text = text.replace(/^\* (.+)/gm, '<li>$1</li>');
    
    // Wrap consecutive <li> in <ul>
    text = text.replace(/(<li>.*?<\/li>\s*)+/gs, '<ul>$&</ul>');
    
    // Convert line breaks to paragraphs
    const lines = text.split('\n');
    let formatted = '';
    let inParagraph = false;
    
    for (let line of lines) {
        line = line.trim();
        
        if (line.startsWith('<h3>') || line.startsWith('<h4>') || 
            line.startsWith('<ul>') || line.startsWith('<hr>') || line === '') {
            if (inParagraph) {
                formatted += '</p>';
                inParagraph = false;
            }
            formatted += line + '\n';
        } else if (line.startsWith('<li>') || line.startsWith('</ul>')) {
            formatted += line + '\n';
        } else {
            if (!inParagraph && line !== '') {
                formatted += '<p>';
                inParagraph = true;
            }
            formatted += line + ' ';
        }
    }
    
    if (inParagraph) {
        formatted += '</p>';
    }
    
    return formatted;
}

/**
 * Check if message needs formatting
 * @param {string} message - The message text
 * @returns {boolean} - Whether message contains markdown
 */
function needsFormatting(message) {
    return message.includes('###') || 
           message.includes('####') || 
           message.includes('**') || 
           message.includes('* ') ||
           message.includes('---');
}

/**
 * Add a message to the chat box
 * @param {string} message - The message text
 * @param {string} sender - Either 'user' or 'bot'
 */
function addMessage(message, sender) {
    // Hide empty state if it's visible
    if (emptyState.style.display !== 'none') {
        emptyState.style.display = 'none';
    }

    // Create message elements
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("chat-message", sender);
    
    const contentDiv = document.createElement("div");
    contentDiv.classList.add("message-content");
    
    // Format bot messages if they contain markdown
    if (sender === 'bot' && needsFormatting(message)) {
        contentDiv.classList.add("formatted");
        contentDiv.innerHTML = formatText(message);
    } else {
        contentDiv.innerText = message;
    }
    
    msgDiv.appendChild(contentDiv);
    
    // Insert before typing indicator
    chatBox.insertBefore(msgDiv, typingIndicator);
    
    // Scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Show status message with appropriate styling
 * @param {string} message - The status message
 * @param {string} type - Status type: 'success', 'error', or 'processing'
 */
function showStatus(message, type) {
    statusDiv.className = 'status ' + type;
    statusDiv.innerText = message;
    statusDiv.style.display = 'block';
}

/**
 * Hide the status message
 */
function hideStatus() {
    statusDiv.style.display = 'none';
}

/**
 * Enable/disable the send button
 * @param {boolean} enabled - Whether the button should be enabled
 */
function setSendButtonState(enabled) {
    sendBtn.disabled = !enabled;
    sendBtn.innerHTML = enabled 
        ? '<span class="button-text">Get Recommendations</span>'
        : '<span class="button-text">Processing...</span>';
}

/**
 * Show/hide typing indicator
 * @param {boolean} show - Whether to show the indicator
 */
function showTypingIndicator(show) {
    if (show) {
        typingIndicator.classList.add('active');
        chatBox.scrollTop = chatBox.scrollHeight;
    } else {
        typingIndicator.classList.remove('active');
    }
}

/**
 * Handle sending the query to the backend
 */
async function handleSendQuery() {
    const query = userQuery.value.trim();
    const email = userEmail.value.trim();

    // Validate input
    if (!query) {
        showStatus("Please enter a query.", "error");
        return;
    }

    // Add user message to chat
    addMessage(query, "user");
    userQuery.value = "";
    
    // Update UI state
    setSendButtonState(false);
    showTypingIndicator(true);
    showStatus("Processing your request...", "processing");

    try {
        // Make API request
        const response = await fetch("/api/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: query, email: email })
        });

        const data = await response.json();
        showTypingIndicator(false);

        // Handle response
        if (data.success) {
            addMessage(data.recommendation, "bot");
            
            if (email) {
                showStatus("✓ Recommendation sent to " + email + "!", "success");
            } else {
                showStatus("✓ Recommendation generated successfully!", "success");
            }
        } else {
            showStatus("Failed to get recommendation. Please try again.", "error");
        }

    } catch (err) {
        console.error("Error processing query:", err);
        showTypingIndicator(false);
        showStatus("Error occurred while processing. Please try again.", "error");
    } finally {
        // Re-enable send button
        setSendButtonState(true);
    }
}

// Event Listeners
sendBtn.addEventListener("click", handleSendQuery);

// Allow Enter to send (Shift+Enter for new line)
userQuery.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// Optional: Clear status message when user starts typing
userQuery.addEventListener("input", function() {
    if (statusDiv.classList.contains('error')) {
        hideStatus();
    }
});