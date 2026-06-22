document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const pdfUpload = document.getElementById('pdf-upload');
    
    // New elements for Answer Key feature
    const generateKeyBtn = document.getElementById('generate-key-btn');
    const qpaperUpload = document.getElementById('qpaper-upload');
    const reviewModal = document.getElementById('review-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const answerKeyTextarea = document.getElementById('answer-key-textarea');

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

    // Answer Key Logic
    generateKeyBtn.addEventListener('click', () => {
        qpaperUpload.click();
    });

    qpaperUpload.addEventListener('change', async () => {
        if (!qpaperUpload.files || qpaperUpload.files.length === 0) return;

        const file = qpaperUpload.files[0];
        const formData = new FormData();
        formData.append('file', file);

        appendMessage('assistant', `Processing Question Paper: ${file.name}... This might take a minute as I search the notes for every question.`);
        const typingId = showTypingIndicator();

        try {
            const response = await fetch('/generate_key', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            removeElement(typingId);

            if (response.ok) {
                appendMessage('assistant', `✅ Finished generating the answer key! Review it in the pop-up window.`);
                // Show modal and populate text
                answerKeyTextarea.value = data.response;
                reviewModal.classList.remove('hidden');
            } else {
                appendMessage('assistant', `❌ Error: ${data.response}`);
            }
        } catch (error) {
            console.error('Error generating key:', error);
            removeElement(typingId);
            appendMessage('assistant', '❌ Sorry, there was an error communicating with the server.');
        }

        qpaperUpload.value = '';
    });

    closeModalBtn.addEventListener('click', () => {
        reviewModal.classList.add('hidden');
    });

    downloadPdfBtn.addEventListener('click', async () => {
        const content = answerKeyTextarea.value;
        downloadPdfBtn.disabled = true;
        downloadPdfBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

        try {
            const response = await fetch('/download_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content })
            });

            if (response.ok) {
                // Get the blob from the response
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'Answer_Key.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                reviewModal.classList.add('hidden');
            } else {
                const data = await response.json();
                alert('Error creating PDF: ' + data.response);
            }
        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Failed to download PDF.');
        } finally {
            downloadPdfBtn.disabled = false;
            downloadPdfBtn.innerHTML = '<i class="fa-solid fa-download"></i> Download PDF';
        }
    });

    // Evaluate Answer Sheet Logic
    const evaluateBtn = document.getElementById('evaluate-btn');
    const answersheetUpload = document.getElementById('answersheet-upload');
    const strictnessSelect = document.getElementById('strictness-select');
    const evaluationModal = document.getElementById('evaluation-modal');
    const closeEvalModalBtn = document.getElementById('close-eval-modal-btn');
    const downloadEvalPdfBtn = document.getElementById('download-eval-pdf-btn');
    const evaluationTextarea = document.getElementById('evaluation-textarea');

    evaluateBtn.addEventListener('click', () => {
        const currentAnswerKey = answerKeyTextarea.value.trim();
        if (!currentAnswerKey) {
            alert("Please generate or provide an Answer Key first before evaluating.");
            return;
        }
        answersheetUpload.click();
    });

    answersheetUpload.addEventListener('change', async () => {
        if (!answersheetUpload.files || answersheetUpload.files.length === 0) return;

        const file = answersheetUpload.files[0];
        const strictness = strictnessSelect.value;
        const answerKey = answerKeyTextarea.value;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('answer_key', answerKey);
        formData.append('strictness', strictness);

        appendMessage('assistant', `Evaluating Answer Sheet: ${file.name} with ${strictness} strictness... This will take a moment.`);
        const typingId = showTypingIndicator();

        try {
            const response = await fetch('/evaluate_sheet', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            removeElement(typingId);

            if (response.ok) {
                appendMessage('assistant', `✅ Finished evaluating the answer sheet! Review the report in the pop-up window.`);
                evaluationTextarea.value = data.response;
                evaluationModal.classList.remove('hidden');
            } else {
                appendMessage('assistant', `❌ Error: ${data.response}`);
            }
        } catch (error) {
            console.error('Error evaluating sheet:', error);
            removeElement(typingId);
            appendMessage('assistant', '❌ Sorry, there was an error communicating with the server.');
        }

        answersheetUpload.value = '';
    });

    closeEvalModalBtn.addEventListener('click', () => {
        evaluationModal.classList.add('hidden');
    });

    downloadEvalPdfBtn.addEventListener('click', async () => {
        const content = evaluationTextarea.value;
        downloadEvalPdfBtn.disabled = true;
        downloadEvalPdfBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

        try {
            const response = await fetch('/download_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'Evaluation_Report.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                evaluationModal.classList.add('hidden');
            } else {
                const data = await response.json();
                alert('Error creating PDF: ' + data.response);
            }
        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Failed to download PDF.');
        } finally {
            downloadEvalPdfBtn.disabled = false;
            downloadEvalPdfBtn.innerHTML = '<i class="fa-solid fa-download"></i> Download PDF';
        }
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
