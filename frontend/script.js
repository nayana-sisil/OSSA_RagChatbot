document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const examModeToggle = document.getElementById('exam-mode-toggle');
    const suggestions = document.getElementById('suggestions');
    const userTemplate = document.getElementById('user-message-template');
    const assistantTemplate = document.getElementById('assistant-message-template');

    const API_URL = 'http://localhost:8000/ask';

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Send on Enter
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    sendBtn.addEventListener('click', handleSendMessage);

    // Suggestions click
    suggestions.addEventListener('click', (e) => {
        if (e.target.classList.contains('suggestion-btn')) {
            userInput.value = e.target.innerText;
            handleSendMessage();
        }
    });

    async function handleSendMessage() {
        const question = userInput.value.trim();
        if (!question) return;

        // Clear input field and reset height
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add user's message to the UI immediately
        addMessageToUI('user', question);

        // Display typing indicator while waiting for API response
        const typingIndicator = addTypingIndicator();
        
        try {
            const isExamMode = examModeToggle.checked;
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    exam_mode: isExamMode
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            
            // Remove the typing indicator and render the AI response
            typingIndicator.remove();
            addMessageToUI('assistant', data.answer, data.sources);

        } catch (error) {
            console.error('Error:', error);
            typingIndicator.remove();
            addMessageToUI('assistant', 'Sorry, I encountered an error connecting to my knowledge base. Please ensure the backend server is running.', []);
        }
    }

    function addMessageToUI(sender, text, sources = []) {
        const template = sender === 'user' ? userTemplate : assistantTemplate;
        const clone = template.content.cloneNode(true);
        
        const bubble = clone.querySelector('.message-bubble');
        
        if (sender === 'assistant') {
            bubble.innerHTML = parseMarkdown(text);
        } else {
            bubble.innerText = text;
        }

        if (sender === 'assistant' && sources.length > 0) {
            const sourcesContainer = clone.querySelector('.message-sources');
            sources.forEach(source => {
                const tag = document.createElement('span');
                tag.className = 'source-tag';
                tag.innerHTML = `<i class="far fa-file-pdf"></i> ${source.file} (p. ${source.page})`;
                sourcesContainer.appendChild(tag);
            });
        }

        chatContainer.appendChild(clone);
        scrollToBottom();
    }

    function parseMarkdown(text) {
        // Simple regex-based Markdown parser
        let html = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold: **text**
            .replace(/\*(.*?)\*/g, '<em>$1</em>')             // Italic: *text*
            .replace(/\n/g, '<br>');                          // New lines

        // Handle simple bullet points
        html = html.replace(/^\* (.*?)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

        return html;
    }

    function addTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message assistant typing';
        div.innerHTML = `
            <div class="message-icon"><i class="fas fa-robot"></i></div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                </div>
            </div>
        `;
        chatContainer.appendChild(div);
        scrollToBottom();
        return div;
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
