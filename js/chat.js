/**
 * =============================================
 * SAURABH AI - Chat Functionality
 * Core chat logic with streaming, stop, regenerate
 * =============================================
 */

const Chat = {
  // Current abort controller for stopping generation
  abortController: null,

  // Current streaming state
  isStreaming: false,

  // Message counter for IDs
  messageCounter: 0,

  // API base URL
  API_BASE: 'http://localhost:8000',

  /**
   * Initialize chat
   */
  init() {
    // Load current chat or create new
    let currentChatId = Storage.getCurrentChat();
    let currentChat = Storage.getChat(currentChatId);

    if (!currentChat) {
      currentChat = Storage.createChat();
    }

    // Render chat
    this.renderChat(currentChat);
    this.renderSidebar();

    // Set up event listeners
    this.setupEventListeners();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    const input = document.getElementById('msgInput');
    const sendBtn = document.getElementById('sendBtn');

    // Send on button click
    sendBtn.addEventListener('click', () => this.send());

    // Send on Enter (without Shift)
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 180) + 'px';
      this.updateSendButton();
    });
  },

  /**
   * Update send button state
   */
  updateSendButton() {
    const input = document.getElementById('msgInput');
    const sendBtn = document.getElementById('sendBtn');
    const hasText = input.value.trim().length > 0;
    sendBtn.classList.toggle('active', hasText && !this.isStreaming);
  },

  /**
   * Send message
   */
  async send() {
    const input = document.getElementById('msgInput');
    const message = input.value.trim();

    if (!message || this.isStreaming) return;

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Get current chat
    let currentChat = Storage.getChat(Storage.getCurrentChat());
    if (!currentChat) {
      currentChat = Storage.createChat();
    }

    // Add user message
    const userMessage = {
      id: Utils.generateId(),
      role: 'user',
      content: message,
      timestamp: Date.now()
    };
    Storage.addMessage(currentChat.id, userMessage);

    // Render user message
    this.renderMessage(userMessage, 'user');
    this.scrollToBottom();

    // Get AI response
    await this.getAIResponse(currentChat);

    // Update UI
    this.updateSendButton();
    this.renderSidebar();
  },

  /**
   * Get AI response with streaming
   * @param {Object} chat - Chat object
   */
  async getAIResponse(chat) {
    const messages = chat.messages.map(m => ({
      role: m.role,
      content: m.content
    }));

    // Add system prompt based on mode
    const mode = Storage.getSettings().selectedMode;
    const systemPrompt = Modes.getSystemPrompt(mode);
    if (systemPrompt) {
      messages.unshift({ role: 'system', content: systemPrompt });
    }

    // Create AI message placeholder
    const aiMessage = {
      id: Utils.generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now()
    };
    Storage.addMessage(chat.id, aiMessage);

    // Render AI message placeholder
    const messageEl = this.renderMessage(aiMessage, 'assistant', true);

    // Create abort controller
    this.abortController = new AbortController();
    this.isStreaming = true;
    this.updateStreamingUI(true);

    // Play sent sound
    Sounds.playMessageSent();

    // Start time tracking
    const startTime = Date.now();

    try {
      const response = await fetch(`${this.API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: Storage.getSettings().selectedModel || 'llama-3.3-70b-versatile',
          messages: messages,
          stream: true
        }),
        signal: this.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Process streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let tickCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              const token = parsed.choices?.[0]?.delta?.content || '';
              if (token) {
                fullContent += token;
                aiMessage.content = fullContent;
                
                // Update UI
                const contentEl = messageEl.querySelector('.message-content');
                if (contentEl) {
                  contentEl.innerHTML = this.formatMessage(fullContent) + '<span class="cursor"></span>';
                }

                // Play typing sound
                tickCount++;
                if (tickCount % 5 === 0) {
                  Sounds.playTypingTick();
                }
              }
            } catch (e) {
              // Ignore parse errors for partial chunks
            }
          }
        }
      }

      // Update final message
      aiMessage.content = fullContent;
      Storage.updateLastMessage(chat.id, aiMessage);

      // Update UI with final content
      const contentEl = messageEl.querySelector('.message-content');
      if (contentEl) {
        contentEl.innerHTML = this.formatMessage(fullContent);
        contentEl.innerHTML += this.renderMessageActions(aiMessage);
      }

      // Update stats
      const endTime = Date.now();
      const duration = ((endTime - startTime) / 1000).toFixed(1);
      this.updateMessageStats(messageEl, duration, Utils.estimateTokens(fullContent));

      // Play received sound
      Sounds.playMessageReceived();

    } catch (error) {
      if (error.name === 'AbortError') {
        // User stopped generation
        console.log('Generation stopped by user');
        aiMessage.content += '\n\n[Generation stopped]';
      } else {
        // Error occurred
        console.error('Error:', error);
        aiMessage.content = `Sorry, an error occurred: ${error.message}`;
      }

      // Update UI with error
      const contentEl = messageEl.querySelector('.message-content');
      if (contentEl) {
        contentEl.innerHTML = `<span class="error">${Utils.escapeHtml(aiMessage.content)}</span>`;
      }

      Sounds.playError();
    } finally {
      // Cleanup
      this.abortController = null;
      this.isStreaming = false;
      this.updateStreamingUI(false);
      this.scrollToBottom();
    }
  },

  /**
   * Stop generation
   */
  stopGeneration() {
    if (this.abortController) {
      this.abortController.abort();
    }
  },

  /**
   * Regenerate last message
   */
  async regenerate() {
    const currentChat = Storage.getChat(Storage.getCurrentChat());
    if (!currentChat || currentChat.messages.length < 2) return;

    // Remove last AI message
    if (currentChat.messages[currentChat.messages.length - 1].role === 'assistant') {
      currentChat.messages.pop();
      Storage.updateChat(currentChat.id, { messages: currentChat.messages });

      // Re-render chat
      this.renderChat(currentChat);

      // Get new AI response
      await this.getAIResponse(currentChat);
      this.renderSidebar();
    }
  },

  /**
   * Copy message to clipboard
   * @param {string} messageId - Message ID
   */
  async copyMessage(messageId) {
    const currentChat = Storage.getChat(Storage.getCurrentChat());
    const message = currentChat?.messages.find(m => m.id === messageId);
    if (message) {
      const success = await Utils.copyToClipboard(message.content);
      if (success) {
        Sounds.playSuccess();
        App.showToast('Copied to clipboard!', 'success');
      }
    }
  },

  /**
   * Delete message
   * @param {string} messageId - Message ID
   */
  deleteMessage(messageId) {
    const currentChat = Storage.getChat(Storage.getCurrentChat());
    if (!currentChat) return;

    currentChat.messages = currentChat.messages.filter(m => m.id !== messageId);
    Storage.updateChat(currentChat.id, { messages: currentChat.messages });
    this.renderChat(currentChat);
  },

  /**
   * Edit and resend message
   * @param {string} messageId - Message ID
   */
  editMessage(messageId) {
    const currentChat = Storage.getChat(Storage.getCurrentChat());
    const messageIndex = currentChat?.messages.findIndex(m => m.id === messageId);
    
    if (messageIndex === undefined || messageIndex === -1) return;

    const message = currentChat.messages[messageIndex];
    if (message.role !== 'user') return;

    // Remove this and all following messages
    currentChat.messages = currentChat.messages.slice(0, messageIndex);
    Storage.updateChat(currentChat.id, { messages: currentChat.messages });

    // Set input value
    const input = document.getElementById('msgInput');
    input.value = message.content;
    input.focus();

    // Re-render chat
    this.renderChat(currentChat);
    this.updateSendButton();
  },

  /**
   * Render message
   * @param {Object} message - Message object
   * @param {string} type - 'user' or 'assistant'
   * @param {boolean} isStreaming - Is streaming
   */
  renderMessage(message, type, isStreaming = false) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.dataset.id = message.id;

    if (type === 'assistant') {
      messageEl.innerHTML = `
        <div class="message-avatar">
          <div class="avatar">S</div>
        </div>
        <div class="message-body">
          <div class="message-header">
            <span class="message-sender">Saurabh AI</span>
            <span class="message-badge">${Modes.getName(Storage.getSettings().selectedMode)}</span>
          </div>
          <div class="message-content">
            ${isStreaming ? '<span class="typing-indicator"><span></span><span></span><span></span></span>' : this.formatMessage(message.content)}
          </div>
          ${!isStreaming ? this.renderMessageActions(message) : ''}
          <div class="message-stats"></div>
        </div>
      `;
    } else {
      messageEl.innerHTML = `
        <div class="message-body user">
          <div class="message-content">
            ${Utils.escapeHtml(message.content)}
          </div>
        </div>
      `;
    }

    messagesContainer.appendChild(messageEl);
    return messageEl;
  },

  /**
   * Render message action buttons
   * @param {Object} message - Message object
   */
  renderMessageActions(message) {
    return `
      <div class="message-actions">
        <button class="action-btn" onclick="Chat.copyMessage('${message.id}')" data-tooltip="Copy">
          ${Icons.get('copy', 14)}
        </button>
        <button class="action-btn" onclick="Chat.regenerate()" data-tooltip="Regenerate">
          ${Icons.get('refresh', 14)}
        </button>
        ${message.role === 'user' ? `
          <button class="action-btn" onclick="Chat.editMessage('${message.id}')" data-tooltip="Edit">
            ${Icons.get('edit', 14)}
          </button>
        ` : ''}
      </div>
    `;
  },

  /**
   * Update message stats
   * @param {Element} messageEl - Message element
   * @param {string} duration - Response duration
   * @param {number} tokens - Token count
   */
  updateMessageStats(messageEl, duration, tokens) {
    const statsEl = messageEl.querySelector('.message-stats');
    if (statsEl) {
      statsEl.innerHTML = `
        <span class="stat-item">
          ${Icons.get('clock', 12)}
          ${duration}s
        </span>
        <span class="stat-item">
          ${Utils.estimateTokens} tokens
        </span>
      `;
    }
  },

  /**
   * Format message content with markdown
   * @param {string} content - Raw content
   */
  formatMessage(content) {
    if (!content) return '';

    // Escape HTML first
    let html = Utils.escapeHtml(content);

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || Utils.detectLanguage(code);
      return `
        <div class="code-block">
          <div class="code-header">
            <span class="code-lang">${language}</span>
            <button class="code-copy" onclick="Utils.copyToClipboard('${code.trim().replace(/'/g, "\\'")}')">
              ${Icons.get('copy', 12)}
              Copy
            </button>
          </div>
          <pre class="code-pre">${code.trim()}</pre>
        </div>
      `;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
  },

  /**
   * Update streaming UI
   * @param {boolean} isStreaming - Is currently streaming
   */
  updateStreamingUI(isStreaming) {
    const sendBtn = document.getElementById('sendBtn');
    const input = document.getElementById('msgInput');

    if (isStreaming) {
      sendBtn.innerHTML = `
        <button class="stop-btn" onclick="Chat.stopGeneration()">
          ${Icons.get('stop', 16)}
          Stop
        </button>
      `;
      sendBtn.classList.add('streaming');
      input.disabled = true;
    } else {
      sendBtn.innerHTML = Icons.get('send', 18);
      sendBtn.classList.remove('streaming');
      input.disabled = false;
      input.focus();
    }
  },

  /**
   * Render chat messages
   * @param {Object} chat - Chat object
   */
  renderChat(chat) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';

    if (!chat || chat.messages.length === 0) {
      this.renderWelcome();
      return;
    }

    chat.messages.forEach(message => {
      this.renderMessage(message, message.role);
    });

    this.scrollToBottom();
  },

  /**
   * Render welcome screen
   */
  renderWelcome() {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = `
      <div class="welcome-screen">
        <div class="welcome-logo">
          ${Icons.get('logo', 64)}
        </div>
        <h1 class="welcome-title">Saurabh AI</h1>
        <p class="welcome-subtitle">Your intelligent AI assistant</p>
        
        <div class="welcome-modes">
          <h3>Choose a mode:</h3>
          <div class="mode-grid">
            ${Object.values(Modes.getAll()).map(mode => `
              <button class="mode-card" onclick="Chat.startWithMode('${mode.id}')">
                <div class="mode-icon" style="color: ${mode.color}">
                  ${Icons.get(mode.icon, 24)}
                </div>
                <span class="mode-name">${mode.name}</span>
                <span class="mode-desc">${mode.description}</span>
              </button>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  },

  /**
   * Start chat with specific mode
   * @param {string} modeId - Mode ID
   */
  startWithMode(modeId) {
    Storage.updateSetting('selectedMode', modeId);
    App.updateModeIndicator();
  },

  /**
   * Render sidebar with chat list
   */
  renderSidebar() {
    const sidebar = document.getElementById('chatList');
    const chats = Storage.getChats();

    if (chats.length === 0) {
      sidebar.innerHTML = `
        <div class="empty-sidebar">
          <p>No chats yet</p>
        </div>
      `;
      return;
    }

    const currentChatId = Storage.getCurrentChat();

    // Sort by most recent
    const sortedChats = [...chats].sort((a, b) => b.updatedAt - a.updatedAt);

    sidebar.innerHTML = sortedChats.map(chat => `
      <div class="chat-item ${chat.id === currentChatId ? 'active' : ''}" 
           onclick="Chat.loadChat('${chat.id}')">
        <div class="chat-icon">
          ${Icons.get('chat', 16)}
        </div>
        <div class="chat-info">
          <span class="chat-title">${Utils.escapeHtml(chat.title)}</span>
          <span class="chat-time">${Utils.formatRelativeTime(chat.updatedAt)}</span>
        </div>
        <button class="chat-delete" onclick="event.stopPropagation(); Chat.deleteChat('${chat.id}')">
          ${Icons.get('trash', 14)}
        </button>
      </div>
    `).join('');
  },

  /**
   * Load chat
   * @param {string} chatId - Chat ID
   */
  loadChat(chatId) {
    Storage.setCurrentChat(chatId);
    const chat = Storage.getChat(chatId);
    if (chat) {
      this.renderChat(chat);
      this.renderSidebar();
    }
  },

  /**
   * Start new chat
   */
  newChat() {
    const chat = Storage.createChat();
    this.renderChat(chat);
    this.renderSidebar();
    document.getElementById('msgInput').focus();
  },

  /**
   * Delete chat
   * @param {string} chatId - Chat ID
   */
  deleteChat(chatId) {
    if (confirm('Delete this chat?')) {
      Storage.deleteChat(chatId);
      const currentChat = Storage.getChat(Storage.getCurrentChat());
      if (currentChat) {
        this.renderChat(currentChat);
      } else {
        this.renderWelcome();
      }
      this.renderSidebar();
      Sounds.playClick();
    }
  },

  /**
   * Clear current chat
   */
  clearChat() {
    const chat = Storage.getChat(Storage.getCurrentChat());
    if (chat) {
      chat.messages = [];
      Storage.updateChat(chat.id, { messages: [] });
      this.renderChat(chat);
    }
  },

  /**
   * Scroll to bottom of chat
   */
  scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    container.scrollTop = container.scrollHeight;
  }
};

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Chat;
}
