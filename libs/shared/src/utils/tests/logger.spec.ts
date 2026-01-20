/**
 * @jest-environment node
 */

// Mock import.meta before importing the logger module
// Jest doesn't support import.meta, so we need to handle it

type MockLogger = {
    info: jest.Mock;
    debug: jest.Mock;
    warn: jest.Mock;
    error: jest.Mock;
    fatal: jest.Mock;
    trace: jest.Mock;
    child: jest.Mock;
};

const mockLogger: MockLogger = {
    info: jest.fn(),
    debug: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    fatal: jest.fn(),
    trace: jest.fn(),
    child: jest.fn().mockReturnThis(),
};

const pinoMock = jest.fn(() => mockLogger);

// Mock pino before importing logger - must return default export
jest.mock('pino', () => ({
    __esModule: true,
    default: pinoMock,
}));

import { createLogger, getLogger, asLogFn, childLogger, __resetLoggerForTesting } from '../logger';
import type { Logger, LogLevel } from '../logger';

describe('logger', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let originalWindow: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let originalProcess: any;

    beforeAll(() => {
        // Ensure mock is set up
        expect(pinoMock).toBeDefined();
    });

    beforeEach(() => {
        jest.clearAllMocks();
        // Reset singleton to ensure test isolation.
        // Without this, the singleton instance persists across test cases,
        // causing tests to fail or behave unexpectedly depending on execution order.
        __resetLoggerForTesting();
    });

    afterEach(() => {
        // Restore global objects
        if (originalWindow !== undefined) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).window = originalWindow;
        } else {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            delete (globalThis as any).window;
        }
        if (originalProcess !== undefined) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).process = originalProcess;
        }
    });

    describe('createLogger', () => {
        it('should create a logger with default options', () => {
            const logger = createLogger();

            expect(logger).toBeDefined();
            expect(pinoMock).toHaveBeenCalled();
        });

        it('should create a logger with custom name', () => {
            createLogger({ name: 'test-logger' });

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    name: 'test-logger',
                })
            );
        });

        it('should create a logger with custom level', () => {
            createLogger({ level: 'error' });

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    level: 'error',
                })
            );
        });

        it('should create a logger with custom base bindings', () => {
            const base = { app: 'test-app', env: 'test' };
            createLogger({ base });

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    base,
                })
            );
        });

        it('should use default level "info" in production', () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            originalProcess = (globalThis as any).process;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).process = {
                env: { NODE_ENV: 'production' },
            };

            createLogger();

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    level: 'info',
                })
            );
        });

        it('should use default level "debug" in development', () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            originalProcess = (globalThis as any).process;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).process = {
                env: { NODE_ENV: 'development' },
            };

            createLogger();

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    level: 'debug',
                })
            );
        });

        it('should configure browser options when in browser environment', () => {
            // Mock browser environment
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            originalWindow = (globalThis as any).window;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).window = {
                document: {},
            };

            createLogger();

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    browser: expect.objectContaining({
                        asObject: false,
                    }),
                })
            );
        });

        it('should not configure browser options in Node environment', () => {
            // Ensure we're in Node environment
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            delete (globalThis as any).window;

            createLogger();

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const calls = pinoMock.mock.calls as any[];
            expect(calls.length).toBeGreaterThan(0);
            const lastCall = calls[calls.length - 1];
            expect(lastCall[0]).not.toHaveProperty('browser');
        });
    });

    describe('getLogger', () => {
        it('should return a singleton instance', () => {
            const logger1 = getLogger();
            const logger2 = getLogger();

            expect(logger1).toBe(logger2);
        });

        it('should create child logger when name is provided after singleton creation', () => {
            const mainLogger = getLogger();
            getLogger({ name: 'child' });

            expect(mainLogger.child).toHaveBeenCalled();
        });

        it('should create child logger when base is provided after singleton creation', () => {
            const mainLogger = getLogger();
            getLogger({ base: { module: 'test' } });

            expect(mainLogger.child).toHaveBeenCalled();
        });

        it('should return singleton when no options provided after creation', () => {
            const logger1 = getLogger();
            jest.clearAllMocks(); // Clear to verify no new child is created
            const logger2 = getLogger({});

            expect(logger1).toBe(logger2);
            expect(logger1.child).not.toHaveBeenCalled();
        });
    });

    describe('asLogFn', () => {
        it('should create a function that logs at info level by default', () => {
            const mockLogger = {
                info: jest.fn(),
                debug: jest.fn(),
                warn: jest.fn(),
                error: jest.fn(),
                fatal: jest.fn(),
                trace: jest.fn(),
            } as unknown as Logger;

            const logFn = asLogFn(mockLogger);
            logFn('test message');

            expect(mockLogger.info).toHaveBeenCalledWith('test message');
        });

        it('should create a function that logs at specified level', () => {
            const mockLogger = {
                info: jest.fn(),
                debug: jest.fn(),
                warn: jest.fn(),
                error: jest.fn(),
                fatal: jest.fn(),
                trace: jest.fn(),
            } as unknown as Logger;

            const logFn = asLogFn(mockLogger, 'error');
            logFn('error message');

            expect(mockLogger.error).toHaveBeenCalledWith('error message');
        });

        it('should support all log levels', () => {
            const levels: Array<Exclude<LogLevel, 'silent'>> = ['fatal', 'error', 'warn', 'info', 'debug', 'trace'];

            levels.forEach((level) => {
                const mockLogger = {
                    info: jest.fn(),
                    debug: jest.fn(),
                    warn: jest.fn(),
                    error: jest.fn(),
                    fatal: jest.fn(),
                    trace: jest.fn(),
                } as unknown as Logger;

                const logFn = asLogFn(mockLogger, level);
                logFn(`test ${level} message`);

                expect(mockLogger[level]).toHaveBeenCalledWith(`test ${level} message`);
            });
        });
    });

    describe('childLogger', () => {
        it('should create a child logger with bindings', () => {
            const mockLogger = {
                child: jest.fn().mockReturnThis(),
            } as unknown as Logger;

            const bindings = { requestId: '123', userId: 'abc' };
            childLogger(mockLogger, bindings);

            expect(mockLogger.child).toHaveBeenCalledWith(bindings);
        });

        it('should sanitize bindings by creating a plain object', () => {
            const mockLocalLogger = {
                child: jest.fn().mockReturnThis(),
            } as unknown as Logger;

            // Create object with prototype
            class CustomClass {
                value = 'test';
            }
            const instance = new CustomClass();

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            childLogger(mockLocalLogger, instance as any);

            expect(mockLocalLogger.child).toHaveBeenCalled();
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const passedBindings = (mockLocalLogger.child as any).mock.calls[0][0];
            // Should be plain object with only enumerable own properties
            expect(passedBindings).toEqual({ value: 'test' });
        });

        it('should handle empty bindings', () => {
            const mockLogger = {
                child: jest.fn().mockReturnThis(),
            } as unknown as Logger;

            childLogger(mockLogger, {});

            expect(mockLogger.child).toHaveBeenCalledWith({});
        });
    });

    describe('environment detection', () => {
        it('should detect Node.js environment', () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            delete (globalThis as any).window;

            createLogger();

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const calls = pinoMock.mock.calls as any[];
            expect(calls.length).toBeGreaterThan(0);
            const lastCall = calls[calls.length - 1];
            expect(lastCall[0]).not.toHaveProperty('browser');
        });

        it('should detect browser environment with window.document', () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            originalWindow = (globalThis as any).window;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).window = {
                document: {},
            };

            createLogger();

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const calls = pinoMock.mock.calls as any[];
            expect(calls.length).toBeGreaterThan(0);
            const lastCall = calls[calls.length - 1];
            expect(lastCall[0]).toHaveProperty('browser');
        });

        it('should not detect browser environment without document', () => {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            originalWindow = (globalThis as any).window;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (globalThis as any).window = {};

            createLogger();

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const calls = pinoMock.mock.calls as any[];
            expect(calls.length).toBeGreaterThan(0);
            const lastCall = calls[calls.length - 1];
            expect(lastCall[0]).not.toHaveProperty('browser');
        });
    });

    describe('base sanitization', () => {
        it('should handle undefined base', () => {
            createLogger({ base: undefined });

            expect(pinoMock).toHaveBeenCalledWith(
                expect.objectContaining({
                    base: {},
                })
            );
        });

        it('should create plain object from base', () => {
            class CustomBase {
                prop = 'value';
            }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const base = new CustomBase() as any;

            createLogger({ base });

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const calls = pinoMock.mock.calls as any[];
            expect(calls.length).toBeGreaterThan(0);
            const lastCall = calls[calls.length - 1];
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const config = lastCall[0] as any;
            expect(config.base).toEqual({ prop: 'value' });
            expect(Object.getPrototypeOf(config.base)).toBe(Object.prototype);
        });
    });
});
