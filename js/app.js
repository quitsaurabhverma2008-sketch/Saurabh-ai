/**
 * =============================================
 * SAURABH AI - Main App
 * Core application logic and initialization
 * =============================================
 */

const App = {
  // App state
  state: {
    initialized: false,
    theme: 'dark',
    soundEnabled: false,
    selectedMode: 'coding',
    selectedModel: 'llama-3.3-70b-versatile',
  },

  /**
   * Initialize the application
   */
  init() {
    if (this.state.initialized) return;

    // Load settings
    this.loadSettings();

    // Apply theme
    this.applyTheme();

    // Initialize components
    Storage.init();
    Sounds.init();
    Chat.init();

    // Set up event listeners
    this.setupEventListeners();

    // Mark as initialized
    this.state.initialized = true;

    console.log('Saurabh AI initialized successfully!');
  },

  /**
   * Load settings from storage
   */
  loadSettings() {
    const settings = Storage.getSettings();
    this.state.theme = settings.theme || 'dark';
    this.state.soundEnabled = settings.soundEnabled || false;
    this.state.selectedMode = settings.selectedMode || 'coding';
    this.state.selectedModel = settings.selectedModel || 'llama-3.3-70b-versatile';

    // Update UI
    this.updateThemeToggle();
    this.updateSoundToggle();
    this.updateModeIndicator();
  },

  /**
   * Setup global event listeners
   */
  setupEventListeners() {
    // Theme toggle
    document.getElementById('themeToggle')?.addEventListener('click', () => this.toggleTheme());

    // Sound toggle
    document.getElementById('soundToggle')?.addEventListener('click', () => this.toggleSound());

    // New chat button
    document.getElementById('newChatBtn')?.addEventListener('click', () => this.newChat());

    // Model selector
    document.getElementById('modelSelector')?.addEventListener('click', () => this.toggleModelDropdown());

    // Mode selector
    document.getElementById('modeSelector')?.addEventListener('click', () => this.toggleModeDropdown());

    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.dropdown')) {
        this.closeAllDropdowns();
      }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + N = New chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        this.newChat();
      }
      // Ctrl/Cmd + L = Clear chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        Chat.clearChat();
      }
      // Escape = Close dropdowns/modals
      if (e.key === 'Escape') {
        this.closeAllDropdowns();
      }
    });

    // Handle online/offline
    window.addEventListener('online', () => this.showToast('Back online!', 'success'));
    window.addEventListener('offline', () => this.showToast('You are offline', 'warning'));
  },

  /**
   * Toggle theme
   */
  toggleTheme() {
    this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
    Storage.setTheme(this.state.theme);
    this.applyTheme();
    this.updateThemeToggle();
    Sounds.playClick();
  },

  /**
   * Apply theme to document
   */
  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.state.theme);
  },

  /**
   * Update theme toggle UI
   */
  updateThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.classList.toggle('active', this.state.theme === 'dark');
    }
  },

  /**
   * Toggle sound
   */
  toggleSound() {
    this.state.soundEnabled = !this.state.soundEnabled;
    Storage.updateSetting('soundEnabled', this.state.soundEnabled);
    Sounds.setEnabled(this.state.soundEnabled);
    this.updateSoundToggle();
    Sounds.playClick();
  },

  /**
   * Update sound toggle UI
   */
  updateSoundToggle() {
    const toggle = document.getElementById('soundToggle');
    if (toggle) {
      toggle.classList.toggle('active', this.state.soundEnabled);
    }
  },

  /**
   * Toggle model dropdown
   */
  toggleModelDropdown() {
    const dropdown = document.getElementById('modelDropdown');
    dropdown?.classList.toggle('open');
    Sounds.playClick();
  },

  /**
   * Toggle mode dropdown
   */
  toggleModeDropdown() {
    const dropdown = document.getElementById('modeDropdown');
    dropdown?.classList.toggle('open');
    Sounds.playClick();
  },

  /**
   * Close all dropdowns
   */
  closeAllDropdowns() {
    document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
  },

  /**
   * Select model
   * @param {string} modelId - Model ID
   */
  selectModel(modelId) {
    this.state.selectedModel = modelId;
    Storage.updateSetting('selectedModel', modelId);
    this.updateModelIndicator();
    this.closeAllDropdowns();
    Sounds.playSuccess();
  },

  /**
   * Select mode
   * @param {string} modeId - Mode ID
   */
  selectMode(modeId) {
    this.state.selectedMode = modeId;
    Storage.updateSetting('selectedMode', modeId);
    this.updateModeIndicator();
    this.closeAllDropdowns();
    Sounds.playSuccess();
  },

  /**
   * Update model indicator in UI
   */
  updateModelIndicator() {
    const indicator = document.getElementById('modelIndicator');
    const models = {
      'llama-3.3-70b-versatile': { name: 'Llama 3.3 70B', color: '#3b82f6' },
      'llama-4-maverick-17b-128e-instruct': { name: 'Llama 4 Maverick', color: '#a855f7' },
      'deepseek-r1-distill-llama-70b': { name: 'DeepSeek R1', color: '#22c55e' },
      'qwen/qwen3-32b': { name: 'Qwen 3 32B', color: '#06b6d4' },
      'llama-3.1-8b-instant': { name: 'Llama 3.1 8B', color: '#60a5fa' },
      'mixtral-8x7b-32768': { name: 'Mixtral 8x7B', color: '#f59e0b' },
    };

    const model = models[this.state.selectedModel] || { name: 'Auto', color: '#d4845a' };

    if (indicator) {
      indicator.innerHTML = `
        <span class="indicator-dot" style="background: ${model.color}"></span>
        <span class="indicator-text">${model.name}</span>
        ${Icons.get('chevronDown', 16)}
      `;
    }
  },

  /**
   * Update mode indicator in UI
   */
  updateModeIndicator() {
    const mode = Modes.get(this.state.selectedMode);
    const indicator = document.getElementById('modeIndicator');

    if (indicator && mode) {
      indicator.innerHTML = `
        <span class="indicator-dot" style="background: ${mode.color}"></span>
        <span class="indicator-text">${mode.name}</span>
        ${Icons.get('chevronDown', 16)}
      `;
    }
  },

  /**
   * Start new chat
   */
  newChat() {
    Chat.newChat();
    Sounds.playClick();
  },

  /**
   * Show toast notification
   * @param {string} message - Toast message
   * @param {string} type - Toast type (success, error, warning, info)
   */
  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      ${type === 'success' ? Icons.get('checkCircle', 16) : ''}
      ${type === 'error' ? Icons.get('xCircle', 16) : ''}
      ${type === 'warning' ? Icons.get('alert', 16) : ''}
      ${type === 'info' ? Icons.get('info', 16) : ''}
      <span>${Utils.escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'toastOut 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  },

  /**
   * Show modal
   * @param {string} modalId - Modal element ID
   */
  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('show');
      Sounds.playPop();
    }
  },

  /**
   * Hide modal
   * @param {string} modalId - Modal element ID
   */
  hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('show');
    }
  },

  /**
   * Get API base URL
   * @returns {string} API base URL
   */
  getAPIUrl() {
    // Can be configured for production
    return 'http://localhost:8000';
  },

  /**
   * Check if online
   * @returns {boolean}
   */
  isOnline() {
    return navigator.onLine;
  },

  /**
   * Get app version
   * @returns {string}
   */
  getVersion() {
    return '2.0.0';
  },

  /**
   * Get app info
   * @returns {Object}
   */
  getInfo() {
    return {
      name: 'Saurabh AI',
      version: this.getVersion(),
      description: 'Your intelligent AI assistant',
      author: 'Saurabh',
      buildDate: '2026'
    };
  }
};

