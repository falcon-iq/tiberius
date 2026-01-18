// libs/shared/util/src/lib/logger.ts
//
// Cross-platform logger (Node, Electron main, Electron renderer, Web) using Pino.
// - Node/Electron main: JSON logs by default; pretty in dev if you want (see createNodeLogger)
// - Browser/renderer: logs to console via pino/browser
//
// Usage:
//   import { getLogger } from '@libs/shared/util/logger';
//   const log = getLogger({ name: 'github-pr-pipeline' });
//   log.info({ org }, 'Starting run');
//
// If you need a (msg: string) => void adapter for existing code:
//   const logFn = asLogFn(log); // (msg) => log.info(msg)
//
// Note: This module intentionally avoids importing Node-only modules (fs/path) so it can be used in web bundles.
import pino from 'pino';
const isBrowser = () => {
    // Browser/Electron renderer: window exists and we're not in a Node.js main process
    // This check works for both web browsers and Electron renderer processes
    return (typeof globalThis !== 'undefined' &&
        'window' in globalThis &&
        typeof globalThis.window !== 'undefined' &&
        'document' in (globalThis.window ?? {}));
};
const defaultLevel = () => {
    // Check NODE_ENV first (works in Node.js and Jest)
    const nodeEnv = (typeof process !== 'undefined' && process.env && process.env['NODE_ENV']) ? process.env['NODE_ENV'] : undefined;
    // In Vite/bundler environments, NODE_ENV is typically set during build
    // For runtime import.meta.env.MODE detection, apps can pass explicit level to createLogger
    const env = (nodeEnv ?? 'production').toLowerCase();
    return env === 'production' ? 'info' : 'debug';
};
const safeBase = (base) => {
    if (!base)
        return {};
    // Ensure it's a plain object; avoid weird prototypes leaking into logs
    return Object.fromEntries(Object.entries(base));
};
/**
 * Creates a logger that works in both browser and Node/Electron.
 * - Browser/Electron renderer: pino/browser (console output via browser bundle)
 * - Node/Electron main: standard pino (stdout, JSON by default)
 *
 * Modern bundlers (Vite, Webpack, etc.) automatically use pino's browser build
 * when bundling for browser environments via package.json's "browser" field.
 */
export const createLogger = (opts = {}) => {
    const level = opts.level ?? defaultLevel();
    const base = safeBase(opts.base);
    const pinoConfig = {
        name: opts.name,
        level,
        base,
        ...(opts.pinoOptions ?? {}),
    };
    // In browser/Electron renderer, configure browser-specific options
    if (isBrowser()) {
        // Browser-specific config: ensure logs go to console
        const browserOpts = opts.pinoOptions?.browser;
        pinoConfig.browser = {
            asObject: false, // Log as formatted strings to console
            ...(browserOpts ?? {}),
        };
    }
    return pino(pinoConfig);
};
/**
 * Convenience singleton for typical app usage.
 * If you need per-module loggers, call createLogger() and/or .child().
 *
 * Note: The first call to getLogger() sets the singleton's level and pinoOptions.
 * Subsequent calls with different level/pinoOptions will be ignored (only name/base
 * create child loggers). This is by design to maintain consistent log levels across
 * the application.
 */
let singleton = null;
export const getLogger = (opts = {}) => {
    if (!singleton) {
        singleton = createLogger(opts);
        return singleton;
    }
    // If caller provided new bindings, return a child so they don't mutate the singleton.
    const hasName = typeof opts.name === 'string' && opts.name.length > 0;
    const hasBase = opts.base && Object.keys(opts.base).length > 0;
    if (hasName || hasBase) {
        return singleton.child({
            ...(hasName ? { name: opts.name } : {}),
            ...(hasBase ? safeBase(opts.base) : {}),
        });
    }
    return singleton;
};
/**
 * Adapter for code that expects a simple (msg: string) => void.
 * Defaults to info-level.
 *
 * Example:
 *   const log = getLogger();
 *   const logFn = asLogFn(log); // Creates (msg) => log.info(msg)
 *   someLibrary({ logger: logFn });
 */
export const asLogFn = (logger, level = 'info') => {
    return (msg) => {
        // Pino logger methods can be called with just a string directly
        logger[level](msg);
    };
};
/**
 * Utility to create a child logger with consistent bindings.
 */
export const childLogger = (logger, bindings) => {
    return logger.child(safeBase(bindings));
};
/**
 * **TEST ONLY**: Resets the singleton logger instance.
 * This should ONLY be used in test files to ensure test isolation.
 * DO NOT use this in production code.
 *
 * @internal
 */
export const __resetLoggerForTesting = () => {
    singleton = null;
};
