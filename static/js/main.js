document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const pdfUpload = document.getElementById('pdf-upload');

    // Prevent submitting empty messages
    userInput.addEventListener('input', () => {
        sendBtn.disabled = userInput.value.trim() === '';
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to UI
        appendMessage('user', message);
        
        // Clear input
        userInput.value = '';
        sendBtn.disabled = true;

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            // Send request to Flask backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeElement(typingId);

            // Add assistant message
            appendMessage('assistant', data.response);

        } catch (error) {
            console.error('Error:', error);
            removeElement(typingId);
            appendMessage('assistant', 'Sorry, there was an error communicating with the server.');
        }
    });

    clearBtn.addEventListener('click', () => {
        chatMessages.innerHTML = `
            <div class="message assistant">
                <div class="avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="content">Hello! I am the KTU Industrial Safety Assistant. Ask me a question about your notes!</div>
            </div>
        `;
    });

    // Trigger file input when upload button is clicked
    uploadBtn.addEventListener('click', () => {
        pdfUpload.click();
    });

    // Handle file selection and upload
    pdfUpload.addEventListener('change', async () => {
        if (!pdfUpload.files || pdfUpload.files.length === 0) return;

        const files = pdfUpload.files;
        const formData = new FormData();
        
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        // Show parsing message
        appendMessage('assistant', `Uploading and processing ${files.length} PDF(s)... Please wait.`);
        const typingId = showTypingIndicator();

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            removeElement(typingId);
            
            if (response.ok) {
                appendMessage('assistant', `✅ ${data.response}`);
            } else {
                appendMessage('assistant', `❌ ${data.response}`);
            }

        } catch (error) {
            console.error('Error uploading:', error);
            removeElement(typingId);
            appendMessage('assistant', '❌ Sorry, there was an error uploading the files.');
        }

        // Reset the input
        pdfUpload.value = '';
    });

    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const iconClass = role === 'user' ? 'fa-user' : 'fa-robot';
        
        // Basic markdown-to-html for line breaks (since gemini returns text with newlines)
        const formattedContent = content.replace(/\n/g, '<br>');

        messageDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${iconClass}"></i></div>
            <div class="content">${formattedContent}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = id;
        
        typingDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
