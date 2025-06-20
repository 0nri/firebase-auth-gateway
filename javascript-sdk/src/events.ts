/**
 * Simple event emitter for vanilla JavaScript
 */
export class EventEmitter {
  private events: { [key: string]: Function[] } = {};

  /**
   * Register an event listener
   * @param event Event name
   * @param callback Callback function
   * @returns Unsubscribe function
   */
  on(event: string, callback: Function): () => void {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);

    // Return unsubscribe function
    return () => {
      this.events[event] = this.events[event].filter(cb => cb !== callback);
    };
  }

  /**
   * Emit an event
   * @param event Event name
   * @param args Arguments to pass to the callback
   */
  emit(event: string, ...args: any[]): void {
    if (this.events[event]) {
      this.events[event].forEach(callback => {
        callback(...args);
      });
    }
  }

  /**
   * Remove all event listeners
   * @param event Optional event name to clear only specific event listeners
   */
  clear(event?: string): void {
    if (event) {
      delete this.events[event];
    } else {
      this.events = {};
    }
  }
}
