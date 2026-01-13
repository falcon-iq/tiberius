export default {
  displayName: 'shared-util',
  preset: '../../../jest.preset.js',
  testEnvironment: 'node',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
  coverageDirectory: '../../../coverage/libs/shared/util',
  moduleNameMapper: {
    '^@libs/shared/utils$': '<rootDir>/src/index.ts',
  },
};
