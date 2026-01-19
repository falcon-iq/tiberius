module.exports = {
  displayName: 'shared',
  preset: '../../jest.preset.js',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../coverage/libs/shared',
  moduleNameMapper: {
    '^@libs/shared/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: [
    '<rootDir>/src/**/tests/**/*.spec.ts',
    '<rootDir>/src/**/tests/**/*.spec.tsx',
  ],
};
