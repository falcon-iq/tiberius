export default {
  displayName: 'shared-hooks',
  preset: '../../../../jest.preset.js',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.[tj]sx?$': ['ts-jest', { tsconfig: '<rootDir>/../../tsconfig.json' }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../../../coverage/libs/shared/src/hooks',
  moduleNameMapper: {
    '^@libs/shared/hooks$': '<rootDir>/use-async-validation.ts',
    '^@libs/shared/utils/logger$': '<rootDir>/../utils/logger.ts',
    '^@libs/shared/utils$': '<rootDir>/../utils/logger.ts',
  },
};
