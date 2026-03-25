/**
 * =============================================
 * SAURABH AI - Utility Functions
 * Helper functions used throughout the app
 * =============================================
 */

const Utils = {
  /**
   * Escape HTML to prevent XSS
   * @param {string} str - String to escape
   * @returns {string} Escaped string
   */
  escapeHtml(str) {
    if (typeof str !== 'string') return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },

  /**
   * Generate unique ID
   * @returns {string} Unique ID
   */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  },

  /**
   * Debounce function
   * @param {function} func - Function to debounce
   * @param {number} wait - Wait time in ms
   * @returns {function} Debounced function
   */
  debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Throttle function
   * @param {function} func - Function to throttle
   * @param {number} limit - Time limit in ms
   * @returns {function} Throttled function
   */
  throttle(func, limit = 300) {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Format timestamp to readable time
   * @param {number} timestamp - Unix timestamp
   * @returns {string} Formatted time
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  },

  /**
   * Format date to readable format
   * @param {number} timestamp - Unix timestamp
   * @returns {string} Formatted date
   */
  formatDate(timestamp) {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    }
  },

  /**
   * Format relative time (e.g., "2 min ago")
   * @param {number} timestamp - Unix timestamp
   * @returns {string} Relative time
   */
  formatRelativeTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return this.formatDate(timestamp);
  },

  /**
   * Copy text to clipboard
   * @param {string} text - Text to copy
   * @returns {Promise<boolean>} Success status
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
      } catch (e) {
        document.body.removeChild(textarea);
        return false;
      }
    }
  },

  /**
   * Download file
   * @param {string} content - File content
   * @param {string} filename - File name
   * @param {string} type - MIME type
   */
  downloadFile(content, filename, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Download image from URL
   * @param {string} url - Image URL
   * @param {string} filename - File name
   */
  async downloadImage(url, filename = 'image.png') {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const urlBlob = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = urlBlob;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(urlBlob);
      return true;
    } catch (err) {
      console.error('Download failed:', err);
      return false;
    }
  },

  /**
   * Truncate text with ellipsis
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @returns {string} Truncated text
   */
  truncate(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
  },

  /**
   * Get first line of text (for chat title)
   * @param {string} text - Full text
   * @param {number} maxLength - Maximum length
   * @returns {string} First line
   */
  getFirstLine(text, maxLength = 40) {
    const firstLine = text.split('\n')[0].trim();
    return this.truncate(firstLine, maxLength);
  },

  /**
   * Estimate token count (rough)
   * @param {string} text - Text to count
   * @returns {number} Estimated tokens
   */
  estimateTokens(text) {
    // Rough estimate: 1 token ≈ 4 characters
    return Math.ceil(text.length / 4);
  },

  /**
   * Parse markdown-like formatting
   * @param {string} text - Text with formatting
   * @returns {string} HTML string
   */
  parseMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML first
    let html = this.escapeHtml(text);
    
    // Code blocks (must be first)
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre class="code-block"><code class="code-pre">${code.trim()}</code></pre>`;
    });
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
  },

  /**
   * Detect language from code block
   * @param {string} code - Code content
   * @returns {string} Detected language
   */
  detectLanguage(code) {
    const patterns = {
      javascript: /\b(const|let|var|function|=>|import|export|require)\b/,
      python: /\b(def|class|import|from|if __name__|print\(|lambda)\b/,
      html: /<\/?(!DOCTYPE|html|head|body|div|span|p|a|img|script|style)\b/i,
      css: /\{[^}]*:\s*[^;]+;\s*\}/,
      json: /^\s*[{[\s]*[\w]+:\s*["\d\[\]]/,
      sql: /\b(SELECT|INSERT|UPDATE|DELETE|CREATE|FROM|WHERE)\b/i,
      bash: /^#!/m,
      java: /\b(public|private|class|void|static|import java)\b/,
      cpp: /\b(#include|int main|std::|cout|cin)\b/,
      go: /\b(func|package|import|fmt|main)\b/,
      rust: /\b(fn|let|mut|impl|pub|use)\b/,
    };

    for (const [lang, pattern] of Object.entries(patterns)) {
      if (pattern.test(code)) {
        return lang;
      }
    }
    return 'text';
  },

  /**
   * Random ID generator
   * @param {number} length - Length of ID
   * @returns {string} Random ID
   */
  randomId(length = 8) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  },

  /**
   * Check if dark mode preferred
   * @returns {boolean}
   */
  prefersDarkMode() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  },

  /**
   * Get random item from array
   * @param {Array} arr - Array
   * @returns {*} Random item
   */
  randomFrom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  },

  /**
   * Clamp number between min and max
   * @param {number} num - Number
   * @param {number} min - Minimum
   * @param {number} max - Maximum
   * @returns {number} Clamped number
   */
  clamp(num, min, max) {
    return Math.min(Math.max(num, min), max);
  },

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds
   * @returns {Promise}
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * Get file extension
   * @param {string} filename - File name
   * @returns {string} Extension
   */
  getFileExtension(filename) {
    return filename.split('.').pop().toLowerCase();
  },

  /**
   * Format file size
   * @param {number} bytes - Size in bytes
   * @returns {string} Formatted size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
};

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Utils;
}
