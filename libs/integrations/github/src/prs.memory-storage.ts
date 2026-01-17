// libs/integrations/github/src/lib/prs.memory-storage.ts

import type { PrStorage } from './prs';

export class MemoryPrStorage implements PrStorage {
    private readonly store: Map<string, string | Uint8Array>;

    constructor() {
        this.store = new Map();
    }

    async init(): Promise<void> {
        // No-op for in-memory storage
    }

    async writeText(key: string, contents: string): Promise<void> {
        this.store.set(key, contents);
    }

    async writeBinary(key: string, contents: Uint8Array): Promise<void> {
        this.store.set(key, contents);
    }

    // Helper method to retrieve stored content (useful for testing)
    get(key: string): string | Uint8Array | undefined {
        return this.store.get(key);
    }

    // Helper method to check if key exists
    has(key: string): boolean {
        return this.store.has(key);
    }

    // Helper method to clear all stored data
    clear(): void {
        this.store.clear();
    }

    // Helper method to get all keys
    keys(): string[] {
        return Array.from(this.store.keys());
    }
}
