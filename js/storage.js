/**
 * =============================================
 * SAURABH AI - Storage Management
 * LocalStorage operations for chats and settings
 * =============================================
 */

const Storage = {
  // Storage keys
  KEYS: {
    CHATS: 'saurabh_ai_chats',
    SETTINGS: 'saurabh_ai_settings',
    CURRENT_CHAT: 'saurabh_ai_current_chat',
    THEME: 'saurabh_ai_theme',
    SOUND: 'saurabh_ai_sound',
  },

  // Max chats to keep
  MAX_CHATS: 10,

  /**
   * Get all chats from storage
   * @returns {Array} Array of chats
   */
  getChats() {
    try {
      const data = localStorage.getItem(this.KEYS.CHATS);
      return data ? JSON.parse(data) : [];
    } catch (err) {
      console.error('Error loading chats:', err);
      return [];
    }
  },

  /**
   * Save chats to storage
   * @param {Array} chats - Array of chats
   */
  saveChats(chats) {
    try {
      // Keep only last MAX_CHATS
      const trimmedChats = chats.slice(-this.MAX_CHATS);
      localStorage.setItem(this.KEYS.CHATS, JSON.stringify(trimmedChats));
    } catch (err) {
      console.error('Error saving chats:', err);
    }
  },

  /**
   * Get a single chat by ID
   * @param {string} chatId - Chat ID
   * @returns {Object|null} Chat object
   */
  getChat(chatId) {
    const chats = this.getChats();
    return chats.find(chat => chat.id === chatId) || null;
  },

  /**
   * Create a new chat
   * @param {string} title - Chat title (optional)
   * @returns {Object} New chat object
   */
  createChat(title = null) {
    const chats = this.getChats();
    const chat = {
      id: Utils.generateId(),
      title: title || 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model: 'llama-3.3-70b-versatile',
      mode: null
    };
    chats.push(chat);
    this.saveChats(chats);
    this.setCurrentChat(chat.id);
    return chat;
  },

  /**
   * Update a chat
   * @param {string} chatId - Chat ID
   * @param {Object} updates - Updates to apply
   */
  updateChat(chatId, updates) {
    const chats = this.getChats();
    const index = chats.findIndex(chat => chat.id === chatId);
    if (index !== -1) {
      chats[index] = {
        ...chats[index],
        ...updates,
        updatedAt: Date.now()
      };
      this.saveChats(chats);
    }
  },

  /**
   * Add message to chat
   * @param {string} chatId - Chat ID
   * @param {Object} message - Message object
   */
  addMessage(chatId, message) {
    const chats = this.getChats();
    const index = chats.findIndex(chat => chat.id === chatId);
    if (index !== -1) {
      chats[index].messages.push(message);
      chats[index].updatedAt = Date.now();
      
      // Update title from first user message if not set
      if (chats[index].messages.length === 2 && message.role === 'user') {
        chats[index].title = Utils.getFirstLine(message.content);
      }
      
      this.saveChats(chats);
    }
  },

  /**
   * Update last message in chat
   * @param {string} chatId - Chat ID
   * @param {Object} message - Updated message
   */
  updateLastMessage(chatId, message) {
    const chats = this.getChats();
    const index = chats.findIndex(chat => chat.id === chatId);
    if (index !== -1 && chats[index].messages.length > 0) {
      chats[index].messages[chats[index].messages.length - 1] = message;
      chats[index].updatedAt = Date.now();
      this.saveChats(chats);
    }
  },

  /**
   * Delete a chat
   * @param {string} chatId - Chat ID
   */
  deleteChat(chatId) {
    let chats = this.getChats();
    chats = chats.filter(chat => chat.id !== chatId);
    this.saveChats(chats);
    
    // If deleted current chat, switch to most recent
    if (this.getCurrentChat() === chatId) {
      const remainingChats = this.getChats();
      if (remainingChats.length > 0) {
        this.setCurrentChat(remainingChats[remainingChats.length - 1].id);
      }
    }
  },

  /**
   * Delete all chats
   */
  deleteAllChats() {
    localStorage.removeItem(this.KEYS.CHATS);
    localStorage.removeItem(this.KEYS.CURRENT_CHAT);
  },

  /**
   * Get current chat ID
   * @returns {string|null} Current chat ID
   */
  getCurrentChat() {
    return localStorage.getItem(this.KEYS.CURRENT_CHAT);
  },

  /**
   * Set current chat ID
   * @param {string} chatId - Chat ID
   */
  setCurrentChat(chatId) {
    localStorage.setItem(this.KEYS.CURRENT_CHAT, chatId);
  },

  /**
   * Get all settings
   * @returns {Object} Settings object
   */
  getSettings() {
    try {
      const data = localStorage.getItem(this.KEYS.SETTINGS);
      return data ? JSON.parse(data) : this.getDefaultSettings();
    } catch (err) {
      console.error('Error loading settings:', err);
      return this.getDefaultSettings();
    }
  },

  /**
   * Get default settings
   * @returns {Object} Default settings
   */
  getDefaultSettings() {
    return {
      theme: 'dark',
      soundEnabled: false,
      soundVolume: 0.5,
      autoScroll: true,
      showTimestamps: true,
      maxTokens: 2000,
      temperature: 0.75,
      selectedModel: 'llama-3.3-70b-versatile',
      fontSize: 'medium',
      streamingResponse: true,
    };
  },

  /**
   * Save settings
   * @param {Object} settings - Settings object
   */
  saveSettings(settings) {
    try {
      localStorage.setItem(this.KEYS.SETTINGS, JSON.stringify(settings));
    } catch (err) {
      console.error('Error saving settings:', err);
    }
  },

  /**
   * Update single setting
   * @param {string} key - Setting key
   * @param {*} value - Setting value
   */
  updateSetting(key, value) {
    const settings = this.getSettings();
    settings[key] = value;
    this.saveSettings(settings);
  },

  /**
   * Get theme
   * @returns {string} 'dark' or 'light'
   */
  getTheme() {
    return localStorage.getItem(this.KEYS.THEME) || 'dark';
  },

  /**
   * Set theme
   * @param {string} theme - 'dark' or 'light'
   */
  setTheme(theme) {
    localStorage.setItem(this.KEYS.THEME, theme);
    document.documentElement.setAttribute('data-theme', theme);
  },

  /**
   * Get sound enabled status
   * @returns {boolean}
   */
  isSoundEnabled() {
    return localStorage.getItem(this.KEYS.SOUND) === 'true';
  },

  /**
   * Set sound enabled status
   * @param {boolean} enabled
   */
  setSoundEnabled(enabled) {
    localStorage.setItem(this.KEYS.SOUND, enabled.toString());
  },

  /**
   * Clear all storage
   */
  clearAll() {
    Object.values(this.KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  },

  /**
   * Get storage usage info
   * @returns {Object} Storage info
   */
  getStorageInfo() {
    let totalSize = 0;
    const items = {};
    
    Object.values(this.KEYS).forEach(key => {
      const data = localStorage.getItem(key);
      if (data) {
        const size = new Blob([data]).size;
        items[key] = {
          size,
          sizeFormatted: Utils.formatFileSize(size)
        };
        totalSize += size;
      }
    });

    return {
      totalSize,
      totalSizeFormatted: Utils.formatFileSize(totalSize),
      items
    };
  },

  /**
   * Export all data as JSON
   * @returns {string} JSON string
   */
  exportData() {
    return JSON.stringify({
      chats: this.getChats(),
      settings: this.getSettings(),
      theme: this.getTheme(),
      exportedAt: new Date().toISOString()
    }, null, 2);
  },

  /**
   * Import data from JSON
   * @param {string} jsonString - JSON string
   * @returns {boolean} Success status
   */
  importData(jsonString) {
    try {
      const data = JSON.parse(jsonString);
      if (data.chats) {
        this.saveChats(data.chats);
      }
      if (data.settings) {
        this.saveSettings(data.settings);
      }
      if (data.theme) {
        this.setTheme(data.theme);
      }
      return true;
    } catch (err) {
      console.error('Error importing data:', err);
      return false;
    }
  }
};

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Storage;
}
