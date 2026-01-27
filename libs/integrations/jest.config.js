module.exports = {
  displayName: 'integrations-github',
  preset: '../../jest.preset.js',
  testEnvironment: 'node',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../coverage/libs/integrations',
  moduleNameMapper: {
    '^@libs/integrations/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: [
    '<rootDir>/src/**/tests/**/*.spec.ts',
    '<rootDir>/src/**/tests/**/*.spec.tsx',
  ],
  silent: false,
  setupFilesAfterEnv: ['<rootDir>/../../jest.setup.js'],
};
