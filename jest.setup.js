// Global Jest setup for all tests
// This file suppresses console logs and pino logger output during tests

// Store original console methods
const originalConsole = {
  log: console.log,
  error: console.error,
  warn: console.warn,
  info: console.info,
  debug: console.debug,
};

// Mock console methods to suppress output during tests
global.console = {
  ...console,
  // Keep console.log for debugging when needed (but mock it)
  log: jest.fn(originalConsole.log),
  // Suppress these to reduce test noise
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn(),
};

// Mock pino logger to suppress JSON log output
jest.mock('pino', () => {
  const mockLogger = {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
    trace: jest.fn(),
    fatal: jest.fn(),
    child: jest.fn(() => mockLogger),
  };
  
  return jest.fn(() => mockLogger);
});
