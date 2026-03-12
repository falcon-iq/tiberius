module.exports = {
  displayName: 'marketpilot-webapp',
  preset: '../../jest.preset.js',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../coverage/apps/marketpilot-webapp',
  testMatch: [
    '<rootDir>/src/**/tests/**/*.spec.ts',
    '<rootDir>/src/**/tests/**/*.spec.tsx',
  ],
  passWithNoTests: true,
};
