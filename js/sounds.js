/**
 * =============================================
 * SAURABH AI - Sound Effects
 * Optional sound effects for better UX
 * =============================================
 */

const Sounds = {
  // Sound enabled status
  enabled: false,

  // Volume level (0 to 1)
  volume: 0.5,

  // Audio context for generating sounds
  audioContext: null,

  /**
   * Initialize sound system
   */
  init() {
    this.enabled = Storage.isSoundEnabled();
    this.volume = Storage.getSettings().soundVolume || 0.5;
  },

  /**
   * Enable/disable sounds
   * @param {boolean} enabled
   */
  setEnabled(enabled) {
    this.enabled = enabled;
    Storage.setSoundEnabled(enabled);
  },

  /**
   * Set volume
   * @param {number} volume - Volume level (0 to 1)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    Storage.updateSetting('soundVolume', this.volume);
  },

  /**
   * Get audio context (create if not exists)
   */
  getContext() {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return this.audioContext;
  },

  /**
   * Play a tone
   * @param {number} frequency - Frequency in Hz
   * @param {number} duration - Duration in seconds
   * @param {string} type - Oscillator type (sine, square, sawtooth, triangle)
   */
  playTone(frequency = 800, duration = 0.05, type = 'sine') {
    if (!this.enabled) return;

    try {
      const ctx = this.getContext();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.type = type;
      oscillator.frequency.value = frequency;
      gainNode.gain.value = this.volume * 0.3;

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + duration);
    } catch (err) {
      console.warn('Sound playback failed:', err);
    }
  },

  /**
   * Typing tick sound (soft click)
   */
  playTypingTick() {
    this.playTone(1200, 0.02, 'sine');
  },

  /**
   * Message sent sound
   */
  playMessageSent() {
    if (!this.enabled) return;
    this.playTone(600, 0.08, 'sine');
    setTimeout(() => this.playTone(800, 0.08, 'sine'), 80);
  },

  /**
   * Message received sound
   */
  playMessageReceived() {
    if (!this.enabled) return;
    this.playTone(800, 0.06, 'sine');
    setTimeout(() => this.playTone(1000, 0.1, 'sine'), 100);
  },

  /**
   * Success sound
   */
  playSuccess() {
    if (!this.enabled) return;
    this.playTone(523, 0.1, 'sine'); // C5
    setTimeout(() => this.playTone(659, 0.1, 'sine'), 100); // E5
    setTimeout(() => this.playTone(784, 0.15, 'sine'), 200); // G5
  },

  /**
   * Error sound
   */
  playError() {
    if (!this.enabled) return;
    this.playTone(200, 0.15, 'square');
    setTimeout(() => this.playTone(150, 0.2, 'square'), 150);
  },

  /**
   * Notification sound
   */
  playNotification() {
    if (!this.enabled) return;
    this.playTone(880, 0.1, 'sine');
    setTimeout(() => this.playTone(1100, 0.1, 'sine'), 120);
  },

  /**
   * Click sound
   */
  playClick() {
    this.playTone(1000, 0.02, 'sine');
  },

  /**
   * Button hover sound
   */
  playHover() {
    this.playTone(600, 0.01, 'sine');
  },

  /**
   * Pop sound (for modals/tooltips)
   */
  playPop() {
    if (!this.enabled) return;
    this.playTone(400, 0.05, 'triangle');
    setTimeout(() => this.playTone(600, 0.05, 'triangle'), 30);
  },

  /**
   * Whoosh sound (for transitions)
   */
  playWhoosh() {
    if (!this.enabled) return;

    try {
      const ctx = this.getContext();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(200, ctx.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.15);
      gainNode.gain.setValueAtTime(this.volume * 0.2, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.15);
    } catch (err) {
      console.warn('Sound playback failed:', err);
    }
  },

  /**
   * Generate a random pleasant sound
   */
  playRandom() {
    if (!this.enabled) return;
    const notes = [523, 587, 659, 698, 784, 880, 988]; // C5 to B5
    const note = notes[Math.floor(Math.random() * notes.length)];
    this.playTone(note, 0.1, 'sine');
  },

  /**
   * Resume audio context (needed for some browsers)
   */
  async resume() {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
  },

  /**
   * Clean up audio context
   */
  cleanup() {
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
};

// Initialize on load
Sounds.init();

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Sounds;
}
