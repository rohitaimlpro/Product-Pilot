const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("send-btn");
const userQuery = document.getElementById("user-query");
const userEmail = document.getElementById("user-email");
const statusDiv = document.getElementById("status");
const emptyState = document.getElementById("empty-state");
const typingIndicator = document.getElementById("typing-indicator");

// ── Inline formatting (bold, italic, code) ──────────────────────────
function inline(text) {
    // Bold first so ** doesn't get caught by italic regex
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic: single * not adjacent to another *
    text = text.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    return text;
}

// ── Table builder ────────────────────────────────────────────────────
function buildTable(rows) {
    const isSeparator = row => /^\|[\s\-:|]+\|/.test(row);
    let html = '<div class="table-wrapper"><table>';
    let headerDone = false;

    for (let j = 0; j < rows.length; j++) {
        if (isSeparator(rows[j])) {
            html += '</thead><tbody>';
            headerDone = true;
            continue;
        }

        const cells = rows[j].split('|').slice(1, -1).map(c => c.trim());

        if (!headerDone) {
            html += j === 0 ? '<thead><tr>' : '<tr>';
            cells.forEach(c => { html += `<th>${inline(c)}</th>`; });
            html += '</tr>';
        } else {
            html += '<tr>';
            cells.forEach(c => { html += `<td>${inline(c)}</td>`; });
            html += '</tr>';
        }
    }

    if (!headerDone) html += '</thead>';
    html += '</tbody></table></div>';
    return html;
}

// ── Main formatter (block-level parsing) ────────────────────────────
function formatText(text) {
    const lines = text.split('\n');
    let html = '';
    let i = 0;

    while (i < lines.length) {
        const trimmed = lines[i].trim();

        if (!trimmed) { i++; continue; }

        // H3
        if (trimmed.startsWith('### ')) {
            html += `<h3>${inline(trimmed.slice(4))}</h3>`;
            i++; continue;
        }

        // H4
        if (trimmed.startsWith('#### ')) {
            html += `<h4>${inline(trimmed.slice(5))}</h4>`;
            i++; continue;
        }

        // HR
        if (trimmed === '---') {
            html += '<hr>';
            i++; continue;
        }

        // Markdown table
        if (trimmed.startsWith('|')) {
            const rows = [];
            while (i < lines.length && lines[i].trim().startsWith('|')) {
                rows.push(lines[i].trim());
                i++;
            }
            html += buildTable(rows);
            continue;
        }

        // Unordered list (* or -)
        if (/^[*-]\s/.test(trimmed)) {
            html += '<ul>';
            while (i < lines.length && /^\s*[*-]\s/.test(lines[i])) {
                const item = lines[i].trim().replace(/^[*-]\s/, '');
                html += `<li>${inline(item)}</li>`;
                i++;
            }
            html += '</ul>';
            continue;
        }

        // Ordered list (1. 2. 3.)
        if (/^\d+\.\s/.test(trimmed)) {
            html += '<ol>';
            while (i < lines.length && /^\s*\d+\.\s/.test(lines[i])) {
                const item = lines[i].trim().replace(/^\d+\.\s/, '');
                html += `<li>${inline(item)}</li>`;
                i++;
            }
            html += '</ol>';
            continue;
        }

        // Regular paragraph
        html += `<p>${inline(trimmed)}</p>`;
        i++;
    }

    return html;
}

function needsFormatting(message) {
    return message.includes('###') ||
           message.includes('**') ||
           message.includes('* ') ||
           message.includes('- ') ||
           message.includes('|') ||
           /^\d+\.\s/m.test(message);
}

// ── Chat UI helpers ──────────────────────────────────────────────────
function addMessage(message, sender) {
    if (emptyState.style.display !== 'none') {
        emptyState.style.display = 'none';
    }

    const msgDiv = document.createElement("div");
    msgDiv.classList.add("chat-message", sender);

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("message-content");

    if (sender === 'bot' && needsFormatting(message)) {
        contentDiv.classList.add("formatted");
        contentDiv.innerHTML = formatText(message);
    } else {
        contentDiv.innerText = message;
    }

    msgDiv.appendChild(contentDiv);
    chatBox.insertBefore(msgDiv, typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showStatus(message, type) {
    statusDiv.className = 'status ' + type;
    statusDiv.innerText = message;
    statusDiv.style.display = 'block';
}

function hideStatus() {
    statusDiv.style.display = 'none';
}

function setSendButtonState(enabled) {
    sendBtn.disabled = !enabled;
    sendBtn.innerHTML = enabled
        ? '<span class="button-text">Get Recommendations</span>'
        : '<span class="button-text">Processing...</span>';
}

function showTypingIndicator(show) {
    if (show) {
        typingIndicator.classList.add('active');
        chatBox.scrollTop = chatBox.scrollHeight;
    } else {
        typingIndicator.classList.remove('active');
    }
}

// ── Main query handler ───────────────────────────────────────────────
async function handleSendQuery() {
    const query = userQuery.value.trim();
    const email = userEmail.value.trim();

    if (!query) {
        showStatus("Please enter a query.", "error");
        return;
    }

    addMessage(query, "user");
    userQuery.value = "";
    setSendButtonState(false);
    showTypingIndicator(true);
    showStatus("Analyzing products... this takes about 60 seconds.", "processing");

    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, email })
        });

        const data = await response.json();
        showTypingIndicator(false);

        if (data.success) {
            addMessage(data.recommendation, "bot");
            showStatus("Recommendation ready!", "success");
        } else {
            showStatus("Failed to get recommendation. Please try again.", "error");
        }
    } catch (err) {
        console.error("Error:", err);
        showTypingIndicator(false);
        showStatus("Error occurred. Please try again.", "error");
    } finally {
        setSendButtonState(true);
    }
}

// ── Event listeners ──────────────────────────────────────────────────
sendBtn.addEventListener("click", handleSendQuery);

userQuery.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

userQuery.addEventListener("input", function () {
    if (statusDiv.classList.contains('error')) hideStatus();
});
