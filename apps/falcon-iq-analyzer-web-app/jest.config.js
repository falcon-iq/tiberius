module.exports = {
  displayName: 'falcon-iq-analyzer-web-app',
  preset: '../../jest.preset.js',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../coverage/apps/falcon-iq-analyzer-web-app',
  testMatch: [
    '<rootDir>/src/**/tests/**/*.spec.ts',
    '<rootDir>/src/**/tests/**/*.spec.tsx',
  ],
  passWithNoTests: true,
};
