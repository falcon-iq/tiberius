export default {
  displayName: 'shared-util',
  preset: '../../../../jest.preset.js',
  testEnvironment: 'node',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/../../tsconfig.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
  coverageDirectory: '../../../../coverage/libs/shared/src/util',
  moduleNameMapper: {
    '^@libs/shared/utils$': '<rootDir>/logger.ts',
  },
};
