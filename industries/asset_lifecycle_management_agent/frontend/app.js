// Predictive Maintenance Agent Frontend
class PredictiveMaintenanceUI {
    constructor() {
        this.apiUrl = localStorage.getItem('apiUrl') || 'http://localhost:8000';
        this.streamMode = localStorage.getItem('streamMode') || 'http';
        this.showIntermediate = false;
        this.isProcessing = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadSettings();
    }

    initializeElements() {
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsPanel = document.getElementById('settings-panel');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.statusIndicator = document.getElementById('status');
        this.showIntermediateCheckbox = document.getElementById('show-intermediate');
    }

    attachEventListeners() {
        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
            this.updateSendButton();
        });

        // Settings panel
        this.settingsBtn.addEventListener('click', () => {
            this.settingsPanel.classList.add('open');
        });

        this.closeSettingsBtn.addEventListener('click', () => {
            this.settingsPanel.classList.remove('open');
        });

        document.getElementById('save-settings').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('reset-settings').addEventListener('click', () => {
            this.resetSettings();
        });

        // Show intermediate steps toggle
        this.showIntermediateCheckbox.addEventListener('change', (e) => {
            this.showIntermediate = e.target.checked;
        });

        // Example prompts
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('example-prompt-btn')) {
                this.userInput.value = e.target.textContent;
                this.updateSendButton();
                this.userInput.focus();
            }
        });

        // Theme toggle
        document.getElementById('theme').addEventListener('change', (e) => {
            document.body.classList.toggle('light-theme', e.target.value === 'light');
        });
    }

    updateSendButton() {
        const hasText = this.userInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isProcessing;
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isProcessing) return;

        // Clear input
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        this.updateSendButton();

        // Remove welcome message if present
        const welcomeMsg = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        // Add user message
        this.addMessage('user', message);

        // Set processing state
        this.isProcessing = true;
        this.updateStatus('Processing...');

        // Add loading indicator
        const loadingId = this.addLoadingMessage();

        try {
            if (this.streamMode === 'http') {
                await this.sendHTTPStreamRequest(message, loadingId);
            } else {
                await this.sendWebSocketRequest(message, loadingId);
            }
        } catch (error) {
            console.error('Error:', error);
            this.removeMessage(loadingId);
            this.addMessage('assistant', `❌ Error: ${error.message}`);
            this.updateStatus('Error occurred');
        } finally {
            this.isProcessing = false;
            this.updateSendButton();
            this.updateStatus('Ready');
        }
    }

    async sendHTTPStreamRequest(message, loadingId) {
        const response = await fetch(`${this.apiUrl}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: [{ role: 'user', content: message }],
                stream: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Remove loading indicator
        this.removeMessage(loadingId);

        // Create assistant message container
        const assistantMsgId = this.addMessage('assistant', '');
        const messageContent = document.querySelector(`[data-message-id="${assistantMsgId}"] .message-content`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        
                        // Handle different response formats
                        if (parsed.choices && parsed.choices[0].delta.content) {
                            fullResponse += parsed.choices[0].delta.content;
                            messageContent.innerHTML = this.formatMessage(fullResponse);
                        } else if (parsed.content) {
                            fullResponse += parsed.content;
                            messageContent.innerHTML = this.formatMessage(fullResponse);
                        } else if (parsed.intermediate_step && this.showIntermediate) {
                            this.addIntermediateStep(assistantMsgId, parsed.intermediate_step);
                        } else if (parsed.type === 'tool_call' && this.showIntermediate) {
                            this.addIntermediateStep(assistantMsgId, `🔧 Tool: ${parsed.tool_name}`);
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e);
                    }
                }
            }

            this.scrollToBottom();
        }

        // Check for visualizations in the response
        this.detectAndRenderVisualizations(assistantMsgId, fullResponse);
    }

    async sendWebSocketRequest(message, loadingId) {
        // WebSocket implementation (placeholder for future enhancement)
        throw new Error('WebSocket mode not yet implemented. Please use HTTP Streaming.');
    }

    addMessage(role, content) {
        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.setAttribute('data-message-id', messageId);

        const roleLabel = role === 'user' ? '👤 You' : '🤖 Assistant';

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-role">${roleLabel}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageId;
    }

    addLoadingMessage() {
        const loadingId = `loading-${Date.now()}`;
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.setAttribute('data-message-id', loadingId);

        loadingDiv.innerHTML = `
            <div class="message-header">
                <span class="message-role">🤖 Assistant</span>
            </div>
            <div class="message-content">
                <div class="loading">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        `;

        this.messagesContainer.appendChild(loadingDiv);
        this.scrollToBottom();

        return loadingId;
    }

    addIntermediateStep(messageId, step) {
        const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
        if (!messageDiv) return;

        const contentDiv = messageDiv.querySelector('.message-content');
        const stepDiv = document.createElement('div');
        stepDiv.className = 'intermediate-step';
        stepDiv.textContent = step;

        contentDiv.insertBefore(stepDiv, contentDiv.firstChild);
        this.scrollToBottom();
    }

    removeMessage(messageId) {
        const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageDiv) {
            messageDiv.remove();
        }
    }

    formatMessage(content) {
        if (!content) return '';
        
        // Convert markdown-style formatting
        let formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        return formatted;
    }

    detectAndRenderVisualizations(messageId, content) {
        // Check for HTML file references (Plotly outputs)
        const htmlPattern = /(?:saved to|generated|created|output).*?['"]?([\w\/\-_]+\.html)['"]?/gi;
        const matches = [...content.matchAll(htmlPattern)];

        if (matches.length > 0) {
            const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
            const contentDiv = messageDiv.querySelector('.message-content');

            matches.forEach(match => {
                const filePath = match[1];
                const vizDiv = document.createElement('div');
                vizDiv.className = 'visualization-container';
                vizDiv.innerHTML = `
                    <iframe src="/output/${filePath}" frameborder="0"></iframe>
                    <div style="padding: 0.5rem; text-align: center; background: var(--bg-tertiary); border-top: 1px solid var(--border-color);">
                        <small>📊 Visualization: ${filePath}</small>
                    </div>
                `;
                contentDiv.appendChild(vizDiv);
            });

            this.scrollToBottom();
        }
    }

    updateStatus(status) {
        this.statusIndicator.textContent = status;
    }

    scrollToBottom() {
        if (document.getElementById('auto-scroll')?.checked !== false) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    loadSettings() {
        document.getElementById('api-url').value = this.apiUrl;
        document.getElementById('stream-mode').value = this.streamMode;
        
        const theme = localStorage.getItem('theme') || 'dark';
        document.getElementById('theme').value = theme;
        document.body.classList.toggle('light-theme', theme === 'light');
        
        const autoScroll = localStorage.getItem('autoScroll') !== 'false';
        document.getElementById('auto-scroll').checked = autoScroll;
    }

    saveSettings() {
        this.apiUrl = document.getElementById('api-url').value;
        this.streamMode = document.getElementById('stream-mode').value;
        const theme = document.getElementById('theme').value;
        const autoScroll = document.getElementById('auto-scroll').checked;

        localStorage.setItem('apiUrl', this.apiUrl);
        localStorage.setItem('streamMode', this.streamMode);
        localStorage.setItem('theme', theme);
        localStorage.setItem('autoScroll', autoScroll);

        this.settingsPanel.classList.remove('open');
        this.updateStatus('Settings saved');
    }

    resetSettings() {
        localStorage.clear();
        this.apiUrl = 'http://localhost:8000';
        this.streamMode = 'http';
        this.loadSettings();
        this.updateStatus('Settings reset');
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new PredictiveMaintenanceUI();
});

