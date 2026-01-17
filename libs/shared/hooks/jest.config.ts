export default {
  displayName: 'shared-hooks',
  preset: '../../../jest.preset.js',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../../coverage/libs/shared/hooks',
  moduleNameMapper: {
    '^@libs/shared/hooks$': '<rootDir>/src/index.ts',
    '^@libs/shared/utils/logger$': '<rootDir>/../utils/src/logger.ts',
    '^@libs/shared/utils$': '<rootDir>/../utils/src/index.ts',
  },
};
