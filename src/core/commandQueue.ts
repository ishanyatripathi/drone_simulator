import type { Command, CommandSource, CommandType } from '@/types/command.types';

/**
 * CommandQueue
 * ------------
 * A source-agnostic FIFO buffer sitting between input devices and the
 * DroneController.
 *
 *   Keyboard  ─┐
 *              ├─► CommandQueue ─► DroneController ─► PhysicsEngine ─► Drone
 *   Gesture*  ─┘   (*Phase 2)
 *
 * Any input source only ever calls `enqueue`. The DroneController is the
 * only consumer, and drains the queue once per simulation tick via
 * `drainAll`. This keeps input handling fully decoupled from flight logic,
 * so swapping keyboard for gesture recognition in Phase 2 requires zero
 * changes here or downstream.
 */
export class CommandQueue {
  private queue: Command[] = [];
  private readonly maxSize: number;

  constructor(maxSize = 256) {
    this.maxSize = maxSize;
  }

  enqueue(type: CommandType, source: CommandSource, intensity = 1): void {
    if (this.queue.length >= this.maxSize) {
      this.queue.shift();
    }
    this.queue.push({ type, source, timestamp: performance.now(), intensity });
  }

  /** Drains and returns every pending command, clearing the queue. */
  drainAll(): Command[] {
    const drained = this.queue;
    this.queue = [];
    return drained;
  }

  peekAll(): readonly Command[] {
    return this.queue;
  }

  clear(): void {
    this.queue = [];
  }

  get size(): number {
    return this.queue.length;
  }
}