// Server Monitor - Handles sleep/wake detection
const ServerMonitor = {
  RETRY_INTERVAL: 5,
  PING_TIMEOUT: 5000,
  
  isServerAwake: false,
  countdownValue: 5,
  countdownInterval: null,
  retryCount: 0,
  maxRetries: 100,
  initialized: false,
  
  getAPIUrl() {
    return App.getAPIUrl();
  },
  
  async checkHealth() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.PING_TIMEOUT);
      
      const res = await fetch(`${this.getAPIUrl()}/ping`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeout);
      
      if (res.ok) {
        this.onServerAwake();
        return true;
      }
    } catch (e) {
      // Server is sleep
    }
    this.onServerSleep();
    return false;
  },
  
  onServerSleep() {
    this.isServerAwake = false;
    
    if (!this.initialized) {
      this.initialized = true;
      this.showSleepOverlay();
      this.startCountdown();
    }
  },
  
  onServerAwake() {
    this.isServerAwake = true;
    this.stopCountdown();
    this.hideSleepOverlay();
    this.initialized = false;
    this.retryCount = 0;
  },
  
  showSleepOverlay() {
    const overlay = document.getElementById('sleepOverlay');
    const splash = document.getElementById('splash');
    
    if (splash) splash.classList.add('out');
    if (overlay) overlay.classList.add('show');
    
    this.updateCountdownDisplay(this.RETRY_INTERVAL);
  },
  
  hideSleepOverlay() {
    const overlay = document.getElementById('sleepOverlay');
    const splash = document.getElementById('splash');
    
    if (overlay) overlay.classList.remove('show');
    if (splash) splash.classList.remove('out');
  },
  
  updateCountdownDisplay(value) {
    const countdown = document.getElementById('sleepCountdown');
    const status = document.getElementById('sleepStatus');
    
    if (countdown) countdown.textContent = value;
    if (status) status.textContent = `Retrying in ${value} seconds...`;
  },
  
  startCountdown() {
    this.countdownValue = this.RETRY_INTERVAL;
    this.updateCountdownDisplay(this.countdownValue);
    
    this.countdownInterval = setInterval(() => {
      this.countdownValue--;
      
      if (this.countdownValue <= 0) {
        this.countdownValue = this.RETRY_INTERVAL;
        this.retryCount++;
        
        if (this.retryCount > this.maxRetries) {
          this.stopCountdown();
          const status = document.getElementById('sleepStatus');
          if (status) status.textContent = 'Server not responding. Retrying...';
          this.retryCount = 0;
        }
        
        this.checkHealth();
      }
      
      this.updateCountdownDisplay(this.countdownValue);
    }, 1000);
  },
  
  stopCountdown() {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
  },
  
  async waitForServer() {
    while (!this.isServerAwake) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  await ServerMonitor.checkHealth();
  App.init();
});

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = App;
}
